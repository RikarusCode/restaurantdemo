# Demo Test Cases

Use this file as the practice script before showing the project to an evaluator. The goal is to demonstrate the exact assignment loop:

```text
user request -> task understood -> tool call -> restaurant result -> short summary
```

The strongest demo path is the UI at `http://localhost:8000`, because the streamed trace makes the agent behavior easy to inspect.

## How To Run The Demo

From the repository root:

```powershell
py -m uvicorn backend.app.main:app --reload
```

Open:

```text
http://localhost:8000
```

For the best assessment demo, set `K2_API_KEY` in `.env`. Without a key, the deterministic fallback still supports the examples below.

## Recommended Live Demo Script

1. Enable **Auto-detect** and run `check if the sushi place is avaliable at 6`.
2. Point out that the app resolves "the sushi place" to Kazu Sushi, fixes the misspelling, assumes 2 guests tonight, and checks 6 PM.
3. Start with **Kazu Sushi** selected and run the table availability example.
4. Point out the visible trace:
   - Restaurant on File
   - Request Understood
   - Calling Restaurant - Table Availability
   - Restaurant Response
   - Final Answer
5. Run an open-status check with **Luna Trattoria** selected.
6. Enable search mode and run the Kazu Sushi search example.
7. Run the clarification example to show reliability.
8. Run the unsupported booking example to show the scope boundary.

## Curated UI Test Cases

| ID | What it proves | Restaurant mode | Request | Expected behavior |
| --- | --- | --- | --- | --- |
| TC-01 | Natural product-style request with typo, alias, and bare time | Search mode enabled | `check if the sushi place is avaliable at 6` | Resolves "sushi place" to Kazu Sushi, treats "avaliable" as availability, assumes 2 guests tonight, interprets 6 as 6 PM, and returns availability. |
| TC-02 | Core assignment path: availability tool call | Kazu Sushi selected | `Call this restaurant and ask if they have a table for 2 tonight at 7 PM.` | Understands `check_table_availability`, calls availability tool, returns no 7 PM table but 7:30 PM available. |
| TC-03 | Happy path: availability is available | Luna Trattoria selected | `Call and ask whether they have a table for 2 tonight at 7 PM.` | Calls availability tool and returns a table is available at 7 PM. |
| TC-04 | Open-status tool call | Luna Trattoria selected | `Is this restaurant open right now?` | Calls hours tool and returns current open/closed status with relevant hours. |
| TC-05 | Specific future open-status check | Kazu Sushi selected | `Is this restaurant open tomorrow at noon?` | Calls hours tool with `tomorrow` and `12:00 PM`, then summarizes status. |
| TC-06 | Search feature as a real capability | Search mode enabled | `Is Kazu Sushi open tomorrow at noon?` | Calls `search_restaurant`, resolves Kazu Sushi, then calls hours tool. |
| TC-07 | Search plus availability | Search mode enabled | `Can you call Luna Trattoria and ask if they have a table for 2 tomorrow at 7 PM?` | Searches Luna Trattoria, calls availability tool, returns available at 7 PM. |
| TC-08 | Clarification instead of fake execution | Harbor Garden selected | `Do they have room for 4?` | Understands availability request but asks for date/time without calling the restaurant tool. |
| TC-09 | Unsupported scope boundary | Kazu Sushi selected | `Can you book a table for me?` | Does not call a restaurant tool; returns that the demo supports availability and open-status checks only. |
| TC-10 | Unknown restaurant search failure | Search mode enabled | `Is Blue Comet Bistro open right now?` | Calls search, cannot resolve restaurant, asks for a valid restaurant rather than inventing one. |

## API Smoke Tests

These are useful if you want to verify behavior without the browser.

### TC-01: Table Availability

```powershell
Invoke-WebRequest -UseBasicParsing `
  -Method POST `
  -Uri http://127.0.0.1:8000/agent/run `
  -ContentType "application/json" `
  -Body '{"restaurant_name":"Kazu Sushi","restaurant_phone":"415-555-0142","user_request":"Call this restaurant and ask if they have a table for 2 tonight at 7 PM."}'
```

Expected trace includes:

```text
Restaurant on File
Request Understood
Calling Restaurant - Table Availability
Restaurant Response
They do not have a table for 2 at 7:00 PM, but 7:30 PM is available.
```

### TC-05: Search Then Hours Check

```powershell
Invoke-WebRequest -UseBasicParsing `
  -Method POST `
  -Uri http://127.0.0.1:8000/agent/run `
  -ContentType "application/json" `
  -Body '{"user_request":"Is Kazu Sushi open tomorrow at noon?"}'
```

Expected trace includes:

```text
Searching for Restaurant
Restaurant Found
Calling Restaurant - Hours Check
Final Answer
```

### TC-07: Clarification

```powershell
Invoke-WebRequest -UseBasicParsing `
  -Method POST `
  -Uri http://127.0.0.1:8000/agent/run `
  -ContentType "application/json" `
  -Body '{"restaurant_name":"Harbor Garden","restaurant_phone":"415-555-0119","user_request":"Do they have room for 4?"}'
```

Expected final answer:

```text
Please specify the date and time you would like me to check.
```

## What To Say During The Demo

Use this framing:

```text
The assignment asks for a simple restaurant-calling agent, so I kept the main flow intentionally small. The restaurant details are already on file, the agent extracts the task, invokes one mocked call tool, and returns a short answer. I also implemented the stretch goal as search mode, where the agent first resolves the restaurant and then runs the same tool flow. The trace is streamed so an evaluator can see every step instead of guessing what the agent did.
```

## Demo Notes

- The mocked call is a deliberate design choice, not a missing integration.
- The UI is the best demo surface because it shows agent transparency.
- The fallback parser makes the demo resilient if an API key is unavailable.
- The unsupported and clarification cases are important because they show the system does not overclaim or fake tool calls.
