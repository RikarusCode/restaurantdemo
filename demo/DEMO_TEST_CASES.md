# Example Use Cases

Use these cases to validate TableCall's supported product behavior. The core loop is:

```text
user request -> LLM planner -> selected tool -> restaurant data -> concise answer
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

1. Enable Auto-detect and run `Can you check whether the sushi place has a table for 2 tonight at 6?`.
2. Confirm the trace shows LLM planning, restaurant search, agent loop continuation, availability tool execution, and final answer.
3. Select Kazu Sushi and run `Can you ask this restaurant about a table for 2 tonight at 7 PM?`
4. Select Luna Trattoria and run `Can you check whether this restaurant is open right now?`
5. Enable Auto-detect and run `Can you check whether the taco place has room for 6 around 6?`
6. Try `Can you book a table for me at this restaurant?` and confirm the product stays inside its supported scope.

## Curated Cases

| ID | Capability | Restaurant mode | Request | Expected behavior |
| --- | --- | --- | --- | --- |
| TC-01 | Alias and natural time handling | Auto-detect | `Can you check whether the sushi place has a table for 2 tonight at 6?` | Resolves Kazu Sushi, treats 6 as 6 PM, and returns availability. |
| TC-02 | Core selected-restaurant availability | Kazu Sushi selected | `Can you ask this restaurant about a table for 2 tonight at 7 PM?` | Calls the availability tool and returns a nearby available time if 7 PM is booked. |
| TC-03 | Available table path | Luna Trattoria selected | `Can you check whether this restaurant has a table for 2 tonight at 7 PM?` | Calls availability and returns a table at 7 PM. |
| TC-04 | Current open-status path | Luna Trattoria selected | `Can you check whether this restaurant is open right now?` | Calls the hours tool and returns current open/closed status. |
| TC-05 | Future open-status path | Kazu Sushi selected | `Can you check whether this restaurant is open tomorrow at noon?` | Checks tomorrow at 12 PM. |
| TC-06 | Search plus hours | Auto-detect | `Can you check whether Kazu Sushi is open tomorrow at noon?` | Searches Kazu Sushi, then checks hours. |
| TC-07 | Search plus availability | Auto-detect | `Can you check whether Luna Trattoria has a table for 2 tomorrow at 7 PM?` | Searches Luna Trattoria, then checks availability. |
| TC-08 | Fourth restaurant diversity | Auto-detect | `Can you check whether the taco place has room for 6 around 6?` | Resolves Nopalito Verde and checks a party of 6 at 6 PM. |
| TC-09 | Clarification | Harbor Garden selected | `Can you check whether this restaurant has room for 4?` | Asks for the missing time without calling availability. |
| TC-10 | Unsupported scope | Kazu Sushi selected | `Can you book a table for me at this restaurant?` | Explains that the product supports availability and open-status checks only. |
| TC-11 | Unknown restaurant | Auto-detect | `Can you check whether Blue Comet Bistro is open right now?` | Does not invent a restaurant; asks which restaurant to call. |

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
