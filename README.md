# Restaurant Agent Demo

A small end-to-end demo of an LLM-powered restaurant agent. The app accepts a restaurant-related request, extracts structured intent, invokes a mocked restaurant-call tool, and returns a concise user-facing answer with trace fields visible for evaluation.

## Supported Features

- Check table availability.
- Check whether a restaurant is open.
- Show intermediate agent steps:
  - parsed intent
  - extracted slots
  - selected tool
  - tool result
  - final summary

## Stretch Goal

If restaurant name or phone are missing, the backend tries to resolve the restaurant from the request using the local mock restaurant dataset. This keeps the search layer reliable for the demo while leaving a clean abstraction for a real Places API later.

## Architecture

- `backend/app/main.py`: FastAPI app and `/agent/run` orchestration.
- `backend/app/schemas.py`: Pydantic request, intent, tool, and response models.
- `backend/app/agent.py`: OpenAI structured intent parsing plus deterministic summary formatting.
- `backend/app/tools.py`: Mocked tool invocation and execution.
- `backend/app/mock_data.py`: In-memory restaurants, hours, and reservation slots.
- `backend/app/restaurant_search.py`: Restaurant resolution from supplied info or request text.
- `backend/app/config.py`: Minimal environment settings.
- `frontend/`: Plain HTML, CSS, and JavaScript demo UI.

The mocked tool execution is intentional: it focuses the demo on agent orchestration, reliable state transitions, and inspectable behavior without introducing telephony, scraping, scheduling queues, or database complexity.

## Setup

Create a virtual environment and install backend dependencies:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copy the example environment file and add your key if you want OpenAI-backed parsing:

```bash
copy ..\.env.example ..\.env
```

Environment variables:

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

If `OPENAI_API_KEY` is not set, the backend uses a small deterministic fallback parser so the demo remains runnable.

## Run

Start the backend from the repository root:

```bash
py -m uvicorn backend.app.main:app --reload --env-file .env
```

Open the frontend:

```bash
frontend/index.html
```

The frontend calls `http://localhost:8000/agent/run`.

## Example Requests

- `Call this restaurant and ask if they have a table for 2 tonight at 7 PM.`
- `Check if this restaurant is open right now.`
- `Is Kazu Sushi open tomorrow at noon?`
- `Can you book a table for me?`
- `Do they have room for 4?`

## Known Limitations

- Restaurant calls are mocked, not live.
- The search layer only resolves restaurants from the local demo dataset.
- No persistence, authentication, background jobs, or telephony integration.
- Date and time handling is intentionally lightweight for demo clarity.

## Tradeoffs And Future Improvements

- Replace mocked search with a real Places provider.
- Add a live calling or reservation integration behind the existing tool boundary.
- Expand date/time normalization for broader natural language coverage.
- Add focused tests around parsing, restaurant resolution, and tool execution.
