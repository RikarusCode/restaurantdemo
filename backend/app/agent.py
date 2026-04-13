"""Restaurant agent orchestration using an LLM planner plus deterministic tools."""

from __future__ import annotations

import json
import re
from typing import Any, Generator

from openai import OpenAI

from .config import settings
from .mock_data import normalize_time
from .reservation_ui import implies_availability_check, merge_summary_with_reservation_ui
from .tools import SEARCH_TOOL_DEFINITION, TOOL_DEFINITIONS, TOOL_DISPLAY_NAMES, execute_tool

Step = dict[str, Any]

SUPPORTED_MESSAGE = "This product currently supports table availability and open-status checks only."
CLARIFICATION_MESSAGE = (
    "Add a time to the request, for example: "
    "'Can you check whether this restaurant has room for 4 tonight at 7 PM?'"
)
LLM_TIMEOUT_SECONDS = 20.0

SYSTEM_PROMPT = """\
You are a concise restaurant-calling agent.

Restaurant on file:
Name: {restaurant_name}
Phone: {restaurant_phone}

Your job is to choose the correct tool for the user's request. Supported tasks:
- Check table availability for a party size, date, and time (including phrases like
  "make a reservation" or "book a table" that imply an availability check).
- Check whether the restaurant is open now or at a specified time.

For availability, assume 2 guests when party size is missing, assume tonight
when date is missing, and interpret bare dinner-hour times like "at 6" as
6:00 PM. If the time is missing, ask for clarification without calling a tool.
If the request is outside the supported tasks, explain the supported scope.
Do not invent restaurant facts or call results.
Do not ask the user to confirm reasonable assumptions. This is a single-turn
tool product, not a chat assistant. If the request is supported and has enough
information, call the tool.
"""

SYSTEM_PROMPT_SEARCH = """\
You are a concise restaurant-calling agent.

No restaurant is selected yet. For supported requests, first use
search_restaurant to resolve the restaurant from the user's words. The search
query can be a proper name, cuisine, neighborhood, or natural description such
as "the sushi place", "the Italian place", "the waterfront place", or
"the taco place".

After the restaurant is resolved, the backend will continue the agent loop
against that restaurant. If no restaurant clue exists, ask the user to specify
which restaurant to call.
Reservation language (book a table, make a reservation) should still use the
availability tool once a restaurant is known.
Do not ask the user to confirm an inferred restaurant. Use search_restaurant
when a supported request includes a plausible restaurant clue.
"""


def run_agent(
    user_request: str,
    restaurant_name: str | None,
    restaurant_phone: str | None,
) -> Generator[Step, None, None]:
    """Yield visible pipeline steps for a restaurant-agent request."""

    text = user_request.lower()

    if restaurant_name and restaurant_phone:
        yield _step(
            "restaurant_info",
            "Restaurant on File",
            {"name": restaurant_name, "phone": restaurant_phone, "source": "selected_by_system"},
        )

    if implies_availability_check(text) and not _extract_time(text):
        yield _step(
            "understanding",
            "Request Needs Time",
            {
                "intent": "check_table_availability",
                "party_size": _extract_party_size(text) or 2,
                "date": _extract_date(text) or "tonight",
                "time": None,
                "missing": "time",
            },
        )
        yield _step("summary", "Final Answer", {"text": CLARIFICATION_MESSAGE})
        return

    if settings.llm_api_key:
        try:
            yield from _run_with_llm(user_request, restaurant_name, restaurant_phone)
            return
        except Exception as exc:
            yield _step(
                "notice",
                "Local Parser Took Over",
                {
                    "message": "The configured LLM provider was unavailable, so the deterministic parser handled the request.",
                    "error": exc.__class__.__name__,
                },
            )

    yield from _run_without_llm(user_request, restaurant_name, restaurant_phone, include_parser_step=True)


