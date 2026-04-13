# TableCall

TableCall is a small full-stack demo for restaurant discovery, deterministic availability, open-hours checks, and an optional **phone reservation handoff** powered by [Retell AI](https://retellai.com). You type a single natural-language request; the backend runs a short agent loop (LLM planning when configured, otherwise a local parser), executes structured tools against a local restaurant directory, streams a transparent trace to the browser, and returns **both** a spoken-style answer and **explicit UI state** for the reservation funnel.

## What you can do

- **Ask for a table** using everyday language, including “make a reservation” or “book a table,” with party size, date, and time.
- **Ask whether a place is open** now or at a specific time.
- **Auto-detect the restaurant** from cuisine, neighborhood, nicknames (“the sushi place”), or proper names.
- When availability is evaluated, the UI may offer **Place reservation?** or **Attempt reservation anyway** (for slots the mock data marks as full or constrained). Opening the modal shows restaurant, location, day/date, time, and party size prefilled from the request.
- **Attempt reservation** starts a **real outbound call** through Retell to the restaurant’s directory number, or to a **test destination** you configure, while injecting reservation details as Retell dynamic variables for your voice agent.

The mock restaurant directory is intentionally deterministic so traces stay reproducible. The telephony path is real: you provide Retell credentials, a Retell-owned `from` number, and (recommended) `TABLECALL_DIAL_OVERRIDE` during development so every restaurant routes to a handset you control.

## How it works

```text
Browser  -> POST /agent/run (NDJSON stream of pipeline steps)
       LLM or local parser selects tools
       -> search_restaurant (when no restaurant is pinned)
       -> call_restaurant_check_availability / call_restaurant_check_hours
       -> summary step includes { text, ui } for availability
  -> POST /reservation/call (JSON) when the user confirms the modal
       Retell service places outbound call, polls until terminal status
       -> response { confirmed, message, call_id, call_status }
```

Backend highlights:

| Module | Role |
| --- | --- |
| `backend/app/main.py` | FastAPI app, static frontend, `/agent/run`, `/reservation/call`, `/api/restaurants` |
| `backend/app/agent.py` | Planner loop, guardrails, summaries |
| `backend/app/tools.py` | Tool definitions and deterministic execution |
| `backend/app/mock_data.py` | Restaurants, hours, availability grid |
| `backend/app/reservation_ui.py` | Reservation funnel UI payload attached to availability summaries |
| `backend/app/retell_service.py` | Isolated Retell client: dial, poll, interpret post-call analysis |
| `backend/app/phone_format.py` | E.164 normalization for telephony |

## Restaurant directory

Four demo venues ship with rich hours, capacity rules, and availability slots. Phone numbers are stored in **E.164** (for example `+14155550142`). For live testing, set `TABLECALL_DIAL_OVERRIDE` so outbound calls always reach your own number while the UI still shows the fictional directory entry.

| Restaurant | Style | Example aliases |
| --- | --- | --- |
| Kazu Sushi | Japanese sushi bar | sushi place, japanese place |
| Luna Trattoria | Italian trattoria | italian place, pasta place |
| Harbor Garden | Waterfront seafood | seafood place, waterfront place |
| Nopalito Verde | Plant-forward Mexican | taco place, mexican place |

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

Configure an LLM provider (optional but recommended for semantic restaurant search):

```text
LAVA_API_BASE_URL=https://api.lava.so/v1
LAVA_SECRET_KEY=your-key-here
LAVA_MODEL=gpt-4.1-mini
```

Other providers supported in `.env.example` include K2 Think and OpenAI-compatible APIs. With no key, the deterministic parser still resolves many requests.

### Retell AI

Add to `.env`:

```text
RETELL_API_KEY=...
RETELL_FROM_NUMBER=+1your-retell-number
# Optional
RETELL_AGENT_ID=...
TABLECALL_DIAL_OVERRIDE=+1your-test-handset
```

Point your Retell agent’s prompt or knowledge base at the dynamic variables TableCall sends (`restaurant_name`, `party_size`, `reservation_time`, `reservation_date`, `location`, `notes`, `requested_date_token`). For reliable **confirmed / not confirmed** signaling in the API response, add a **boolean post-call analysis field** named `reservation_confirmed` on the agent. If that field is absent, TableCall falls back to Retell’s `call_successful` flag (and voicemail detection) so the demo still returns an outcome.

## Run

```powershell
py -m uvicorn backend.app.main:app --reload
```

Open `http://localhost:8000`.

## Product boundaries

TableCall is a demo: availability comes from local fixtures, not live POS systems. The reservation path places a real phone call through your Retell account; compliance, recording consent, and production guardrails are your responsibility. Unsupported example intents in the UI include off-scope requests such as delivery ordering.

## Future ideas

- Automated tests for the planner contract, parser, and availability edge cases.
- Swap the directory for a real Places or reservations provider behind the same tool boundary.
- Webhook-driven Retell completion instead of polling for very long calls.
