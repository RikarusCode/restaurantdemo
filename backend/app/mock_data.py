"""Rich deterministic restaurant directory and lookup helpers."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from difflib import get_close_matches
from typing import Any

Slot = dict[str, Any]
Restaurant = dict[str, Any]


def _slot(available: bool, max_party_size: int, note: str) -> Slot:
    return {"available": available, "max_party_size": max_party_size, "note": note}


def _slots(entries: list[tuple[str, bool, int, str]]) -> dict[str, Slot]:
    return {slot_time: _slot(available, max_party_size, note) for slot_time, available, max_party_size, note in entries}


DINNER_TIMES = ["5:00 PM", "5:30 PM", "6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM", "8:00 PM", "8:30 PM", "9:00 PM"]
LUNCH_TIMES = ["11:30 AM", "12:00 PM", "12:30 PM", "1:00 PM", "1:30 PM", "2:00 PM"]


RESTAURANTS: list[Restaurant] = [
    {
        "name": "Kazu Sushi",
        "phone": "415-555-0142",
        "cuisine": "Japanese",
        "style": "sushi bar",
        "price_range": "$$",
        "neighborhood": "Hayes Valley",
        "address": "214 Linden Street, San Francisco, CA",
        "aliases": ["kazu", "kazu sushi", "sushi place", "the sushi place", "japanese place", "sushi spot"],
        "summary": "Compact sushi bar with omakase seats, a few two-top tables, and strong dinner demand.",
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
            "lunch": _slots([
                ("11:30 AM", True, 2, "bar seats"),
                ("12:00 PM", True, 4, "lunch table"),
                ("12:30 PM", True, 2, "counter seats"),
                ("1:00 PM", False, 0, "chef counter booked"),
                ("1:30 PM", True, 4, "late lunch"),
                ("2:00 PM", True, 2, "last lunch seating"),
            ]),
            "dinner": _slots([
                ("5:00 PM", True, 2, "early counter seats"),
                ("5:30 PM", True, 2, "counter seats"),
                ("6:00 PM", True, 2, "small table"),
                ("6:30 PM", True, 4, "main dining room"),
                ("7:00 PM", False, 0, "fully booked"),
                ("7:30 PM", True, 2, "bar seating"),
                ("8:00 PM", True, 4, "late table"),
                ("8:30 PM", False, 0, "chef counter hold"),
                ("9:00 PM", True, 2, "final seating"),
            ]),
            "tomorrow": _slots([
                ("11:30 AM", True, 4, "lunch table"),
                ("12:00 PM", True, 4, "lunch seating"),
                ("5:30 PM", True, 2, "early dinner"),
                ("6:00 PM", True, 2, "small table"),
                ("6:30 PM", True, 4, "main dining room"),
                ("7:00 PM", False, 0, "fully booked"),
                ("7:30 PM", True, 2, "bar seating"),
                ("8:00 PM", True, 2, "late table"),
            ]),
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
        "summary": "Warm neighborhood trattoria with handmade pasta, patio tables, and flexible party sizes.",
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
            "dinner": _slots([
                ("5:00 PM", True, 6, "early dining room"),
                ("5:30 PM", True, 4, "patio"),
                ("6:00 PM", True, 6, "dining room"),
                ("6:30 PM", True, 4, "window table"),
                ("7:00 PM", True, 2, "two-top"),
                ("7:30 PM", False, 0, "peak time booked"),
                ("8:00 PM", True, 4, "late seating"),
                ("8:30 PM", True, 6, "large booth"),
                ("9:00 PM", True, 2, "last seating"),
            ]),
            "tomorrow": _slots([
                ("5:00 PM", True, 8, "family table"),
                ("5:30 PM", True, 4, "early dinner"),
                ("6:00 PM", True, 6, "dining room"),
                ("6:30 PM", True, 4, "patio"),
                ("7:00 PM", True, 4, "main room"),
                ("7:30 PM", True, 2, "two-top"),
                ("8:00 PM", False, 0, "private event block"),
            ]),
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
        "summary": "Waterfront seafood restaurant with larger tables and high sunset demand.",
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
            "lunch": _slots([
                ("11:30 AM", True, 6, "harbor view"),
                ("12:00 PM", True, 8, "main dining room"),
                ("12:30 PM", True, 4, "window table"),
                ("1:00 PM", True, 6, "patio"),
                ("1:30 PM", False, 0, "private lunch block"),
                ("2:00 PM", True, 4, "late lunch"),
            ]),
            "dinner": _slots([
                ("5:00 PM", True, 6, "early seating"),
                ("5:30 PM", True, 4, "early seating"),
                ("6:00 PM", False, 0, "sunset rush"),
                ("6:30 PM", False, 0, "sunset rush"),
                ("7:00 PM", False, 0, "fully booked"),
                ("7:30 PM", False, 0, "fully booked"),
                ("8:00 PM", True, 2, "late two-top"),
                ("8:30 PM", True, 4, "late dining room"),
                ("9:00 PM", False, 0, "closed soon"),
            ]),
            "tomorrow": _slots([
                ("12:00 PM", True, 6, "lunch"),
                ("5:30 PM", True, 4, "early dinner"),
                ("6:00 PM", True, 6, "main dining room"),
                ("6:30 PM", True, 6, "harbor view"),
                ("7:00 PM", True, 4, "window table"),
                ("8:00 PM", False, 0, "event hold"),
            ]),
        },
    },
    {
        "name": "Nopalito Verde",
        "phone": "415-555-0167",
        "cuisine": "Mexican",
        "style": "plant-forward cantina",
        "price_range": "$$",
        "neighborhood": "NoPa",
        "address": "601 Divisadero Street, San Francisco, CA",
        "aliases": [
            "nopalito",
            "nopalito verde",
            "mexican place",
            "taco place",
            "vegetarian place",
            "cantina",
        ],
        "summary": "Plant-forward Mexican cantina with tacos, share plates, and a lively patio.",
        "reservation_policy": "Small parties are flexible; patio requests are first-call-first-held.",
        "capacity": {"two_tops": 9, "four_tops": 9, "patio_tables": 8, "max_party_size": 8},
        "hours": {
            "Monday": ("12:00 PM", "9:00 PM"),
            "Tuesday": ("12:00 PM", "9:00 PM"),
            "Wednesday": ("12:00 PM", "9:00 PM"),
            "Thursday": ("12:00 PM", "10:00 PM"),
            "Friday": ("12:00 PM", "11:00 PM"),
            "Saturday": ("11:00 AM", "11:00 PM"),
            "Sunday": ("11:00 AM", "9:00 PM"),
        },
        "availability": {
            "lunch": _slots([
                ("12:00 PM", True, 4, "patio"),
                ("12:30 PM", True, 6, "communal table"),
                ("1:00 PM", True, 4, "main room"),
                ("1:30 PM", True, 2, "bar seats"),
                ("2:00 PM", True, 6, "late lunch"),
            ]),
            "dinner": _slots([
                ("5:00 PM", True, 6, "patio"),
                ("5:30 PM", True, 4, "main room"),
                ("6:00 PM", True, 8, "communal table"),
                ("6:30 PM", False, 0, "happy hour rush"),
                ("7:00 PM", True, 4, "covered patio"),
                ("7:30 PM", True, 2, "bar seats"),
                ("8:00 PM", False, 0, "fully booked"),
                ("8:30 PM", True, 4, "late patio"),
                ("9:00 PM", True, 2, "final seating"),
            ]),
            "tomorrow": _slots([
                ("12:00 PM", True, 4, "patio"),
                ("5:30 PM", True, 6, "main room"),
                ("6:00 PM", True, 8, "communal table"),
                ("6:30 PM", True, 4, "patio"),
                ("7:00 PM", False, 0, "large-party hold"),
                ("7:30 PM", True, 2, "bar seats"),
                ("8:30 PM", True, 4, "late patio"),
            ]),
        },
    },
]


def normalize_key(value: str | None) -> str:
    return "".join(ch for ch in (value or "").lower() if ch.isalnum())


def normalize_time(value: str | None, assume_pm: bool = False) -> str | None:
    """Normalize common request time formats to h:mm AM/PM."""

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


def lookup_restaurant(name: str | None = None, phone: str | None = None) -> Restaurant | None:
    """Find a restaurant by phone, exact/fuzzy name, alias, cuisine, style, or neighborhood."""

    if phone:
        phone_digits = normalize_key(phone)
        for restaurant in RESTAURANTS:
            if normalize_key(restaurant["phone"]) == phone_digits:
                return restaurant

    if not name:
        return None

    query = normalize_key(name)
    for restaurant in RESTAURANTS:
        searchable = _search_terms(restaurant)
        if any(normalize_key(value) == query for value in searchable):
            return restaurant
        if any(normalize_key(value) and normalize_key(value) in query for value in searchable):
            return restaurant

    choices = {normalize_key(value): restaurant for restaurant in RESTAURANTS for value in _search_terms(restaurant)}
    matches = get_close_matches(query, choices.keys(), n=1, cutoff=0.6)
    return choices[matches[0]] if matches else None


def find_restaurant_in_text(text: str) -> Restaurant | None:
    """Infer a restaurant from free text using names, cuisines, styles, and aliases."""

    return lookup_restaurant(text)


def check_open_status(restaurant: Restaurant, at_datetime: datetime | None = None) -> dict[str, Any]:
    """Return whether the restaurant is open at a provided or current time."""

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
    restaurant: Restaurant,
    party_size: int | None,
    requested_date: str | None,
    requested_time: str | None,
) -> dict[str, Any]:
    """Check deterministic mocked reservation availability."""

    date_key = _date_key(requested_date)
    time_key = normalize_time(requested_time, assume_pm=True) or "7:00 PM"
    party = party_size or 2
    slots = _slots_for_date(restaurant, date_key, time_key)
    slot = slots.get(time_key)
    max_party_size = restaurant["capacity"]["max_party_size"]

    if party > max_party_size:
        return _availability_result(
            status="party_too_large",
            party_size=party,
            requested_date=date_key,
            requested_time=time_key,
            slot=slot,
            alternative=None,
            slots=slots,
            assumptions=_assumptions(party_size, requested_date, requested_time),
            message=f"Maximum party size is {max_party_size}.",
        )

    is_available = bool(slot and slot["available"] and party <= slot["max_party_size"])
    alternative = None if is_available else _best_alternative(slots, party, time_key)

    return _availability_result(
        status="available" if is_available else "unavailable",
        party_size=party,
        requested_date=date_key,
        requested_time=time_key,
        slot=slot,
        alternative=alternative,
        slots=slots,
        assumptions=_assumptions(party_size, requested_date, requested_time),
    )


def _availability_result(
    status: str,
    party_size: int,
    requested_date: str,
    requested_time: str,
    slot: Slot | None,
    alternative: tuple[str, Slot] | None,
    slots: dict[str, Slot],
    assumptions: dict[str, str | None],
    message: str | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "party_size": party_size,
        "requested_date": requested_date,
        "requested_time": requested_time,
        "requested_slot_note": slot.get("note") if slot else "outside listed reservation slots",
        "alternative_time": alternative[0] if alternative else None,
        "alternative_note": alternative[1]["note"] if alternative else None,
        "message": message,
        "assumptions": assumptions,
        "available_slots": [
            {"time": slot_time, "max_party_size": candidate["max_party_size"], "note": candidate["note"]}
            for slot_time, candidate in slots.items()
            if candidate["available"]
        ],
    }


def _best_alternative(slots: dict[str, Slot], party_size: int, requested_time: str) -> tuple[str, Slot] | None:
    requested_minutes = _minutes(requested_time)
    candidates = [
        (slot_time, slot)
        for slot_time, slot in slots.items()
        if slot["available"] and party_size <= slot["max_party_size"]
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda item: abs(_minutes(item[0]) - requested_minutes))


def _slots_for_date(restaurant: Restaurant, date_key: str, requested_time: str) -> dict[str, Slot]:
    if date_key == "tomorrow" and "tomorrow" in restaurant["availability"]:
        return restaurant["availability"]["tomorrow"]
    if _is_lunch_time(requested_time) and "lunch" in restaurant["availability"]:
        return restaurant["availability"]["lunch"]
    return restaurant["availability"].get("dinner", restaurant["availability"].get("lunch", {}))


def _assumptions(party_size: int | None, requested_date: str | None, requested_time: str | None) -> dict[str, str | None]:
    return {
        "party_size": "Assumed 2 guests when not specified." if party_size is None else None,
        "date": "Assumed tonight when not specified." if not requested_date else None,
        "time": "Interpreted bare dinner-hour time as PM." if requested_time and requested_time.isdigit() else None,
    }


def _date_key(requested_date: str | None) -> str:
    if not requested_date:
        return "tonight"
    lowered = requested_date.lower()
    if "tomorrow" in lowered:
        return "tomorrow"
    if lowered in {"today", "tonight"}:
        return "tonight"
    return lowered


def _search_terms(restaurant: Restaurant) -> list[str]:
    return [
        restaurant["name"],
        restaurant["cuisine"],
        restaurant["style"],
        restaurant["neighborhood"],
        *restaurant.get("aliases", []),
    ]


def _parse_time(value: str) -> time:
    return datetime.strptime(value, "%I:%M %p").time()


def _minutes(value: str) -> int:
    parsed = datetime.strptime(value, "%I:%M %p")
    return parsed.hour * 60 + parsed.minute


def _is_lunch_time(value: str) -> bool:
    parsed = datetime.strptime(value, "%I:%M %p").time()
    return time(10, 0) <= parsed <= time(15, 0)
