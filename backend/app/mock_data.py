"""Rich deterministic restaurant directory and lookup helpers for the demo."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from difflib import get_close_matches
from typing import Any


RESTAURANTS: list[dict[str, Any]] = [
    {
        "name": "Kazu Sushi",
        "phone": "415-555-0142",
        "cuisine": "Japanese",
        "style": "sushi bar",
        "price_range": "$$",
        "neighborhood": "Hayes Valley",
        "address": "214 Linden Street, San Francisco, CA",
        "aliases": ["kazu", "kazu sushi", "sushi place", "the sushi place", "japanese place", "sushi spot"],
        "summary": "Compact neighborhood sushi bar with omakase seats and a few two-top tables.",
        "reservation_policy": "Same-day tables are held by phone; parties over 6 are limited.",
        "capacity": {"two_tops": 8, "four_tops": 4, "bar_seats": 10, "max_party_size": 6},
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
            "tonight": {
                "5:30 PM": {"available": True, "max_party_size": 2, "note": "counter seats"},
                "6:00 PM": {"available": True, "max_party_size": 2, "note": "small table"},
                "6:30 PM": {"available": True, "max_party_size": 4, "note": "main dining room"},
                "7:00 PM": {"available": False, "max_party_size": 0, "note": "fully booked"},
                "7:30 PM": {"available": True, "max_party_size": 2, "note": "bar seating"},
                "8:00 PM": {"available": True, "max_party_size": 4, "note": "table available"},
            },
            "tomorrow": {
                "12:00 PM": {"available": True, "max_party_size": 4, "note": "lunch seating"},
                "6:00 PM": {"available": True, "max_party_size": 2, "note": "early dinner"},
                "6:30 PM": {"available": True, "max_party_size": 4, "note": "main dining room"},
                "7:00 PM": {"available": False, "max_party_size": 0, "note": "fully booked"},
                "8:00 PM": {"available": True, "max_party_size": 2, "note": "late table"},
            },
        },
    },
    {
        "name": "Luna Trattoria",
        "phone": "415-555-0188",
        "cuisine": "Italian",
        "style": "trattoria",
        "price_range": "$$",
        "neighborhood": "Mission District",
        "address": "88 Valencia Street, San Francisco, CA",
        "aliases": ["luna", "luna trattoria", "italian place", "pasta place", "trattoria"],
        "summary": "Warm neighborhood trattoria with handmade pasta and a busy dinner rush.",
        "reservation_policy": "Phone holds are available until 15 minutes after the requested time.",
        "capacity": {"two_tops": 10, "four_tops": 7, "patio_tables": 6, "max_party_size": 8},
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
            "tonight": {
                "5:30 PM": {"available": True, "max_party_size": 4, "note": "patio"},
                "6:00 PM": {"available": True, "max_party_size": 6, "note": "dining room"},
                "6:30 PM": {"available": True, "max_party_size": 4, "note": "window table"},
                "7:00 PM": {"available": True, "max_party_size": 2, "note": "two-top"},
                "7:30 PM": {"available": False, "max_party_size": 0, "note": "peak time booked"},
                "8:00 PM": {"available": True, "max_party_size": 4, "note": "late seating"},
            },
            "tomorrow": {
                "5:30 PM": {"available": True, "max_party_size": 4, "note": "early dinner"},
                "6:00 PM": {"available": True, "max_party_size": 6, "note": "dining room"},
                "7:00 PM": {"available": True, "max_party_size": 4, "note": "main room"},
                "8:00 PM": {"available": False, "max_party_size": 0, "note": "private event block"},
            },
        },
    },
    {
        "name": "Harbor Garden",
        "phone": "415-555-0119",
        "cuisine": "Seafood",
        "style": "waterfront seafood",
        "price_range": "$$$",
        "neighborhood": "Embarcadero",
        "address": "9 Embarcadero Center, San Francisco, CA",
        "aliases": ["harbor", "harbor garden", "seafood place", "fish place", "waterfront place"],
        "summary": "Seafood restaurant near the waterfront with larger tables and sunset demand.",
        "reservation_policy": "Same-day checks are possible, but sunset hours fill quickly.",
        "capacity": {"two_tops": 6, "four_tops": 8, "six_tops": 4, "max_party_size": 10},
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
            "tonight": {
                "5:30 PM": {"available": True, "max_party_size": 4, "note": "early seating"},
                "6:00 PM": {"available": False, "max_party_size": 0, "note": "sunset rush"},
                "6:30 PM": {"available": False, "max_party_size": 0, "note": "sunset rush"},
                "7:00 PM": {"available": False, "max_party_size": 0, "note": "fully booked"},
                "7:30 PM": {"available": False, "max_party_size": 0, "note": "fully booked"},
                "8:00 PM": {"available": True, "max_party_size": 2, "note": "late two-top"},
            },
            "tomorrow": {
                "12:00 PM": {"available": True, "max_party_size": 6, "note": "lunch"},
                "5:30 PM": {"available": True, "max_party_size": 4, "note": "early dinner"},
                "6:00 PM": {"available": True, "max_party_size": 6, "note": "main dining room"},
                "7:00 PM": {"available": True, "max_party_size": 4, "note": "window table"},
                "8:00 PM": {"available": False, "max_party_size": 0, "note": "event hold"},
            },
        },
    },
]


def _normalize(value: str | None) -> str:
    return "".join(ch for ch in (value or "").lower() if ch.isalnum())


def _parse_time(value: str) -> time:
    return datetime.strptime(value, "%I:%M %p").time()


def normalize_time(value: str | None, assume_pm: bool = False) -> str | None:
    """Normalize common demo time formats to h:mm AM/PM."""

    if not value:
        return None

    cleaned = value.strip().upper().replace(".", "")
    if cleaned == "NOON":
        return "12:00 PM"
    if cleaned == "MIDNIGHT":
        return "12:00 AM"
    if assume_pm and cleaned.isdigit():
        return f"{int(cleaned)}:00 PM"

    for pattern in ("%I:%M %p", "%I %p"):
        try:
            return datetime.strptime(cleaned, pattern).strftime("%I:%M %p").lstrip("0")
        except ValueError:
            continue

    return value


def lookup_restaurant(name: str | None = None, phone: str | None = None) -> dict[str, Any] | None:
    """Find a restaurant by exact/fuzzy name, alias, cuisine, style, or phone."""

    if phone:
        phone_digits = _normalize(phone)
        for restaurant in RESTAURANTS:
            if _normalize(restaurant["phone"]) == phone_digits:
                return restaurant

    if not name:
        return None

    normalized_name = _normalize(name)
    for restaurant in RESTAURANTS:
        searchable = [
            restaurant["name"],
            restaurant["cuisine"],
            restaurant["style"],
            restaurant["neighborhood"],
            *restaurant.get("aliases", []),
        ]
        if any(_normalize(value) == normalized_name for value in searchable):
            return restaurant
        if any(_normalize(value) in normalized_name for value in searchable):
            return restaurant

    choices = {
        _normalize(value): restaurant
        for restaurant in RESTAURANTS
        for value in [restaurant["name"], restaurant["cuisine"], restaurant["style"], *restaurant.get("aliases", [])]
    }
    matches = get_close_matches(normalized_name, choices.keys(), n=1, cutoff=0.6)
    return choices[matches[0]] if matches else None


def find_restaurant_in_text(text: str) -> dict[str, Any] | None:
    """Infer a restaurant by matching known names, cuisines, and aliases in text."""

    return lookup_restaurant(text)


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
            next_day = now + timedelta(days=1)
            next_day_name = next_day.strftime("%A")
            next_open, _ = restaurant["hours"][next_day_name]
            label = "tomorrow" if (next_day.date() - now.date()).days == 1 else next_day_name
            opens_next = f"{label} at {next_open}"

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

    date_key = _normalize_date_key(requested_date)
    time_key = normalize_time(requested_time, assume_pm=True) or "7:00 PM"
    party = party_size or 2
    slots = restaurant["availability"].get(date_key, {})
    slot = slots.get(time_key)
    is_available = bool(slot and slot["available"] and party <= slot["max_party_size"])
    alternative_time = None
    alternative_note = None

    if not is_available:
        for slot_time, candidate in slots.items():
            if candidate["available"] and party <= candidate["max_party_size"]:
                alternative_time = slot_time
                alternative_note = candidate.get("note")
                break

    return {
        "status": "available" if is_available else "unavailable",
        "party_size": party,
        "requested_date": date_key,
        "requested_time": time_key,
        "requested_slot_note": slot.get("note") if slot else "not listed in table",
        "alternative_time": alternative_time,
        "alternative_note": alternative_note,
        "assumptions": {
            "party_size": "Assumed 2 guests when not specified." if party_size is None else None,
            "date": "Assumed tonight when not specified." if not requested_date else None,
            "time": "Interpreted bare dinner-hour time as PM." if requested_time and requested_time.isdigit() else None,
        },
        "available_slots": [
            {"time": slot_time, "max_party_size": candidate["max_party_size"], "note": candidate["note"]}
            for slot_time, candidate in slots.items()
            if candidate["available"]
        ],
    }


def _normalize_date_key(requested_date: str | None) -> str:
    if not requested_date:
        return "tonight"
    lowered = requested_date.lower()
    if "tomorrow" in lowered:
        return "tomorrow"
    return "tonight" if lowered in {"today", "tonight"} else lowered
