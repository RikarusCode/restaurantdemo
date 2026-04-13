"""Restaurant resolution layer using mock data with an LLM-shaped extension point."""

from typing import Optional

from .mock_data import find_restaurant_in_text, lookup_restaurant


def resolve_restaurant_info(
    user_request: str,
    restaurant_name: Optional[str],
    restaurant_phone: Optional[str],
) -> tuple[Optional[str], Optional[str], dict]:
    """Resolve restaurant name and phone from supplied fields or mock search."""

    if restaurant_name and restaurant_phone:
        return restaurant_name, restaurant_phone, {"source": "user_supplied", "confidence": "high"}

    matched = lookup_restaurant(restaurant_name, restaurant_phone)
    if matched:
        return matched["name"], matched["phone"], {"source": "provided_field_match", "confidence": "high"}

    inferred = find_restaurant_in_text(user_request)
    if inferred:
        return inferred["name"], inferred["phone"], {"source": "mock_text_match", "confidence": "medium"}

    return restaurant_name, restaurant_phone, {"source": "unresolved", "confidence": "low"}
