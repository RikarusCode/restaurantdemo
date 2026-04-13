# Restaurant Agent Demo

A small end-to-end demo for the assignment: the user gives a restaurant-related request, an LLM-style agent understands the task, triggers a restaurant-call tool, receives a result, and returns a short summary.

The main path assumes restaurant name and phone are already available, as requested. The search feature is also implemented as a first-class mode: when no restaurant is selected, the agent uses a restaurant lookup tool before making the mocked call.

## What This Demonstrates

- Intent understanding for two supported tasks:
  - table availability
  - open-status / hours checks
- Tool calling through a mocked restaurant-call layer.
- A streamed trace that makes each agent step visible in the UI.
- Deterministic fallback behavior when no OpenAI API key is configured.
- Fully implemented restaurant search mode using the local demo directory.

## Demo Flow

```text
User request
  -> restaurant on file, or search_restaurant tool
  -> request understood step
  -> restaurant-call tool invocation
  -> mocked restaurant result
  -> final one-sentence answer
```

The mocked call layer is intentional. It keeps the assessment focused on the agent loop, tool boundary, reliability, and user experience without adding telephony setup, scraping, databases, queues, or other production infrastructure.

## Supported Requests

| Request type | Example |
| --- | --- |
| Table availability | "Call this restaurant and ask if they have a table for 2 tonight at 7 PM." |
| Open status | "Is this restaurant open right now?" |
| Search plus open status | "Is Kazu Sushi open tomorrow at noon?" |
| Clarification | "Do they have room for 4?" |
| Unsupported | "Can you book a table for me?" |

## Architecture

| File | Purpose |
| --- | --- |
| `backend/app/main.py` | FastAPI app, `/agent/run` streaming endpoint, static frontend serving |
| `backend/app/agent.py` | Agent orchestration, OpenAI tool-calling path, deterministic fallback path |
| `backend/app/tools.py` | Tool definitions and mocked tool execution |
| `backend/app/restaurant_search.py` | Restaurant lookup helper for the search feature |
| `backend/app/mock_data.py` | Three demo restaurants with hours and availability slots |
| `backend/app/schemas.py` | API request and streamed trace models |
| `backend/app/config.py` | Minimal environment loading |
| `frontend/` | Plain HTML, CSS, and JavaScript UI |

## Why This Matches The Assignment

The assignment asks for a simple LLM agent that calls a restaurant. This project keeps the scope tight:

- No auth, database, Docker, migrations, queues, or framework-heavy frontend.
- Restaurant details are selected by the system for the main demo path.
- The agent exposes intermediate steps so an evaluator can see the request understanding and tool call.
- The mocked call behaves like the result of a restaurant phone call.
- Search is included as a real feature, but isolated behind a clean lookup tool.

## Setup

From the repository root:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
cd ..
copy .env.example .env
```

Add K2 credentials to `.env` for the LLM tool-calling path:

```text
K2_BASE_URL=https://api.k2think.ai/v1
K2_API_KEY=your-key-here
K2_MODEL=MBZUAI-IFM/K2-Think-v2
```

The app also supports `OPENAI_API_KEY` and `OPENAI_MODEL` as a fallback. If neither `K2_API_KEY` nor `OPENAI_API_KEY` is set, the app still runs with a deterministic fallback parser so the demo remains easy to present.

## Run

From the repository root:

```powershell
py -m uvicorn backend.app.main:app --reload
```

Open:

```text
http://localhost:8000
```

The frontend is served by FastAPI, so there is no separate frontend build step.

## Demo Script

1. Start with Kazu Sushi selected.
2. Click "Table for 2 tonight at 7 PM."
3. Point out the trace: restaurant on file, request understood, tool call, restaurant response, final answer.
4. Click "Is this restaurant open right now?"
5. Click "Is Kazu Sushi open tomorrow at noon?" to show search mode.
6. Click "Do they have room for 4?" to show the clarification path.
7. Try "Can you book a table for me?" to show unsupported handling.

## Mock Restaurants

| Name | Phone | Cuisine |
| --- | --- | --- |
| Kazu Sushi | 415-555-0142 | Japanese |
| Luna Trattoria | 415-555-0188 | Italian |
| Harbor Garden | 415-555-0119 | Seafood |

## Tradeoffs And Future Improvements

- The restaurant call is mocked to keep the demo reliable and self-contained.
- Search uses the local restaurant directory; a production version could swap in Google Places or another provider behind `restaurant_search.py`.
- Time parsing is intentionally lightweight and tuned for demo phrases.
- A production version would add tests, observability, rate limiting, secrets management, and a real telephony or reservation integration.
