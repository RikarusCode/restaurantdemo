# TableCall

TableCall is a small full-stack demo for restaurant discovery, deterministic availability, open-hours checks, and an optional phone reservation handoff powered by [Retell AI](https://retellai.com). A user types one natural-language request; the backend runs a short agent loop, executes structured tools against a local restaurant directory, streams a visible trace, and returns an answer plus explicit UI state for the reservation funnel.

## What You Can Do

- Ask for a table with everyday language, including "make a reservation" or "book a table", when party size, date, and time are known.
- Ask whether a place is open now or at a specific time.
- Auto-detect the restaurant from cuisine, neighborhood, nicknames like "the sushi place", or proper names.
- Render a normal availability answer, a reservation button, an optional reservation modal, a calling state, and a final success or failure answer after the call.
- Place a real outbound reservation attempt through Retell when credentials are configured.

The restaurant data is deterministic so demos stay reproducible. The Retell call is real. During development, route calls to your own phone with `TABLECALL_DIAL_OVERRIDE` instead of dialing the fixture restaurant numbers.

## How It Works

```text
Browser -> POST /agent/run
  -> LLM planner or deterministic parser
  -> search_restaurant when no restaurant is selected
  -> call_restaurant_check_availability or call_restaurant_check_hours
  -> summary { text, ui }

Browser -> POST /reservation/call after modal confirmation
  -> Retell outbound call
  -> poll until terminal status
  -> { confirmed, call_state, message, call_id, call_status }
```

The reservation UI state is intentionally explicit:

```json
{
  "availability": {
    "status": "available",
    "available": true,
    "alternative_time": null,
    "party_size": 2,
    "requested_time": "6:00 PM"
  },
  "reservation_button": {
    "visible": true,
    "enabled": true,
    "label": "Place reservation?",
    "disabled_reason": null
  },
  "reservation_modal": {
    "auto_open": true,
    "draft": {
      "restaurant_name": "Kazu Sushi",
      "restaurant_phone": "+14155550142",
      "location": "214 Linden Street, San Francisco, CA",
      "date_heading": "Tonight - Monday, Apr 13, 2026",
      "requested_date": "tonight",
      "time": "6:00 PM",
      "party_size": 2,
      "availability_status": "available"
    }
  }
}
```

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

Configure an LLM provider if you want LLM planning and semantic restaurant search:

```text
LAVA_API_BASE_URL=https://api.lava.so/v1
LAVA_SECRET_KEY=your-key-here
LAVA_MODEL=gpt-4.1-mini
```

With no LLM key, the deterministic parser still handles the core examples.

## Retell Setup

Put these values in `.env`:

```text
RETELL_API_KEY=your-retell-api-key
RETELL_FROM_NUMBER=+1your-retell-owned-number
RETELL_AGENT_ID=optional-agent-id
TABLECALL_DIAL_OVERRIDE=+1your-personal-test-phone
```

Where your phone number goes:

- `RETELL_FROM_NUMBER` is the caller ID you own in Retell. Copy this from the Retell phone-number page. It must be E.164, for example `+14157774444`.
- `TABLECALL_DIAL_OVERRIDE` is your personal test handset. Set this while demoing so every restaurant call goes to you. This is the safest place for your real phone number.
- Restaurant directory numbers live in [backend/app/mock_data.py](backend/app/mock_data.py). Leave those as fixture numbers unless you intentionally want to change the demo directory.

What to do on the Retell website:

1. Create or choose a phone number in Retell. Copy it into `RETELL_FROM_NUMBER`.
2. Create a voice agent that can call a restaurant host and ask for a reservation using the dynamic variables below.
3. Copy the Retell API key into `RETELL_API_KEY`.
4. Optional: copy the agent ID into `RETELL_AGENT_ID` if you want this app to force one specific agent.
5. Add a boolean post-call analysis field named `reservation_confirmed`. TableCall uses it as the clean success/failure signal.

Dynamic variables sent to Retell:

```text
restaurant_name
party_size
reservation_time
reservation_date
requested_date_token
location
notes
```

If `reservation_confirmed` is missing, TableCall falls back to Retell's `call_successful` and voicemail flags. That works for a demo, but the explicit boolean is much clearer.

## Run

```powershell
py -m uvicorn backend.app.main:app --reload
```

Open:

```text
http://localhost:8000
```

## Examples And Demos

Use examples in three layers:

- Frontend example buttons: best for live demos because they show the normal answer, trace, reservation button, modal, calling state, and final replacement answer.
- [demo/DEMO_TEST_CASES.md](demo/DEMO_TEST_CASES.md): best for a manual checklist before recording or presenting.
- [demo/demo_cases.json](demo/demo_cases.json): best as a stable source for future automated smoke tests.

Recommended live demo flow:

1. Auto-detect: `Can you check whether the sushi place has a table for 2 tonight at 6?`
2. Reservation intent: `Make a reservation for 2 tonight at 6 at the sushi place.`
3. Unavailable but callable: `Can you ask this restaurant about a table for 2 tonight at 7 PM?`
4. Clarification: `Can you check whether this restaurant has room for 4?`
5. Unsupported scope: `Can you order delivery from this restaurant?`

## Project Map

| Module | Role |
| --- | --- |
| `backend/app/main.py` | FastAPI app, static frontend, `/agent/run`, `/reservation/call`, `/api/restaurants` |
| `backend/app/agent.py` | Planner loop, guardrails, summaries |
| `backend/app/tools.py` | Tool definitions and deterministic execution |
| `backend/app/mock_data.py` | Restaurants, hours, availability grid |
| `backend/app/reservation_ui.py` | Availability, reservation button, and modal UI state |
| `backend/app/retell_service.py` | Retell dial, polling, and call outcome interpretation |
| `frontend/app.js` | Browser rendering, modal behavior, call lifecycle rendering |

## Product Boundaries

Availability comes from local fixtures, not live reservation systems. The reservation path places a real phone call through your Retell account. Compliance, consent, recording policy, and production guardrails are your responsibility.
