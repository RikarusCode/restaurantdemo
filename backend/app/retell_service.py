"""Retell AI outbound calls for reservation attempts (isolated provider layer)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from retell import Retell

from .config import settings
from .phone_format import to_e164


@dataclass
class ReservationCallOutcome:
    """Result of a Retell reservation attempt."""

    ok: bool
    confirmed: bool
    call_state: str
    message: str
    call_id: str | None = None
    raw_status: str | None = None


def resolve_dial_number(restaurant_phone: str) -> str:
    """Pick the callee number: optional global test override, else restaurant directory."""

    if settings.tablecall_dial_override:
        return to_e164(settings.tablecall_dial_override)
    return to_e164(restaurant_phone)


def _dynamic_variables(payload: dict[str, Any]) -> dict[str, str]:
    """Retell dynamic variables are string key-value pairs."""

    return {key: str(value) for key, value in payload.items() if value is not None}


def _interpret_confirmation(call_analysis: Any, call_status: str) -> tuple[bool, str]:
    """
    Determine whether a reservation was confirmed.

    Prefer a boolean `reservation_confirmed` field in post-call custom analysis when configured
    on the Retell agent. Otherwise fall back to call_successful with voicemail detection.
    """

    if call_status == "error":
        return False, "The call did not complete successfully."

    if not call_analysis:
        return False, "The call ended before analysis was available. Check the Retell dashboard or try again."

    custom = getattr(call_analysis, "custom_analysis_data", None)
    if isinstance(custom, dict) and "reservation_confirmed" in custom:
        if custom.get("reservation_confirmed") is True:
            return True, "Reservation confirmed."
        return False, "The restaurant did not confirm a reservation on this call."

    in_vm = getattr(call_analysis, "in_voicemail", None)
    successful = getattr(call_analysis, "call_successful", None)

    if in_vm:
        return False, "The call reached voicemail; no live confirmation."

    if successful is True:
        return True, "The call completed successfully and the agent marked it as successful."

    if successful is False:
        return False, "The agent marked the call as unsuccessful."

    return False, "Could not determine confirmation from this call. Add a `reservation_confirmed` boolean in Retell post-call analysis for a definitive signal."


def _start_error_message(exc: Exception) -> str:
    detail = f"{exc.__class__.__name__}: {exc}"
    if "No outbound agent id set up for phone number" in str(exc):
        return (
            "Retell could not choose an outbound agent for RETELL_FROM_NUMBER. "
            "Either bind your reservation agent as the outbound agent for that phone number "
            "in Retell, or set RETELL_AGENT_ID in .env to that agent's id. "
            f"Retell detail: {detail}"
        )
    return f"Could not start the Retell call: {detail}"


def place_reservation_call(
    *,
    restaurant_name: str,
    restaurant_phone: str,
    location: str | None,
    party_size: int,
    requested_time: str,
    date_heading: str,
    requested_date_token: str | None,
    notes: str | None = None,
) -> ReservationCallOutcome:
    """Start an outbound Retell call and block until a terminal status is observed."""

    if not settings.retell_api_key:
        return ReservationCallOutcome(
            ok=False,
            confirmed=False,
            call_state="not_configured",
            message="Retell is not configured. Set RETELL_API_KEY and RETELL_FROM_NUMBER in .env.",
        )
    if not settings.retell_from_number:
        return ReservationCallOutcome(
            ok=False,
            confirmed=False,
            call_state="not_configured",
            message="RETELL_FROM_NUMBER is missing. Add your Retell-owned caller ID.",
        )

    to_number = resolve_dial_number(restaurant_phone)
    from_number = to_e164(settings.retell_from_number)

    client = Retell(api_key=settings.retell_api_key)

    dyn = _dynamic_variables(
        {
            "restaurant_name": restaurant_name,
            "party_size": party_size,
            "reservation_time": requested_time,
            "reservation_date": date_heading,
            "requested_date_token": requested_date_token or "",
            "location": location or "",
            "notes": notes or "",
        }
    )

    try:
        create_kwargs: dict[str, Any] = {
            "from_number": from_number,
            "to_number": to_number,
            "retell_llm_dynamic_variables": dyn,
        }
        if settings.retell_agent_id:
            create_kwargs["override_agent_id"] = settings.retell_agent_id

        created = client.call.create_phone_call(**create_kwargs)
    except Exception as exc:
        return ReservationCallOutcome(
            ok=False,
            confirmed=False,
            call_state="start_failed",
            message=_start_error_message(exc),
        )

    call_id = getattr(created, "call_id", None)
    if not call_id:
        return ReservationCallOutcome(
            ok=False,
            confirmed=False,
            call_state="start_failed",
            message="Retell did not return a call id.",
        )

    deadline = time.monotonic() + settings.retell_call_max_wait_seconds

    last_status = "registered"
    while time.monotonic() < deadline:
        try:
            current = client.call.retrieve(call_id)
        except Exception as exc:
            return ReservationCallOutcome(
                ok=False,
                confirmed=False,
                call_state="poll_failed",
                message=f"Lost contact with Retell while polling the call: {exc.__class__.__name__}: {exc}",
                call_id=call_id,
                raw_status=last_status,
            )

        last_status = current.call_status
        if current.call_status in ("ended", "error"):
            if current.call_status == "ended" and current.call_analysis is None:
                for _ in range(10):
                    time.sleep(1.0)
                    current = client.call.retrieve(call_id)
                    if current.call_analysis is not None:
                        break

            confirmed, msg = _interpret_confirmation(current.call_analysis, current.call_status)
            ok = current.call_status != "error"
            return ReservationCallOutcome(
                ok=ok,
                confirmed=confirmed and ok,
                call_state="completed" if ok else "failed",
                message=msg,
                call_id=call_id,
                raw_status=current.call_status,
            )

        time.sleep(settings.retell_poll_interval_seconds)

    return ReservationCallOutcome(
        ok=False,
        confirmed=False,
        call_state="timed_out",
        message="Timed out waiting for the call to finish.",
        call_id=call_id,
        raw_status=last_status,
    )
