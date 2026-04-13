"""Normalize directory phone strings to E.164 for telephony APIs."""

from __future__ import annotations


def to_e164(raw: str | None) -> str:
    """Best-effort US-centric E.164 normalization."""

    if not raw or not str(raw).strip():
        raise ValueError("Phone number is required.")

    text = str(raw).strip()
    if text.startswith("+"):
        digits = "".join(ch for ch in text[1:] if ch.isdigit())
        return f"+{digits}"

    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return f"+{digits}"
