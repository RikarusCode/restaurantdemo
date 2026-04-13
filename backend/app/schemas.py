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


class ReservationCallRequest(StrictModel):
    """Start a Retell outbound call with the reservation details shown in the modal."""

    restaurant_name: str = Field(..., min_length=1)
    restaurant_phone: str = Field(..., min_length=1)
    location: Optional[str] = None
    party_size: int = Field(..., ge=1, le=99)
    requested_time: str = Field(..., min_length=1)
    date_heading: str = Field(..., min_length=1)
    requested_date_token: Optional[str] = None
    notes: Optional[str] = None


class ReservationCallResponse(StrictModel):
    """Outcome of a reservation phone attempt."""

    confirmed: bool
    call_state: str
    message: str
    call_id: Optional[str] = None
    call_status: Optional[str] = None


class PipelineStep(StrictModel):
    """One visible step in the streamed agent pipeline."""

    step: str
    title: str
    data: dict[str, Any]
