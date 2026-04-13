"""Restaurant lookup helpers used by the search tool and frontend."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from .config import settings
from .mock_data import RESTAURANTS, find_restaurant_in_text, lookup_restaurant
from .mock_data import normalize_key

SEARCH_RESOLVER_TIMEOUT_SECONDS = 8.0


def search_restaurants(query: str) -> dict[str, Any]:
    """Resolve a restaurant with exact local lookup, LLM semantics, then fallback heuristics."""

    exact = _exact_local_match(query)
    if exact:
        return _success(exact, "local_exact_match", "high", "Matched an exact restaurant name, alias, cuisine, style, or neighborhood.")

    llm_result = _llm_semantic_match(query)
    if llm_result["restaurant"]:
        return _success(
            llm_result["restaurant"],
            "llm_semantic_resolver",
            llm_result["confidence"],
            llm_result["reason"],
        )

    inferred = find_restaurant_in_text(query)
    if inferred:
        return _success(inferred, "deterministic_fallback", "medium", "Matched with local fuzzy search after semantic resolution was unavailable or inconclusive.")

    return {
        "success": False,
        "source": "local_restaurant_directory",
        "confidence": "low",
        "resolver": "unresolved",
        "reason": llm_result["reason"] or "No local or semantic match found.",
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


def _success(restaurant: dict[str, Any], resolver: str, confidence: str, reason: str) -> dict[str, Any]:
    return {
        "success": True,
        "source": "local_restaurant_directory",
        "resolver": resolver,
        "confidence": confidence,
        "reason": reason,
        "restaurant": public_restaurant(restaurant),
    }


def _exact_local_match(query: str) -> dict[str, Any] | None:
    normalized_query = normalize_key(query)
    if not normalized_query:
        return None

    for restaurant in RESTAURANTS:
        terms = [
            restaurant["name"],
            restaurant["phone"],
            restaurant["cuisine"],
            restaurant["style"],
            restaurant["neighborhood"],
            *restaurant.get("aliases", []),
        ]
        if any(normalize_key(term) == normalized_query for term in terms):
            return restaurant
    return None


def _llm_semantic_match(query: str) -> dict[str, Any]:
    if not settings.llm_api_key:
        return {"restaurant": None, "confidence": "low", "reason": "No LLM provider is configured for semantic restaurant resolution."}

    directory = [
        {
            "name": restaurant["name"],
            "cuisine": restaurant["cuisine"],
            "style": restaurant["style"],
            "neighborhood": restaurant["neighborhood"],
            "summary": restaurant["summary"],
            "aliases": restaurant["aliases"],
        }
        for restaurant in RESTAURANTS
    ]
    prompt = (
        "Resolve the user's restaurant description to exactly one restaurant from this local directory. "
        "Use semantic meaning, not only exact words. For example, vegan can match plant-forward. "
        "Return JSON only with keys: restaurant_name, confidence, reason. "
        "Use null for restaurant_name if there is not enough evidence.\n\n"
        f"Directory:\n{json.dumps(directory, indent=2)}\n\n"
        f"User description: {query}"
    )

    try:
        client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=SEARCH_RESOLVER_TIMEOUT_SECONDS,
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a precise restaurant directory resolver."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        parsed = _parse_json_object(content)
        restaurant = lookup_restaurant(parsed.get("restaurant_name"))
        confidence = parsed.get("confidence") or "medium"
        reason = parsed.get("reason") or "The LLM semantically matched the request to the directory."
        return {"restaurant": restaurant, "confidence": confidence, "reason": reason}
    except Exception as exc:
        return {
            "restaurant": None,
            "confidence": "low",
            "reason": f"LLM semantic resolver unavailable: {exc.__class__.__name__}.",
        }


def _parse_json_object(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start : end + 1])
        raise
