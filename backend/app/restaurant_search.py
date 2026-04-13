"""Restaurant lookup helpers used by the search tool and demo UI."""

from __future__ import annotations

from typing import Any

from .mock_data import RESTAURANTS, find_restaurant_in_text, lookup_restaurant


def search_restaurants(query: str) -> dict[str, Any]:
    """Search the local restaurant directory and return trace-friendly metadata."""

    exact = lookup_restaurant(query)
    inferred = exact or find_restaurant_in_text(query)

    if inferred:
        return {
            "success": True,
            "source": "mock_restaurant_directory",
            "confidence": "high" if exact else "medium",
            "restaurant": public_restaurant(inferred),
        }

    return {
        "success": False,
        "source": "mock_restaurant_directory",
        "confidence": "low",
        "error": f"No restaurant found for '{query}'.",
        "candidates": [public_restaurant(restaurant) for restaurant in RESTAURANTS],
    }


def public_restaurant(restaurant: dict[str, Any]) -> dict[str, Any]:
    """Return the public fields shown in the frontend and traces."""

    return {
        "name": restaurant["name"],
        "phone": restaurant["phone"],
        "cuisine": restaurant["cuisine"],
        "style": restaurant["style"],
        "price_range": restaurant["price_range"],
        "neighborhood": restaurant["neighborhood"],
        "address": restaurant["address"],
        "summary": restaurant["summary"],
        "reservation_policy": restaurant["reservation_policy"],
        "capacity": restaurant["capacity"],
        "aliases": restaurant["aliases"],
        "hours": restaurant["hours"],
        "availability": restaurant["availability"],
    }
