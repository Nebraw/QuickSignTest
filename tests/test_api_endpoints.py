"""Tests for API endpoints. Tests files are not documented by choice."""

import io
import json
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import BaseModel

from app.exceptions import BaseAPIException
from app.webservice import app


class _PredictInput(BaseModel):
    """Mocking an input."""

    action: str


class _PredictOutput(BaseModel):
    """Mocking an output."""

    status: str


async def _predict(item: _PredictInput) -> _PredictOutput:
    """Mocking a prediction."""
    if item.action == "SuccessfulResponse":
        return _PredictOutput(status="Success")
    elif item.action == "BaseAPIException":
        raise BaseAPIException("This is a BaseAPIException raised for testing.")
    else:
        raise Exception("This is an unknown exception raised for testing.")


@pytest.fixture(name="client")
def app_client_fixture():
    """Use the real FastAPI app for testing."""
    client = TestClient(app)
    return client


def test_base_routes_of_create_app(client):
    """Test the health and root endpoints."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    response = client.get("/")
    assert response.status_code == 200


def test_base_exceptions_str_representation():
    """Test the string representation of BaseAPIException."""
    exc = BaseAPIException("Test error")
    assert (
        str(exc)
        == "[status_code=500][title=internal server error][details=Test error]"
    )


def test_base_api_exception_response():
    """Test the response() method of BaseAPIException."""
    exc = BaseAPIException("Test error response")
    response = exc.response()

    assert response.status_code == 500
    assert json.loads(response.body.decode()) == {
        "details": "Test error response",
        "status_code": 500,
        "title": "internal server error",
    }


def test_metrics_endpoint(client):
    """Test the metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    # Check that the response contains prometheus metrics
    assert b"prediction_score_average" in response.content
    assert b"predictions_total" in response.content


@mock.patch("app.services.prediction.perform_prediction")
@mock.patch("app.metrics.update_metrics")
@mock.patch("app.webservice.Image.open")
def test_predict_endpoint_mock(
    mock_image_open,
    mock_update_metrics,
    mock_perform_prediction,
    client
):
    """Test the predict endpoint with mocked prediction."""
    # Mock the prediction function
    mock_perform_prediction.return_value = ("test text", 0.95)
    
    # Mock PIL Image.open
    mock_img = Image.new("RGB", (100, 30), color="white")
    mock_image_open.return_value = mock_img
    
    # Create a dummy image file
    img_bytes = io.BytesIO()
    img = Image.new("RGB", (100, 30), color="white")
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    
    # Send request
    response = client.post(
        "/predict",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_text"] == "test text"
    assert data["score"] == 0.95
    
    # Verify metrics were updated
    mock_update_metrics.assert_called_once_with(0.95)


@mock.patch("app.webservice.httpx.AsyncClient")
@mock.patch("app.services.prediction.perform_prediction")
@mock.patch("app.services.storage.upload_image_to_minio")
@mock.patch("app.services.database.save_metadata_to_mongo")
@mock.patch("app.metrics.update_metrics")
def test_ingest_endpoint_success(
    mock_update_metrics,
    mock_save_metadata,
    mock_upload_image,
    mock_perform_prediction,
    mock_async_client,
    client
):
    """Test the ingest endpoint with successful ingestion."""
    # Mock image download
    img = Image.new("RGB", (100, 30), color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_data = img_bytes.getvalue()
    
    mock_response = mock.MagicMock()
    mock_response.content = img_data
    mock_response.raise_for_status = mock.MagicMock()
    
    mock_client_instance = mock.MagicMock()
    mock_client_instance.__aenter__ = mock.AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = mock.AsyncMock()
    mock_client_instance.get = mock.AsyncMock(return_value=mock_response)
    mock_async_client.return_value = mock_client_instance
    
    # Mock prediction
    mock_perform_prediction.return_value = ("predicted text", 0.85)
    
    # Mock MinIO upload
    mock_upload_image.return_value = "images/test_image.jpg"
    
    # Send request
    response = client.post(
        "/ingest",
        json={
            "image_url": "https://example.com/test.jpg",
            "annotation": "ground truth text"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["predicted_text"] == "predicted text"
    assert data["score"] == 0.85
    assert "image_id" in data
    
    # Verify all functions were called
    mock_perform_prediction.assert_called_once()
    mock_upload_image.assert_called_once()
    mock_save_metadata.assert_called_once()
    mock_update_metrics.assert_called_once_with(0.85)


@mock.patch("app.webservice.httpx.AsyncClient")
def test_ingest_endpoint_invalid_url(mock_async_client, client):
    """Test the ingest endpoint with invalid URL."""
    # Mock failed download
    mock_client_instance = mock.MagicMock()
    mock_client_instance.__aenter__ = mock.AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = mock.AsyncMock()
    mock_client_instance.get = mock.AsyncMock(side_effect=Exception("Connection error"))
    mock_async_client.return_value = mock_client_instance
    
    response = client.post(
        "/ingest",
        json={
            "image_url": "https://invalid-url.com/nonexistent.jpg"
        }
    )
    
    assert response.status_code == 500
    assert "Internal error" in response.json()["detail"]


@mock.patch("app.services.database.save_metadata_to_mongo")
@mock.patch("app.metrics.update_metrics")
@mock.patch("app.services.storage.upload_image_to_minio")
@mock.patch("app.services.prediction.perform_prediction")
@mock.patch("app.webservice.Image.open")
@mock.patch("app.webservice.httpx.AsyncClient")
def test_ingest_endpoint_generic_exception(
    mock_client_class,
    mock_image_open,
    mock_predict,
    mock_upload,
    mock_update,
    mock_save,
    client
):
    """Test ingest endpoint with generic exception during processing."""
    # Mock httpx to return successful response
    mock_response = mock.MagicMock()
    mock_response.content = b"fake image"
    mock_response.raise_for_status = mock.MagicMock()
    mock_client = mock.MagicMock()
    mock_client.__aenter__ = mock.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mock.AsyncMock()
    mock_client.get = mock.AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client
    
    # Mock Image.open to succeed
    mock_image_open.return_value = mock.MagicMock()
    
    # Mock perform_prediction to raise a generic exception
    mock_predict.side_effect = RuntimeError("Unexpected error during prediction")
    
    response = client.post(
        "/ingest",
        json={"image_url": "http://example.com/image.jpg"}
    )
    
    # Should return 500 status code
    assert response.status_code == 500
    assert "Internal error during ingestion" in response.json()["detail"]
