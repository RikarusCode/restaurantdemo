"""Pydantic models for the public API and streamed trace."""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Reject unknown fields so API traces stay predictable."""

    model_config = ConfigDict(extra="forbid")


class AgentRequest(StrictModel):
    """Incoming request from the browser or an API client."""

    user_request: str = Field(..., min_length=1)
    restaurant_name: Optional[str] = None
    restaurant_phone: Optional[str] = None


class PipelineStep(StrictModel):
    """One visible step in the streamed agent pipeline."""

    step: str
    title: str
    data: dict[str, Any]
