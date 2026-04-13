"""Build reservation funnel UI payloads returned with agent summaries."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def implies_availability_check(text: str) -> bool:
    lowered = text.lower()
    return _is_availability_request(lowered) or is_reservation_request(lowered)


def is_reservation_request(text: str) -> bool:
    lowered = text.lower()
    if "reservation" in lowered or "reserve" in lowered:
        return True
    if "book" in lowered and ("table" in lowered or "reserv" in lowered):
        return True
    return False


def _is_availability_request(text: str) -> bool:
    return any(
        word in text
        for word in ["table", "availability", "available", "avaliable", "seat", "room"]
    )


def format_reservation_date_heading(requested_date: str | None) -> str:
    """Human-readable day and calendar date for the reservation modal."""

    key = (requested_date or "tonight").lower().strip()
    today = datetime.now().date()

    if key in ("tonight", "today"):
        head = "Tonight" if key == "tonight" else "Today"
        target = today
    elif key == "tomorrow":
        head = "Tomorrow"
        target = today + timedelta(days=1)
    else:
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        if key in weekdays:
            want = weekdays[key]
            cur = today.weekday()
            delta = (want - cur) % 7
            target = today + timedelta(days=delta)
            head = key.capitalize()
        else:
            return requested_date or "Tonight"

    cal = target.strftime("%A, %b %d, %Y")
    return f"{head} - {cal}"


def build_reservation_ui_state(user_request: str, result: dict[str, Any]) -> dict[str, Any] | None:
    """Structured UI state for the reservation funnel; None when the CTA should be hidden."""

    if not result.get("success"):
        return None

    status = result.get("status")
    if status not in ("available", "unavailable", "party_too_large"):
        return None

    available = status == "available"
    can_attempt = status in ("available", "unavailable")
    reservation_intent = is_reservation_request(user_request)

    if available:
        label = "Place reservation?"
    elif can_attempt:
        label = "Attempt reservation anyway"
    else:
        label = "Party too large to call"

    disabled_reason = None
    if not can_attempt:
        disabled_reason = result.get("message") or "This party size is outside the restaurant's limit."

    draft = {
        "restaurant_name": result.get("restaurant_name") or "",
        "restaurant_phone": result.get("restaurant_phone") or "",
        "location": result.get("restaurant_address") or "",
        "guest_name": "",
        "date_heading": format_reservation_date_heading(result.get("requested_date")),
        "requested_date": result.get("requested_date") or "tonight",
        "time": result.get("requested_time") or "",
        "party_size": int(result.get("party_size") or 2),
        "availability_status": status,
    }

    return {
        "availability": {
            "status": status,
            "available": available,
            "alternative_time": result.get("alternative_time"),
            "party_size": result.get("party_size"),
            "requested_time": result.get("requested_time"),
        },
        "reservation_button": {
            "visible": True,
            "enabled": can_attempt,
            "label": label,
            "disabled_reason": disabled_reason,
        },
        "reservation_modal": {
            "auto_open": reservation_intent and can_attempt,
            "draft": draft,
        },
    }


def merge_summary_with_reservation_ui(text: str, user_request: str, result: dict[str, Any]) -> dict[str, Any]:
    """Attach optional `ui` block to a final availability summary."""

    payload: dict[str, Any] = {"text": text}
    ui = build_reservation_ui_state(user_request, result)
    if ui:
        payload["ui"] = ui
    return payload
