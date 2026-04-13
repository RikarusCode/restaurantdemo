"""FastAPI entrypoint that streams agent pipeline steps as NDJSON."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from .agent import run_agent
from .mock_data import RESTAURANTS
from .restaurant_search import public_restaurant
from .retell_service import place_reservation_call
from .schemas import AgentRequest, ReservationCallRequest, ReservationCallResponse

app = FastAPI(title="TableCall Restaurant Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/restaurants")
def list_restaurants() -> list[dict]:
    """Expose restaurants so the frontend can populate the selector."""

    return [public_restaurant(restaurant) for restaurant in RESTAURANTS]


@app.post("/reservation/call", response_model=ReservationCallResponse)
def reservation_call_endpoint(request: ReservationCallRequest) -> ReservationCallResponse:
    """Place an outbound reservation attempt through Retell and wait for a terminal call status."""

    outcome = place_reservation_call(
        restaurant_name=request.restaurant_name,
        restaurant_phone=request.restaurant_phone,
        location=request.location,
        party_size=request.party_size,
        requested_time=request.requested_time,
        date_heading=request.date_heading,
        requested_date_token=request.requested_date_token,
        notes=request.notes,
    )
    return ReservationCallResponse(
        confirmed=outcome.confirmed,
        message=outcome.message,
        call_id=outcome.call_id,
        call_status=outcome.raw_status,
    )


@app.post("/agent/run")
def run_agent_endpoint(request: AgentRequest) -> StreamingResponse:
    """Stream each agent step as one JSON object per line."""

    def generate():
        for step in run_agent(
            request.user_request,
            request.restaurant_name,
            request.restaurant_phone,
        ):
            yield json.dumps(step, default=str) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"X-Content-Type-Options": "nosniff"},
    )


_frontend = Path(__file__).resolve().parent.parent.parent / "frontend"
if _frontend.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
