"""Restaurant agent orchestration using OpenAI tool calling with a fast fallback."""

from __future__ import annotations

import json
import re
from typing import Any, Generator

from openai import OpenAI

from .config import settings
from .mock_data import normalize_time
from .tools import SEARCH_TOOL_DEFINITION, TOOL_DEFINITIONS, TOOL_DISPLAY_NAMES, execute_tool

Step = dict[str, Any]

SUPPORTED_MESSAGE = "This demo supports table availability and open-status checks only."
CLARIFICATION_MESSAGE = "Please specify the date and time you would like me to check."
MAX_TOOL_ROUNDS = 4

SYSTEM_PROMPT = """\
You are a concise restaurant phone assistant for a demo.

Restaurant already on file:
Name: {restaurant_name}
Phone: {restaurant_phone}

Supported tasks:
- Ask whether a table is available for a party size, date, and time.
- Ask whether the restaurant is open now or at a specified time.

Use exactly one of the provided restaurant-call tools for supported requests.
Do not call a table-availability tool unless party size, date, and time are present.
If details are missing, ask for clarification without calling a tool.
If the user asks to book, reserve, order, see a menu, complain, or do anything else,
say that this demo supports table availability and open-status checks only.
Do not invent restaurant details or call results. Relay only tool output.
Keep the final answer to one polished sentence.
"""

SYSTEM_PROMPT_SEARCH = """\
You are a concise restaurant phone assistant for a demo.

No restaurant is on file. For supported requests, first use search_restaurant
to find restaurant details from the user's text, then call the relevant
restaurant tool.

Supported tasks:
- Ask whether a table is available for a party size, date, and time.
- Ask whether the restaurant is open now or at a specified time.

If no restaurant name is present, ask the user to specify a restaurant.
Do not call a table-availability tool unless party size, date, and time are present.
If details are missing, ask for clarification without calling a tool.
If the user asks to book, reserve, order, see a menu, complain, or do anything else,
say that this demo supports table availability and open-status checks only.
Do not invent restaurant details or call results. Relay only tool output.
Keep the final answer to one polished sentence.
"""


def run_agent(
    user_request: str,
    restaurant_name: str | None,
    restaurant_phone: str | None,
) -> Generator[Step, None, None]:
    """Yield visible pipeline steps for the agent request."""

    if restaurant_name and restaurant_phone:
        yield _step(
            "restaurant_info",
            "Restaurant on File",
            {"name": restaurant_name, "phone": restaurant_phone, "source": "selected_by_system"},
        )

    if settings.openai_api_key:
        try:
            yield from _run_with_llm(user_request, restaurant_name, restaurant_phone)
            return
        except Exception as exc:
            yield _step(
                "notice",
                "LLM Unavailable",
                {
                    "message": "OpenAI parsing failed, so the demo is using the deterministic fallback.",
                    "error": exc.__class__.__name__,
                },
            )

    yield from _run_without_llm(user_request, restaurant_name, restaurant_phone)


