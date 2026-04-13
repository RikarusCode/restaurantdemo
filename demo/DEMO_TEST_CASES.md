# Example Use Cases

Use these cases to validate TableCall's supported product behavior. The core loop is:

```text
user request -> planner/parser -> selected tool -> restaurant data -> concise answer -> optional reservation UI
```

## Run Locally

From the repository root:

```powershell
py -m uvicorn backend.app.main:app --reload
```

Open:

```text
http://localhost:8000
```

## Recommended Manual Checks

1. Enable Auto-detect and run `Can you check whether the sushi place has a table for 2 tonight at 6?`
2. Confirm the answer is a normal availability response and the reservation button appears.
3. Run `Make a reservation for 2 tonight at 6 at the sushi place.` and confirm the modal auto-opens.
4. Submit the modal with Retell unconfigured and confirm the answer is replaced with a clear failure message.
5. Configure Retell with `TABLECALL_DIAL_OVERRIDE` pointed at your phone, submit again, and confirm the UI shows `Calling the restaurant...` until the final call result.
6. Select Kazu Sushi and run `Can you ask this restaurant about a table for 2 tonight at 7 PM?` Confirm the "Attempt reservation anyway" button appears.
7. Select Harbor Garden and run `Can you check whether this restaurant has room for 4?` Confirm it asks for a time without calling availability.
8. Select Kazu Sushi and run `Can you order delivery from this restaurant?` Confirm the unsupported-scope message.

## Curated Cases

| ID | Capability | Restaurant mode | Request | Expected behavior |
| --- | --- | --- | --- | --- |
| TC-01 | Alias and natural time handling | Auto-detect | `Can you check whether the sushi place has a table for 2 tonight at 6?` | Resolves Kazu Sushi, treats 6 as 6 PM, returns availability, and shows `Place reservation?`. |
| TC-02 | Unavailable table with alternative | Kazu Sushi selected | `Can you ask this restaurant about a table for 2 tonight at 7 PM?` | Calls availability and offers `Attempt reservation anyway`. |
| TC-03 | Available table path | Luna Trattoria selected | `Can you check whether this restaurant has a table for 2 tonight at 7 PM?` | Calls availability and returns a table at 7 PM. |
| TC-04 | Reservation intent | Auto-detect | `Make a reservation for 2 tonight at 6 at the sushi place.` | Resolves Kazu Sushi, checks availability, and auto-opens the reservation modal. |
| TC-05 | Current open-status path | Luna Trattoria selected | `Can you check whether this restaurant is open right now?` | Calls the hours tool and returns current open/closed status. |
| TC-06 | Future open-status path | Kazu Sushi selected | `Can you check whether this restaurant is open tomorrow at noon?` | Checks tomorrow at 12 PM. |
| TC-07 | Search plus hours | Auto-detect | `Can you check whether Kazu Sushi is open tomorrow at noon?` | Searches Kazu Sushi, then checks hours. |
| TC-08 | Fourth restaurant diversity | Auto-detect | `Can you check whether the taco place has room for 6 around 6?` | Resolves Nopalito Verde and checks a party of 6 at 6 PM. |
| TC-09 | Clarification | Harbor Garden selected | `Can you check whether this restaurant has room for 4?` | Asks for the missing time without calling availability. |
| TC-10 | Unsupported scope | Kazu Sushi selected | `Can you order delivery from this restaurant?` | Explains that the product supports availability and open-status checks only. |
| TC-11 | Unknown restaurant | Auto-detect | `Can you check whether Blue Comet Bistro is open right now?` | Does not invent a restaurant; asks which restaurant to call. |
| TC-12 | Party too large | Kazu Sushi selected | `Can you check whether this restaurant has a table for 9 tonight at 6?` | Returns the max-party message and renders a disabled reservation button. |

## API Smoke Check

```powershell
Invoke-WebRequest -UseBasicParsing `
  -Method POST `
  -Uri http://127.0.0.1:8000/agent/run `
  -ContentType "application/json" `
  -Body '{"user_request":"Can you check whether the sushi place has a table for 2 tonight at 6?"}'
```

Expected trace includes:

```text
LLM Planning
LLM Selected Tool
Resolving Restaurant
Agent Loop Continues
Calling Restaurant - Table Availability
Final Answer
```