def _run_with_llm(
    user_request: str,
    restaurant_name: str | None,
    restaurant_phone: str | None,
) -> Generator[Step, None, None]:
    has_restaurant = bool(restaurant_name and restaurant_phone)
    tools = list(TOOL_DEFINITIONS) if has_restaurant else [SEARCH_TOOL_DEFINITION]
    prompt = (
        SYSTEM_PROMPT.format(restaurant_name=restaurant_name, restaurant_phone=restaurant_phone)
        if has_restaurant
        else SYSTEM_PROMPT_SEARCH
    )

    yield _step(
        "llm_planning",
        "LLM Planning",
        {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "restaurant_context": "selected" if has_restaurant else "needs_search",
            "available_tools": [tool["name"] for tool in tools],
        },
    )

    client = OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=0,
    )
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": user_request}],
        tools=_as_chat_tools(tools),
        tool_choice="auto",
    )
    message = response.choices[0].message
    tool_calls = message.tool_calls or []

    if not tool_calls:
        if _should_force_tool_path(user_request):
            yield _step(
                "notice",
                "Decisive Tool Guardrail",
                {
                    "message": "The LLM returned conversational text without a tool call, so the backend continued with the tool path for this supported single-turn request.",
                    "llm_text": _clean_summary(message.content),
                },
            )
            yield from _run_without_llm(user_request, restaurant_name, restaurant_phone)
            return

        yield _step("summary", "Final Answer", {"text": _clean_summary(message.content)})
        return

    tool_call = tool_calls[0]
    tool_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments or "{}")

    yield _step(
        "llm_decision",
        "LLM Selected Tool",
        {
            "tool_name": tool_name,
            "tool_args": args,
            "why_it_matters": "The model converted the user's natural language into a concrete action.",
        },
    )

    if tool_name != "search_restaurant":
        yield _step("understanding", "Request Understood", _understanding_from_tool(tool_name, args))

    yield _step(
        "tool_call",
        TOOL_DISPLAY_NAMES.get(tool_name, tool_name),
        {
            "tool_name": tool_name,
            "arguments": args,
            "executor": "hybrid_llm_directory_resolver" if tool_name == "search_restaurant" else "mock_restaurant_call",
        },
    )
    result = execute_tool(tool_name, args, restaurant_name, restaurant_phone)
    yield _step(
        "tool_result",
        "Directory Result" if tool_name == "search_restaurant" else "Restaurant Response",
        result,
    )

    if tool_name == "search_restaurant":
        if not result.get("success"):
            yield _step("summary", "Final Answer", {"text": "Please specify which restaurant you want me to call."})
            return

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
        yield _step(
            "agent_loop",
            "Agent Loop Continues",
            {
                "message": "The LLM chose the search tool. The resolver used exact matching, LLM semantics, or fallback search, then the agent continued with restaurant context.",
                "next_context": restaurant_name,
            },
        )
        yield from _run_with_llm(user_request, restaurant_name, restaurant_phone)
        return

    kind = _tool_result_kind(tool_name)
    if kind == "availability":
        yield _step(
            "summary",
            "Final Answer",
            merge_summary_with_reservation_ui(_summary_from_tool_result(kind, result), user_request, result),
        )
    else:
        yield _step("summary", "Final Answer", {"text": _summary_from_tool_result(kind, result)})


def _run_without_llm(
    user_request: str,
    restaurant_name: str | None,
    restaurant_phone: str | None,
    include_parser_step: bool = False,
) -> Generator[Step, None, None]:
    text = user_request.lower()

    if include_parser_step:
        yield _step(
            "local_parser",
            "Deterministic Fallback",
            {"message": "Local heuristics are handling the same tool loop without an LLM call."},
        )

    if _is_unsupported(text):
        yield _step("understanding", "Request Understood", {"intent": "unsupported", "reason": "outside_supported_scope"})
        yield _step("summary", "Final Answer", {"text": SUPPORTED_MESSAGE})
        return

    if not restaurant_name or not restaurant_phone:
        yield _step(
            "tool_call",
            TOOL_DISPLAY_NAMES["search_restaurant"],
            {"tool_name": "search_restaurant", "arguments": {"query": user_request}, "executor": "hybrid_llm_directory_resolver"},
        )
        search_result = execute_tool("search_restaurant", {"query": user_request}, None, None)
        yield _step("tool_result", "Directory Result", search_result)
        if not search_result.get("success"):
            yield _step("summary", "Final Answer", {"text": "Please specify which restaurant you want me to call."})
            return

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

    if implies_availability_check(text):
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
    requested_date = _extract_date(text) or "tonight"
    requested_time = _extract_time(text)

    yield _step(
        "understanding",
        "Request Understood",
        {
            "intent": "check_table_availability",
            "party_size": party_size or 2,
            "date": requested_date,
            "time": requested_time,
            "assumptions": {
                "party_size": "Assumed 2 guests when not specified." if party_size is None else None,
                "date": "Assumed tonight when not specified." if requested_date == "tonight" and "tonight" not in text else None,
                "time": "Interpreted bare dinner-hour time as PM." if _has_bare_time(text) else None,
            },
        },
    )

    if not requested_time:
        yield _step("summary", "Final Answer", {"text": CLARIFICATION_MESSAGE})
        return

    args = {"party_size": party_size or 2, "date": requested_date, "time": requested_time}
    yield _step(
        "tool_call",
        TOOL_DISPLAY_NAMES["call_restaurant_check_availability"],
        {"tool_name": "call_restaurant_check_availability", "arguments": args, "executor": "mock_restaurant_call"},
    )
    result = execute_tool("call_restaurant_check_availability", args, name, phone)
    yield _step("tool_result", "Restaurant Response", result)
    yield _step(
        "summary",
        "Final Answer",
        merge_summary_with_reservation_ui(_summary_from_tool_result("availability", result), text, result),
    )


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
        {"tool_name": "call_restaurant_check_hours", "arguments": args, "executor": "mock_restaurant_call"},
    )
    result = execute_tool("call_restaurant_check_hours", args, name, phone)
    yield _step("tool_result", "Restaurant Response", result)
    yield _step("summary", "Final Answer", {"text": _summary_from_tool_result("hours", result)})


