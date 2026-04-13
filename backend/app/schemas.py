"""Pydantic schemas for requests, parsed intent, tool calls, and responses."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base model that rejects unknown fields for predictable API shapes."""

    model_config = ConfigDict(extra="forbid")


class AgentRequest(StrictModel):
    """Incoming request from the demo UI or API client."""

    user_request: str = Field(..., min_length=1, description="The user's natural language request.")
    restaurant_name: Optional[str] = Field(None, description="Optional restaurant name supplied by the user.")
    restaurant_phone: Optional[str] = Field(None, description="Optional restaurant phone supplied by the user.")


class ParsedIntent(StrictModel):
    """Structured interpretation of the user's request."""

    intent: Literal["check_table_availability", "check_open_status", "unsupported"]
    party_size: Optional[int] = Field(None, ge=1, le=20)
    requested_date: Optional[str] = Field(None, description="Requested date as stated or normalized by the parser.")
    requested_time: Optional[str] = Field(None, description="Requested time as stated or normalized by the parser.")
    natural_language_time: Optional[str] = Field(None, description="Original time expression when useful.")
    clarification_needed: bool = False
    clarification_message: Optional[str] = None


class ToolInvocation(StrictModel):
    """Trace of the tool the agent selected."""

    tool_name: str
    tool_args: dict[str, Any]


class ToolResult(StrictModel):
    """Result returned by the mocked restaurant-call tool."""

    success: bool
    raw_result: str
    structured_result: dict[str, Any]


class AgentResponse(StrictModel):
    """Full response including trace fields for the demo."""

    restaurant_name: Optional[str]
    restaurant_phone: Optional[str]
    parsed_intent: ParsedIntent
    tool_invocation: Optional[ToolInvocation]
    tool_result: Optional[ToolResult]
    summary: str
