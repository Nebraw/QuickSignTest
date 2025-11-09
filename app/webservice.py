"""Base API."""

import io
import shutil
import tempfile
import typing as tp
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import RedirectResponse
from PIL import Image
from prometheus_client import generate_latest
from starlette.responses import Response

from app.config import MINIO_BUCKET
from app.exceptions import BaseAPIException
from app.metrics import update_metrics
from app.models import (
    HealthCheckResponse,
    IngestRequest,
    IngestResponse,
    PredictOutput,
)
from app.services.database import save_metadata_to_mongo
from app.services.prediction import perform_prediction
from app.services.storage import upload_image_to_minio


async def root(req: Request) -> RedirectResponse:
    """Simple redirection to '/docs' taking root_path into account.

    Args:
        req: a request made to the root path.

    Returns:
        a redirection to the docs route.
    """
    root_path = req.scope.get("root_path", "").rstrip("/")
    return RedirectResponse(root_path + "/docs")


async def health():
    """Simple health-check response."""
    return HealthCheckResponse()


def add_base_routes(
    source_app: FastAPI,
) -> None:
    """Add basic routes to a FastAPI app.

    added routes are:
      - '/health' => return {'status': 'ok'}
      - '/' => redirect to '/docs'

    Args:
        source_app: instance of a FastAPI application
    """
    # make sure we have a FastAPI app :)
    assert isinstance(source_app, FastAPI)

    # add basic health check route
    source_app.add_api_route(
        "/health",
        health,
        status_code=status.HTTP_200_OK,
        include_in_schema=True,
        response_model=HealthCheckResponse,
    )

    # add redirect route to /docs
    # not included in openAPI schema
    source_app.add_api_route(
        "/",
        root,
        include_in_schema=False,
    )


def create_app(
    debug: bool = False,
    title: str = "FastAPI",
    description: str = "FastAPI app",
    **kwargs: tp.Any,
) -> FastAPI:
    """Create a FastAPI application with basic routes.

    Args:
        debug: Run the app in debug mode. Defaults to False.
        title: Defaults to "FastAPI".
        description: Defaults to "FastAPI app".
        kwargs: other keyword arguments to pass to FastAPI app.

    Returns:
        The FastAPI app ready to be used or extended.
    """
    # FastAPI instance
    new_app = FastAPI(
        debug=debug,
        title=title,
        version="0.1.0",
        description=description,
        **kwargs,
    )
    add_base_routes(new_app)
    return new_app


app = create_app(
    title="webservice",
    description="Service to run application.",
)


EXTRA_RESPONSES = {
    **BaseAPIException.response_model(),
}

@app.post("/predict", response_model=PredictOutput)
async def predict(file: UploadFile = File(...)) -> tp.Any:
    """Predict endpoint for uploaded files.
    
    Args:
        file: Image file to process
        
    Returns:
        Prediction output with text and confidence score
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp.flush()  # Ensure data is written to disk
        image_path = Path(tmp.name)
    
    try:
        # Open image after closing the temporary file
        img = Image.open(image_path).convert("RGB")
        predicted_text, confidence = perform_prediction(img)
        
        # Update metrics
        update_metrics(confidence)
        
        return PredictOutput(predicted_text=predicted_text, score=confidence)
    finally:
        # Clean up temporary file
        if image_path.exists():
            image_path.unlink()


@app.post("/ingest", response_model=IngestResponse)
async def ingest_data(
    request: IngestRequest,
    background_tasks: BackgroundTasks
) -> IngestResponse:
    """Ingest image from URL, predict, and store in MinIO and MongoDB.
    
    Args:
        request: Ingest request containing image URL and optional annotation
        background_tasks: FastAPI background tasks for async operations
        
    Returns:
        Ingest response with status and prediction results
    """
    try:
        # Download image from URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(str(request.image_url))
            response.raise_for_status()
            image_data = response.content
        
        # Load image
        img = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        # Perform prediction
        predicted_text, confidence = perform_prediction(img)
        
        # Update metrics
        update_metrics(confidence)
        
        # Generate unique image ID
        image_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Schedule background tasks for storage operations
        # Upload to MinIO in background
        background_tasks.add_task(
            upload_image_to_minio,
            image_data,
            image_id
        )
        
        # Save metadata to MongoDB in background
        minio_path = f"{MINIO_BUCKET}/{image_id}.jpg"
        background_tasks.add_task(
            save_metadata_to_mongo,
            image_id=image_id,
            image_url=str(request.image_url),
            minio_path=minio_path,
            predicted_text=predicted_text,
            score=confidence,
            annotation=request.annotation
        )
        
        return IngestResponse(
            status="success",
            image_id=image_id,
            predicted_text=predicted_text,
            score=confidence
        )
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download image from URL: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error during ingestion: {str(e)}"
        ) from e


@app.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics.
    
    Returns:
        Prometheus metrics in text format
    """
    return Response(content=generate_latest(), media_type="text/plain")