def _run_with_llm(
    user_request: str,
    restaurant_name: str | None,
    restaurant_phone: str | None,
) -> Generator[Step, None, None]:
    client = OpenAI(api_key=settings.openai_api_key)
    has_restaurant = bool(restaurant_name and restaurant_phone)
    system_prompt = (
        SYSTEM_PROMPT.format(restaurant_name=restaurant_name, restaurant_phone=restaurant_phone)
        if has_restaurant
        else SYSTEM_PROMPT_SEARCH
    )
    tools = list(TOOL_DEFINITIONS) if has_restaurant else [SEARCH_TOOL_DEFINITION, *TOOL_DEFINITIONS]
    conversation: list[Any] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_request},
    ]

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.responses.create(
            model=settings.openai_model,
            input=conversation,
            tools=tools,
        )
        tool_calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]

        if not tool_calls:
            yield _step("summary", "Final Answer", {"text": _clean_summary(response.output_text)})
            return

        conversation.extend(_serialize_output_items(response.output))

        for tool_call in tool_calls:
            args = json.loads(tool_call.arguments or "{}")

            if tool_call.name != "search_restaurant":
                yield _step("understanding", "Request Understood", _understanding_from_tool(tool_call.name, args))

            yield _step(
                "tool_call",
                TOOL_DISPLAY_NAMES.get(tool_call.name, tool_call.name),
                {"tool_name": tool_call.name, "arguments": args},
            )

            result = execute_tool(tool_call.name, args, restaurant_name, restaurant_phone)

            if tool_call.name == "search_restaurant" and result.get("success"):
                restaurant_name = result["name"]
                restaurant_phone = result["phone"]
                yield _step(
                    "restaurant_info",
                    "Restaurant Found",
                    {
                        "name": restaurant_name,
                        "phone": restaurant_phone,
                        "cuisine": result.get("cuisine"),
                        "address": result.get("address"),
                        "source": "search_restaurant",
                        "resolution": result.get("resolution"),
                    },
                )

            yield _step("tool_result", "Restaurant Response", result)
            conversation.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": json.dumps(result),
                }
            )

    yield _step(
        "summary",
        "Final Answer",
        {"text": "I could not complete the tool call in time. Try the request again."},
    )


def _run_without_llm(
    user_request: str,
    restaurant_name: str | None,
    restaurant_phone: str | None,
) -> Generator[Step, None, None]:
    text = user_request.lower()

    if _is_unsupported(text):
        yield _step("understanding", "Request Understood", {"intent": "unsupported", "reason": "outside_demo_scope"})
        yield _step("summary", "Final Answer", {"text": SUPPORTED_MESSAGE})
        return

    if not restaurant_name or not restaurant_phone:
        yield _step(
            "tool_call",
            TOOL_DISPLAY_NAMES["search_restaurant"],
            {"tool_name": "search_restaurant", "arguments": {"query": user_request}},
        )
        search_result = execute_tool("search_restaurant", {"query": user_request}, None, None)
        yield _step("tool_result", "Search Result", search_result)
        if search_result.get("success"):
            restaurant_name = search_result["name"]
            restaurant_phone = search_result["phone"]
            yield _step(
                "restaurant_info",
                "Restaurant Found",
                {
                    "name": restaurant_name,
                    "phone": restaurant_phone,
                    "cuisine": search_result.get("cuisine"),
                    "address": search_result.get("address"),
                    "source": "search_restaurant",
                    "resolution": search_result.get("resolution"),
                },
            )
        else:
            yield _step("summary", "Final Answer", {"text": "Please specify which restaurant you want me to call."})
            return

    if _is_availability_request(text):
        yield from _fallback_availability(text, restaurant_name, restaurant_phone)
        return

    if _is_hours_request(text):
        yield from _fallback_hours(text, restaurant_name, restaurant_phone)
        return

    yield _step("understanding", "Request Understood", {"intent": "unsupported", "reason": "unclear_request"})
    yield _step("summary", "Final Answer", {"text": SUPPORTED_MESSAGE})


def _fallback_availability(
    text: str,
    name: str | None,
    phone: str | None,
) -> Generator[Step, None, None]:
    party_size = _extract_party_size(text)
    requested_date = _extract_date(text)
    requested_time = _extract_time(text)

    understanding = {
        "intent": "check_table_availability",
        "party_size": party_size,
        "date": requested_date,
        "time": requested_time,
    }
    yield _step("understanding", "Request Understood", understanding)

    if not party_size or not requested_date or not requested_time:
        yield _step("summary", "Final Answer", {"text": CLARIFICATION_MESSAGE})
        return

    args = {"party_size": party_size, "date": requested_date, "time": requested_time}
    yield _step(
        "tool_call",
        TOOL_DISPLAY_NAMES["call_restaurant_check_availability"],
        {"tool_name": "call_restaurant_check_availability", "arguments": args},
    )
    result = execute_tool("call_restaurant_check_availability", args, name, phone)
    yield _step("tool_result", "Restaurant Response", result)
    yield _step("summary", "Final Answer", {"text": _summary_from_tool_result("availability", result)})