def _summary_from_tool_result(kind: str, result: dict[str, Any]) -> str:
    if not result.get("success"):
        return result.get("message") or result.get("error") or "I could not complete that check."

    if kind == "availability":
        party_size = result.get("party_size") or "your party"
        requested_time = result.get("requested_time") or "that time"
        assumptions = _format_assumptions(result.get("assumptions", {}))
        suffix = f" {assumptions}" if assumptions else ""

        if result.get("status") == "available":
            return f"They have a table for {party_size} at {requested_time}.{suffix}"
        if result.get("status") == "party_too_large":
            message = result.get("message") or "That party size is above the restaurant's limit."
            return f"They cannot seat a party of {party_size}. {message}{suffix}"
        if result.get("alternative_time"):
            return f"They do not have a table for {party_size} at {requested_time}, but {result['alternative_time']} is available.{suffix}"
        return f"They do not have a table for {party_size} at {requested_time}.{suffix}"

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
        return {"intent": "check_open_status", "date": args.get("date"), "time": args.get("time") or "now"}
    return {"intent": "unknown"}


def _tool_result_kind(tool_name: str) -> str:
    if tool_name == "call_restaurant_check_availability":
        return "availability"
    if tool_name == "call_restaurant_check_hours":
        return "hours"
    return "unknown"


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
    if match:
        minutes = match.group(2) or "00"
        meridiem = "AM" if match.group(3).startswith("a") else "PM"
        return normalize_time(f"{match.group(1)}:{minutes} {meridiem}")

    bare_match = re.search(r"\b(?:at|around)\s+(\d{1,2})(?::(\d{2}))?\b", text)
    if not bare_match:
        return None

    hour = int(bare_match.group(1))
    minutes = bare_match.group(2) or "00"
    meridiem = "PM" if 1 <= hour <= 11 else "AM"
    return normalize_time(f"{hour}:{minutes} {meridiem}")


def _is_unsupported(text: str) -> bool:
    if implies_availability_check(text):
        return False
    unsupported_words = ["menu", "delivery", "order", "complaint", "review"]
    return any(word in text for word in unsupported_words)


def _is_hours_request(text: str) -> bool:
    return any(word in text for word in ["open", "closed", "hours", "close"])


def _should_force_tool_path(user_request: str) -> bool:
    text = user_request.lower()
    if _is_unsupported(text):
        return False
    return implies_availability_check(text) or _is_hours_request(text)


def _clean_summary(text: str | None) -> str:
    cleaned = (text or "").strip()
    return cleaned or "I can help with table availability or open-status checks."


def _step(step_type: str, title: str, data: dict[str, Any]) -> Step:
    return {"step": step_type, "title": title, "data": data}


def _has_bare_time(text: str) -> bool:
    return bool(re.search(r"\b(?:at|around)\s+\d{1,2}(?::\d{2})?\b", text))


def _format_assumptions(assumptions: dict[str, Any]) -> str:
    values = [value for value in assumptions.values() if value]
    return " ".join(values)


def _as_chat_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
                "strict": tool.get("strict", False),
            },
        }
        for tool in tools
    ]
