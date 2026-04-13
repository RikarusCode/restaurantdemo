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
from .schemas import AgentRequest

app = FastAPI(title="Restaurant Agent Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/restaurants")
def list_restaurants() -> list[dict]:
    """Expose demo restaurants so the frontend can populate the selector."""

    return [public_restaurant(restaurant) for restaurant in RESTAURANTS]


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
