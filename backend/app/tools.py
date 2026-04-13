"""Tool definitions for OpenAI function calling and mock execution."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .mock_data import check_availability, check_open_status, lookup_restaurant, normalize_time
from .restaurant_search import search_restaurants


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "call_restaurant_check_availability",
        "description": (
            "Simulate calling the selected restaurant to ask whether a table is "
            "available for a party size, date, and time."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "party_size": {
                    "type": "integer",
                    "description": "Number of guests in the party.",
                },
                "date": {
                    "type": "string",
                    "description": "Date to check, such as 'tonight' or 'tomorrow'.",
                },
                "time": {
                    "type": "string",
                    "description": "Time to check, such as '7:00 PM' or 'noon'.",
                },
            },
            "required": ["party_size", "date", "time"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "call_restaurant_check_hours",
        "description": (
            "Simulate calling the selected restaurant to ask whether it is open "
            "now or at a specified date and time."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date to check, such as 'today' or 'tomorrow'.",
                },
                "time": {
                    "type": ["string", "null"],
                    "description": "Specific time to check, or null for current status.",
                },
            },
            "required": ["date", "time"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

SEARCH_TOOL_DEFINITION: dict[str, Any] = {
    "type": "function",
    "name": "search_restaurant",
    "description": "Search the demo restaurant directory by name.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Restaurant name or search phrase from the user request.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    "strict": True,
}

TOOL_DISPLAY_NAMES: dict[str, str] = {
    "call_restaurant_check_availability": "Calling Restaurant - Table Availability",
    "call_restaurant_check_hours": "Calling Restaurant - Hours Check",
    "search_restaurant": "Searching for Restaurant",
}


def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    restaurant_name: str | None,
    restaurant_phone: str | None,
) -> dict[str, Any]:
    """Dispatch to the correct mock handler and return a structured result."""

    if tool_name == "call_restaurant_check_availability":
        return _exec_availability(arguments, restaurant_name, restaurant_phone)
    if tool_name == "call_restaurant_check_hours":
        return _exec_hours(arguments, restaurant_name, restaurant_phone)
    if tool_name == "search_restaurant":
        return _exec_search(arguments)

    return {"success": False, "error": f"Unknown tool: {tool_name}"}


def _exec_availability(
    args: dict[str, Any],
    name: str | None,
    phone: str | None,
) -> dict[str, Any]:
    restaurant = lookup_restaurant(name, phone)
    if restaurant is None:
        return _restaurant_not_found()

    result = check_availability(
        restaurant,
        args.get("party_size"),
        args.get("date"),
        normalize_time(args.get("time")),
    )
    return {
        "success": True,
        "restaurant_name": restaurant["name"],
        "restaurant_phone": restaurant["phone"],
        "raw_result": availability_sentence(restaurant["name"], result),
        **result,
    }


def _exec_hours(
    args: dict[str, Any],
    name: str | None,
    phone: str | None,
) -> dict[str, Any]:
    restaurant = lookup_restaurant(name, phone)
    if restaurant is None:
        return _restaurant_not_found()

    at_dt = _build_datetime(args.get("date"), args.get("time"))
    result = check_open_status(restaurant, at_dt)
    return {
        "success": True,
        "restaurant_name": restaurant["name"],
        "restaurant_phone": restaurant["phone"],
        "raw_result": hours_sentence(restaurant["name"], result, bool(args.get("time"))),
        **result,
    }


def _exec_search(args: dict[str, Any]) -> dict[str, Any]:
    result = search_restaurants(args.get("query", ""))
    if not result["success"]:
        return result

    restaurant = result["restaurant"]
    matched = lookup_restaurant(restaurant["name"], restaurant["phone"])
    day = datetime.now().strftime("%A")
    opens, closes = matched["hours"][day] if matched else ("unknown", "unknown")
    return {
        "success": True,
        "name": restaurant["name"],
        "phone": restaurant["phone"],
        "cuisine": restaurant["cuisine"],
        "address": restaurant["address"],
        "hours_today": f"{opens} to {closes}",
        "resolution": {
            "source": result["source"],
            "confidence": result["confidence"],
        },
    }


def _build_datetime(date_str: str | None, time_str: str | None) -> datetime | None:
    normalized = normalize_time(time_str) if time_str else None
    base = datetime.now()

    if date_str and "tomorrow" in date_str.lower():
        base += timedelta(days=1)

    if normalized:
        parsed_time = datetime.strptime(normalized, "%I:%M %p").time()
        return datetime.combine(base.date(), parsed_time)

    return None if not date_str else base


def _restaurant_not_found() -> dict[str, Any]:
    return {
        "success": False,
        "error": "Restaurant not found in the demo directory.",
        "hint": "Select a restaurant or use Search mode with a restaurant name in the request.",
    }


def availability_sentence(restaurant_name: str, result: dict[str, Any]) -> str:
    """Human-readable result from the mocked availability call."""

    party_size = result.get("party_size") or "your party"
    requested_time = result.get("requested_time") or "that time"
    requested_date = result.get("requested_date") or "that date"

    if result.get("status") == "available":
        note = f" ({result['requested_slot_note']})" if result.get("requested_slot_note") else ""
        return f"{restaurant_name} has a table for {party_size} at {requested_time} {requested_date}{note}."
    if result.get("alternative_time"):
        return (
            f"{restaurant_name} does not have a table at {requested_time}, "
            f"but {result['alternative_time']} is available."
        )
    return f"{restaurant_name} has no availability {requested_date}."


def hours_sentence(restaurant_name: str, result: dict[str, Any], checked_specific_time: bool) -> str:
    """Human-readable result from the mocked hours call."""

    if result.get("is_open"):
        prefix = "is open at that time" if checked_specific_time else "is open now"
        return f"{restaurant_name} {prefix} and closes at {result.get('closes_at')}."

    prefix = "is closed at that time" if checked_specific_time else "is closed now"
    return f"{restaurant_name} {prefix} and opens {result.get('opens_next')}."
