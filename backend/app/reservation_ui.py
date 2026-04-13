"""Build reservation funnel UI payloads returned with agent summaries."""

from __future__ import annotations

from datetime import datetime, timedelta


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
            return f"{requested_date}"

    cal = target.strftime("%A, %b %d, %Y")
    return f"{head} · {cal}"


def build_reservation_ui_state(user_request: str, result: dict) -> dict | None:
    """Structured UI state for the reservation funnel; None when the CTA should be hidden."""

    if not result.get("success"):
        return None

    status = result.get("status")
    if status not in ("available", "unavailable", "party_too_large"):
        return None

    available = status == "available"
    lowered = user_request.lower()
    reservation_intent = is_reservation_request(lowered)
    auto_open = reservation_intent and available

    cta_label = "Place reservation?" if available else "Attempt reservation anyway"

    return {
        "reservation": {
            "show": True,
            "cta_label": cta_label,
            "auto_open_modal": auto_open,
            "draft": {
                "restaurant_name": result.get("restaurant_name") or "",
                "restaurant_phone": result.get("restaurant_phone") or "",
                "location": result.get("restaurant_address") or "",
                "date_heading": format_reservation_date_heading(result.get("requested_date")),
                "requested_date": result.get("requested_date") or "tonight",
                "time": result.get("requested_time") or "",
                "party_size": int(result.get("party_size") or 2),
                "mock_available": available,
            },
        }
    }


def merge_summary_with_reservation_ui(text: str, user_request: str, result: dict) -> dict:
    """Attach optional `ui` block to a final availability summary."""

    payload: dict = {"text": text}
    ui = build_reservation_ui_state(user_request, result)
    if ui:
        payload["ui"] = ui
    return payload