def _fallback_hours(
    text: str,
    name: str | None,
    phone: str | None,
) -> Generator[Step, None, None]:
    requested_date = _extract_date(text) or "today"
    requested_time = _extract_time(text)
    args = {"date": requested_date, "time": requested_time}

    yield _step(
        "understanding",
        "Request Understood",
        {"intent": "check_open_status", "date": requested_date, "time": requested_time or "now"},
    )
    yield _step(
        "tool_call",
        TOOL_DISPLAY_NAMES["call_restaurant_check_hours"],
        {"tool_name": "call_restaurant_check_hours", "arguments": args},
    )
    result = execute_tool("call_restaurant_check_hours", args, name, phone)
    yield _step("tool_result", "Restaurant Response", result)
    yield _step("summary", "Final Answer", {"text": _summary_from_tool_result("hours", result)})


def _summary_from_tool_result(kind: str, result: dict[str, Any]) -> str:
    if not result.get("success"):
        return result.get("error") or "I could not complete that check."

    if kind == "availability":
        party_size = result.get("party_size") or "your party"
        requested_time = result.get("requested_time") or "that time"
        if result.get("status") == "available":
            return f"They have a table for {party_size} at {requested_time}."
        if result.get("alternative_time"):
            return f"They do not have a table for {party_size} at {requested_time}, but {result['alternative_time']} is available."
        return f"They do not have a table for {party_size} at {requested_time}."

    if result.get("is_open"):
        return f"The restaurant is open and closes at {result.get('closes_at')}."
    return f"The restaurant is closed and opens {result.get('opens_next')}."


def _understanding_from_tool(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "call_restaurant_check_availability":
        return {
            "intent": "check_table_availability",
            "party_size": args.get("party_size"),
            "date": args.get("date"),
            "time": args.get("time"),
        }
    if tool_name == "call_restaurant_check_hours":
        return {
            "intent": "check_open_status",
            "date": args.get("date"),
            "time": args.get("time") or "now",
        }
    return {"intent": "unknown"}


def _extract_party_size(text: str) -> int | None:
    match = re.search(r"(?:for|party of|table for|room for)\s+(\d+)", text)
    return int(match.group(1)) if match else None


def _extract_date(text: str) -> str | None:
    if "tonight" in text:
        return "tonight"
    if "tomorrow" in text:
        return "tomorrow"
    if "today" in text or "right now" in text or "currently" in text or "now" in text:
        return "today"
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        if day in text:
            return day
    return None


def _extract_time(text: str) -> str | None:
    if "noon" in text:
        return "12:00 PM"
    if "midnight" in text:
        return "12:00 AM"

    match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)\b", text)
    if not match:
        return None

    minutes = match.group(2) or "00"
    meridiem = "AM" if match.group(3).startswith("a") else "PM"
    return normalize_time(f"{match.group(1)}:{minutes} {meridiem}")


def _is_unsupported(text: str) -> bool:
    unsupported_words = ["book", "reserve", "reservation", "menu", "delivery", "order", "complaint", "review"]
    return any(word in text for word in unsupported_words)


def _is_availability_request(text: str) -> bool:
    return any(word in text for word in ["table", "availability", "available", "seat", "room"])


def _is_hours_request(text: str) -> bool:
    return any(word in text for word in ["open", "closed", "hours", "close"])


def _clean_summary(text: str | None) -> str:
    cleaned = (text or "").strip()
    if cleaned:
        return cleaned
    return "I could not complete that request. Try asking about table availability or opening hours."


def _serialize_output_items(items: list[Any]) -> list[Any]:
    serialized = []
    for item in items:
        if hasattr(item, "model_dump"):
            serialized.append(item.model_dump(exclude_none=True))
        else:
            serialized.append(item)
    return serialized


def _step(step_type: str, title: str, data: dict[str, Any]) -> Step:
    return {"step": step_type, "title": title, "data": data}
