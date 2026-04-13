# Project Spec

Build a small end-to-end demo of an LLM restaurant agent.

## Goal
User gives a restaurant-related request. The system:
1. understands the request
2. extracts task details
3. invokes a tool/action
4. gets a result
5. returns a short summary

## Supported requests
- check table availability
- check whether the restaurant is open

## Stretch goal
- search restaurant information on the fly if restaurant name and phone are not already given

## Constraints
- keep the project small and demoable
- prioritize reliability and clarity over production complexity
- no auth, database, Docker, background jobs, or unnecessary abstractions
- expose intermediate steps in the demo:
  - parsed intent
  - extracted slots
  - selected tool
  - tool result
  - final summary

## Preferred stack
- FastAPI backend
- simple frontend with plain HTML/CSS/JS
- use OpenAI API for structured extraction
- use mocked restaurant call behavior unless explicitly swapped for live telephony later