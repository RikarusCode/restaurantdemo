# TableCall Restaurant Agent

TableCall is a local web app for checking restaurant availability and hours through an agentic call flow. A user asks in natural language, the LLM chooses the appropriate tool, the backend executes a deterministic restaurant-call action against local restaurant data, and the app returns a concise answer with an integrated trace of the loop.

The main product path assumes a restaurant is already selected by the system. Auto-detect mode extends that flow by resolving restaurants from phrases like "the sushi place", "the taco place", or "the waterfront place" before checking availability or hours.

## Capabilities

- Check table availability by party size, date, and time.
- Check whether a restaurant is open now or at a specified time.
- Resolve restaurants by name, cuisine, neighborhood, style, or alias.
- Show the LLM planning step, selected tool, tool execution, and tool result.
- Use a deterministic fallback parser if an LLM provider is unavailable.
- Serve the polished frontend and FastAPI backend from one local command.

## Agent Flow

```text
User request
  -> LLM planning
  -> LLM-selected tool
  -> local restaurant data/tool execution
  -> concise answer
  -> visible trace for transparency
```

For provider compatibility and reliability, the LLM is responsible for planning and tool selection. The backend owns tool execution and final deterministic formatting, which keeps the product snappy and prevents the model from inventing restaurant facts.

## Example Use Cases

| Request | Expected behavior |
| --- | --- |
| `Can you check whether the sushi place has a table for 2 tonight at 6?` | Resolves Kazu Sushi by alias and checks availability at 6:00 PM. |
| `Can you ask this restaurant about a table for 2 tonight at 7 PM?` | Uses the selected restaurant and returns the nearest available time if 7 PM is booked. |
| `Can you check whether the taco place has room for 6 around 6?` | Resolves Nopalito Verde and checks availability for 6 guests at 6:00 PM. |
| `Can you check whether this restaurant is open right now?` | Calls the hours tool for the selected restaurant. |
| `Can you check whether Kazu Sushi is open tomorrow at noon?` | Resolves Kazu Sushi and checks open status at tomorrow noon. |
| `Can you check whether this restaurant has room for 4?` | Recognizes an availability request but asks for the missing time. |
| `Can you book a table for me at this restaurant?` | Explains that booking is outside the supported product scope. |

## Restaurant Data

The local directory contains four restaurants with diverse operating data:

| Restaurant | Type | Search aliases |
| --- | --- | --- |
| Kazu Sushi | Japanese sushi bar | `sushi place`, `japanese place`, `sushi spot` |
| Luna Trattoria | Italian trattoria | `italian place`, `pasta place`, `trattoria` |
| Harbor Garden | Waterfront seafood | `seafood place`, `fish place`, `waterfront place` |
| Nopalito Verde | Plant-forward Mexican cantina | `taco place`, `mexican place`, `vegetarian place` |

Each restaurant includes:

- weekly hours
- capacity and maximum party size
- reservation policy
- lunch, dinner, and tomorrow availability slots
- party-size constraints
- unavailable slots and alternative-time behavior

## Architecture

| File | Purpose |
| --- | --- |
| `backend/app/main.py` | FastAPI app, static frontend serving, streamed `/agent/run` endpoint |
| `backend/app/agent.py` | LLM planner, local fallback parser, visible agent-loop orchestration |
| `backend/app/tools.py` | OpenAI-compatible tool definitions and deterministic tool execution |
| `backend/app/mock_data.py` | Restaurant directory, hours, availability, search aliases, and availability helpers |
| `backend/app/restaurant_search.py` | Restaurant search and public restaurant serialization |
| `backend/app/schemas.py` | Pydantic API and trace models |
| `backend/app/config.py` | Provider configuration for Lava, K2, and OpenAI-compatible APIs |
| `frontend/` | Product UI with request entry, answer card, trace panel, and data table |

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

Configure one LLM provider in `.env`. Lava is preferred when present:

```text
LAVA_API_BASE_URL=https://api.lava.so/v1
LAVA_SECRET_KEY=your-key-here
LAVA_MODEL=gpt-4.1-mini
```

K2 and standard OpenAI-compatible credentials are also supported:

```text
K2_BASE_URL=https://api.k2think.ai/v1
K2_API_KEY=your-key-here
K2_MODEL=MBZUAI-IFM/K2-Think-v2

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
```

If no provider key is configured, TableCall still runs with the deterministic local parser.

## Run

From the repository root:

```powershell
py -m uvicorn backend.app.main:app --reload
```

Open:

```text
http://localhost:8000
```

## Product Boundaries

TableCall supports availability and open-status checks. It does not place real reservations, call live phone numbers, scrape restaurant websites, or process menu/order requests. The restaurant-call action is intentionally local and deterministic so the agent loop can be evaluated reliably and extended later with a real calling or reservation provider.

## Future Improvements

- Add automated tests for the LLM planner contract, fallback parser, and availability edge cases.
- Replace the local restaurant directory with a real Places provider behind the existing search boundary.
- Add a real telephony or reservation integration behind the existing tool executor.
- Add observability around provider latency, fallback rate, and tool outcomes.
