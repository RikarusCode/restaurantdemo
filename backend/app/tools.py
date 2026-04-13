"""Mocked tool invocation and execution for restaurant call behavior."""

from datetime import datetime, timedelta

from .mock_data import check_availability, check_open_status, lookup_restaurant, normalize_time
from .schemas import ParsedIntent, ToolInvocation, ToolResult


def _datetime_from_intent(parsed_intent: ParsedIntent) -> datetime | None:
    """Build a demo datetime for open-status checks when date/time are supplied."""

    normalized_time = normalize_time(parsed_intent.requested_time or parsed_intent.natural_language_time)
    if not normalized_time:
        return None

    base = datetime.now()
    if (parsed_intent.requested_date or "").lower() == "tomorrow" or "tomorrow" in (parsed_intent.natural_language_time or "").lower():
        base += timedelta(days=1)

    parsed_time = datetime.strptime(normalized_time, "%I:%M %p").time()
    return datetime.combine(base.date(), parsed_time)


def build_tool_invocation(
    parsed_intent: ParsedIntent,
    restaurant_name: str | None,
    restaurant_phone: str | None,
) -> ToolInvocation:
    """Build a traceable tool invocation from parsed intent and restaurant info."""

    return ToolInvocation(
        tool_name=parsed_intent.intent,
        tool_args={
            "restaurant_name": restaurant_name,
            "restaurant_phone": restaurant_phone,
            "party_size": parsed_intent.party_size,
            "requested_date": parsed_intent.requested_date,
            "requested_time": parsed_intent.requested_time,
        },
    )


def execute_tool(
    parsed_intent: ParsedIntent,
    restaurant_name: str | None,
    restaurant_phone: str | None,
) -> ToolResult:
    """Execute the mocked restaurant tool and return raw plus structured output."""

    restaurant = lookup_restaurant(restaurant_name, restaurant_phone)
    if restaurant is None:
        return ToolResult(
            success=False,
            raw_result="I could not find that restaurant in the demo data.",
            structured_result={"error": "restaurant_not_found"},
        )

    if parsed_intent.intent == "check_table_availability":
        result = check_availability(
            restaurant,
            parsed_intent.party_size,
            parsed_intent.requested_date,
            parsed_intent.requested_time,
        )
        if result["status"] == "available":
            raw = (
                f"{restaurant['name']} has availability for {result['party_size']} "
                f"at {result['requested_time']} {result['requested_date']}."
            )
        elif result["alternative_time"]:
            raw = (
                f"{restaurant['name']} is unavailable at {result['requested_time']}, "
                f"but {result['alternative_time']} is available."
            )
        else:
            raw = f"{restaurant['name']} has no availability {result['requested_date']}."

        return ToolResult(success=True, raw_result=raw, structured_result=result)

    if parsed_intent.intent == "check_open_status":
        result = check_open_status(restaurant, _datetime_from_intent(parsed_intent))
        if result["is_open"]:
            raw = f"{restaurant['name']} is open now and closes at {result['closes_at']}."
        else:
            raw = f"{restaurant['name']} is closed now and opens {result['opens_next']}."
        return ToolResult(success=True, raw_result=raw, structured_result=result)

    return ToolResult(
        success=False,
        raw_result="This demo currently supports table availability and open-status checks only.",
        structured_result={"error": "unsupported_intent"},
    )
