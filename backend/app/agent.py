"""LLM-backed parsing for turning user text into a structured intent."""

import json
import re
from typing import Any

from openai import OpenAI

from .config import settings
from .schemas import AgentRequest, ParsedIntent, ToolResult


def build_system_prompt() -> str:
    """Return the compact instruction prompt used for intent extraction."""

    return (
        "You classify restaurant requests for a small demo agent. "
        "Return only JSON matching the requested schema. Supported intents are "
        "check_table_availability, check_open_status, and unsupported. Extract "
        "party_size, requested_date, requested_time, and natural_language_time only "
        "when present or clearly implied. Do not invent restaurant names, phone "
        "numbers, policies, or availability. If table availability is requested "
        "without a date or time, set clarification_needed to true with a short "
        "clarification_message. Booking, menu, delivery, complaints, and general "
        "chat are unsupported."
    )


def _parse_without_llm(request: AgentRequest) -> ParsedIntent:
    """Fallback parser for local demos when no OpenAI API key is configured."""

    text = request.user_request.lower()
    party_match = re.search(r"(?:for|party of|table for)\s+(\d+)", text)
    party_size = int(party_match.group(1)) if party_match else None

    has_time = bool(
        re.search(r"\b(\d{1,2})(?::\d{2})?\s*(am|pm)\b", text)
        or any(word in text for word in ["tonight", "tomorrow", "noon", "midnight", "morning", "afternoon", "evening"])
    )

    unsupported_words = ["book", "reserve", "reservation", "menu", "delivery", "order", "complaint", "review"]
    if any(word in text for word in unsupported_words):
        return ParsedIntent(
            intent="unsupported",
            party_size=party_size,
            requested_date=None,
            requested_time=None,
            natural_language_time=None,
            clarification_needed=False,
            clarification_message=None,
        )

    if any(word in text for word in ["open", "closed", "hours"]):
        return ParsedIntent(
            intent="check_open_status",
            party_size=None,
            requested_date="tomorrow" if "tomorrow" in text else None,
            requested_time="12:00 PM" if "noon" in text else None,
            natural_language_time="tomorrow at noon" if "tomorrow" in text and "noon" in text else None,
            clarification_needed=False,
            clarification_message=None,
        )

    if any(word in text for word in ["table", "availability", "available", "seat", "room"]):
        time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", text)
        requested_time = None
        if time_match:
            minutes = time_match.group(2) or "00"
            requested_time = f"{time_match.group(1)}:{minutes} {time_match.group(3).upper()}"
        return ParsedIntent(
            intent="check_table_availability",
            party_size=party_size,
            requested_date="tomorrow" if "tomorrow" in text else "tonight" if "tonight" in text else None,
            requested_time=requested_time,
            natural_language_time="tonight" if "tonight" in text else "tomorrow" if "tomorrow" in text else None,
            clarification_needed=not has_time,
            clarification_message="Please specify the date and time you'd like me to check." if not has_time else None,
        )

    return ParsedIntent(
        intent="unsupported",
        party_size=None,
        requested_date=None,
        requested_time=None,
        natural_language_time=None,
        clarification_needed=False,
        clarification_message=None,
    )


def parse_user_request(request: AgentRequest) -> ParsedIntent:
    """Classify the request and extract slots using structured OpenAI output."""

    if not settings.openai_api_key:
        return _parse_without_llm(request)

    client = OpenAI(api_key=settings.openai_api_key)
    schema: dict[str, Any] = ParsedIntent.model_json_schema()

    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": request.user_request},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "parsed_intent",
                "schema": schema,
                "strict": True,
            }
        },
    )

    return ParsedIntent.model_validate(json.loads(response.output_text))


def build_summary(parsed_intent: ParsedIntent, tool_result: ToolResult | None) -> str:
    """Create a short deterministic final answer without another LLM call."""

    if parsed_intent.clarification_needed:
        return parsed_intent.clarification_message or "Please specify the date and time you'd like me to check."

    if parsed_intent.intent == "unsupported":
        return "This demo currently supports table availability and open-status checks only."

    if tool_result is None:
        return "I could not complete that check."

    if not tool_result.success:
        return tool_result.raw_result

    data = tool_result.structured_result
    if parsed_intent.intent == "check_table_availability":
        party = data.get("party_size") or parsed_intent.party_size or "your party"
        requested_time = data.get("requested_time") or parsed_intent.requested_time or "that time"
        if data.get("status") == "available":
            return f"They have a table for {party} at {requested_time}."
        if data.get("alternative_time"):
            return f"They do not have a table for {party} at {requested_time}, but {data['alternative_time']} is available."
        return f"They do not have a table for {party} at {requested_time}."

    if parsed_intent.intent == "check_open_status":
        if parsed_intent.requested_date or parsed_intent.requested_time or parsed_intent.natural_language_time:
            if data.get("is_open"):
                return f"The restaurant is open at that time and closes at {data.get('closes_at', 'its listed closing time')}."
            return f"The restaurant is closed at that time and opens {data.get('opens_next', 'at its next listed opening time')}."
        if data.get("is_open"):
            return f"The restaurant is currently open and closes at {data.get('closes_at', 'its listed closing time')}."
        return f"The restaurant is currently closed and opens {data.get('opens_next', 'at its next listed opening time')}."

    return tool_result.raw_result
