"""Implement tests for webservice functions. Tests files are not documented by choice."""

import json

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.exceptions import BaseAPIException
from app.webservice import app


class MockUploadFile:
    """Mocking an upload file."""

    def __init__(self, content, content_type, filename):
        """Init the mock."""
        self.content = content
        self.content_type = content_type
        self.filename = filename


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
