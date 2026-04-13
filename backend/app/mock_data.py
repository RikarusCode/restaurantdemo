"""Deterministic mock restaurant data and lookup helpers for the demo."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from difflib import get_close_matches
from typing import Any


RESTAURANTS: list[dict[str, Any]] = [
    {
        "name": "Kazu Sushi",
        "phone": "415-555-0142",
        "cuisine": "Japanese",
        "address": "214 Linden Street, San Francisco, CA",
        "hours": {
            "Monday": ("11:30 AM", "10:00 PM"),
            "Tuesday": ("11:30 AM", "10:00 PM"),
            "Wednesday": ("11:30 AM", "10:00 PM"),
            "Thursday": ("11:30 AM", "10:00 PM"),
            "Friday": ("11:30 AM", "11:00 PM"),
            "Saturday": ("12:00 PM", "11:00 PM"),
            "Sunday": ("12:00 PM", "9:00 PM"),
        },
        "availability": {
            "tonight": {"7:00 PM": False, "7:30 PM": True, "8:00 PM": True},
            "tomorrow": {"12:00 PM": True, "6:30 PM": True, "7:00 PM": False},
        },
    },
    {
        "name": "Luna Trattoria",
        "phone": "415-555-0188",
        "cuisine": "Italian",
        "address": "88 Valencia Street, San Francisco, CA",
        "hours": {
            "Monday": ("5:00 PM", "10:00 PM"),
            "Tuesday": ("5:00 PM", "10:00 PM"),
            "Wednesday": ("5:00 PM", "10:00 PM"),
            "Thursday": ("5:00 PM", "10:00 PM"),
            "Friday": ("5:00 PM", "11:00 PM"),
            "Saturday": ("4:00 PM", "11:00 PM"),
            "Sunday": ("4:00 PM", "9:00 PM"),
        },
        "availability": {
            "tonight": {"6:30 PM": True, "7:00 PM": True, "7:30 PM": False},
            "tomorrow": {"5:30 PM": True, "7:00 PM": True, "8:00 PM": False},
        },
    },
    {
        "name": "Harbor Garden",
        "phone": "415-555-0119",
        "cuisine": "Seafood",
        "address": "9 Embarcadero Center, San Francisco, CA",
        "hours": {
            "Monday": ("11:00 AM", "9:00 PM"),
            "Tuesday": ("11:00 AM", "9:00 PM"),
            "Wednesday": ("11:00 AM", "9:00 PM"),
            "Thursday": ("11:00 AM", "9:00 PM"),
            "Friday": ("11:00 AM", "10:00 PM"),
            "Saturday": ("10:00 AM", "10:00 PM"),
            "Sunday": ("10:00 AM", "8:00 PM"),
        },
        "availability": {
            "tonight": {"6:00 PM": False, "7:00 PM": False, "7:30 PM": False},
            "tomorrow": {"12:00 PM": True, "6:00 PM": True, "7:00 PM": True},
        },
    },
]


def _normalize(value: str | None) -> str:
    return "".join(ch for ch in (value or "").lower() if ch.isalnum())


def _parse_time(value: str) -> time:
    return datetime.strptime(value, "%I:%M %p").time()


def normalize_time(value: str | None) -> str | None:
    """Normalize common demo time formats to h:mm AM/PM."""

    if not value:
        return None
    cleaned = value.strip().upper().replace(".", "")
    if cleaned == "NOON":
        return "12:00 PM"
    if cleaned == "MIDNIGHT":
        return "12:00 AM"
    for pattern in ("%I:%M %p", "%I %p"):
        try:
            return datetime.strptime(cleaned, pattern).strftime("%I:%M %p").lstrip("0")
        except ValueError:
            continue
    return value


def lookup_restaurant(name: str | None = None, phone: str | None = None) -> dict[str, Any] | None:
    """Find a restaurant by exact/fuzzy name or exact phone."""

    if phone:
        phone_digits = _normalize(phone)
        for restaurant in RESTAURANTS:
            if _normalize(restaurant["phone"]) == phone_digits:
                return restaurant

    if name:
        normalized_name = _normalize(name)
        for restaurant in RESTAURANTS:
            if _normalize(restaurant["name"]) == normalized_name:
                return restaurant

        choices = {_normalize(restaurant["name"]): restaurant for restaurant in RESTAURANTS}
        matches = get_close_matches(normalized_name, choices.keys(), n=1, cutoff=0.65)
        if matches:
            return choices[matches[0]]

    return None


def find_restaurant_in_text(text: str) -> dict[str, Any] | None:
    """Infer a restaurant by matching known mock names in free text."""

    normalized_text = _normalize(text)
    for restaurant in RESTAURANTS:
        if _normalize(restaurant["name"]) in normalized_text:
            return restaurant

    choices = {_normalize(restaurant["name"]): restaurant for restaurant in RESTAURANTS}
    matches = get_close_matches(normalized_text, choices.keys(), n=1, cutoff=0.5)
    return choices[matches[0]] if matches else None


def check_open_status(restaurant: dict[str, Any], at_datetime: datetime | None = None) -> dict[str, Any]:
    """Return whether the restaurant is open at the provided or current time."""

    now = at_datetime or datetime.now()
    day_name = now.strftime("%A")
    opens_at, closes_at = restaurant["hours"][day_name]
    open_time = _parse_time(opens_at)
    close_time = _parse_time(closes_at)
    current_time = now.time()
    is_open = open_time <= current_time <= close_time

    opens_next = None
    if not is_open:
        if current_time < open_time:
            opens_next = f"today at {opens_at}"
        else:
            next_day = now
            for _ in range(8):
                next_day += timedelta(days=1)
                next_day_name = next_day.strftime("%A")
                next_open, _ = restaurant["hours"][next_day_name]
                opens_next = f"{'tomorrow' if (next_day.date() - now.date()).days == 1 else next_day_name} at {next_open}"
                break

    return {
        "is_open": is_open,
        "checked_day": day_name,
        "opens_at": opens_at,
        "closes_at": closes_at,
        "opens_next": opens_next,
    }


def check_availability(
    restaurant: dict[str, Any],
    party_size: int | None,
    requested_date: str | None,
    requested_time: str | None,
) -> dict[str, Any]:
    """Check deterministic mocked availability for party size and time."""

    date_key = "tomorrow" if (requested_date or "").lower() == "tomorrow" else "tonight"
    time_key = normalize_time(requested_time) or "7:00 PM"
    slots = restaurant["availability"].get(date_key, {})
    is_available = bool(slots.get(time_key))
    alternative_time = None

    if not is_available:
        for slot_time, available in slots.items():
            if available:
                alternative_time = slot_time
                break

    return {
        "status": "available" if is_available else "unavailable",
        "party_size": party_size,
        "requested_date": date_key,
        "requested_time": time_key,
        "alternative_time": alternative_time,
        "available_slots": [slot_time for slot_time, available in slots.items() if available],
    }
