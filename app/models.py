"""Pydantic models for API schemas."""

import typing as tp

from pydantic import BaseModel, HttpUrl


class PredictOutput(BaseModel):
    """Model output."""

    predicted_text: str
    score: float


class IngestRequest(BaseModel):
    """Request model for data ingestion."""

    image_url: HttpUrl
    annotation: tp.Optional[str] = None


class IngestResponse(BaseModel):
    """Response model for data ingestion."""

    status: str
    image_id: str
    predicted_text: str
    score: float


class HealthCheckResponse(BaseModel):  # pylint: disable=too-few-public-methods
    """Schema for health-check response."""

    status: str = "ok"