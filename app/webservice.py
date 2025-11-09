"""Base API."""

import shutil
import tempfile
import typing as tp
from pathlib import Path

import torch
from fastapi import FastAPI, File, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from PIL import Image
from pydantic import BaseModel
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from app.exceptions import (
    BaseAPIException,
)


class PredictOutput(BaseModel):
    """Model output."""

    predicted_text: str
    score: float
    
class HealthCheckResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Schema for health-check response."""

    status: str = "ok"

PROCESSOR = TrOCRProcessor.from_pretrained("microsoft/trocr-base-printed")
MODEL = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-printed")
# Configure beam search for confidence scoring
MODEL.config.num_beams = 4
MODEL.config.early_stopping = True
MODEL.config.length_penalty = 2.0
MODEL.config.no_repeat_ngram_size = 3

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
    """Predict endpoint."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        shutil.copyfileobj(file.file, tmp)
        image_path = Path(tmp.name)
        img = Image.open(image_path).convert("RGB")  # Replace with your image path

        pixel_values = PROCESSOR(images=img, return_tensors="pt").pixel_values

        # Generate with scores
        outputs = MODEL.generate(
            pixel_values,
            output_scores=True,
            return_dict_in_generate=True
        )

        # Decode prediction
        predicted_text = PROCESSOR.batch_decode(outputs.sequences, skip_special_tokens=True)[0]

        # Get confidence score (log-probability → probability)
        log_score = outputs.sequences_scores[0].item()
        confidence = torch.exp(torch.tensor(log_score)).item()
        print(predicted_text)
        print(confidence)
        return PredictOutput(predicted_text=predicted_text, score=confidence)