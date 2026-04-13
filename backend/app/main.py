"""FastAPI entrypoint that orchestrates restaurant-agent requests."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agent import build_summary, parse_user_request
from .restaurant_search import resolve_restaurant_info
from .schemas import AgentRequest, AgentResponse
from .tools import build_tool_invocation, execute_tool


app = FastAPI(title="Restaurant Agent Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/agent/run", response_model=AgentResponse)
def run_agent(request: AgentRequest) -> AgentResponse:
    """Resolve restaurant info, parse intent, optionally invoke a tool, and respond."""

    restaurant_name, restaurant_phone, _metadata = resolve_restaurant_info(
        request.user_request,
        request.restaurant_name,
        request.restaurant_phone,
    )
    parsed_intent = parse_user_request(request)

    if parsed_intent.clarification_needed or parsed_intent.intent == "unsupported":
        return AgentResponse(
            restaurant_name=restaurant_name,
            restaurant_phone=restaurant_phone,
            parsed_intent=parsed_intent,
            tool_invocation=None,
            tool_result=None,
            summary=build_summary(parsed_intent, None),
        )

    tool_invocation = build_tool_invocation(parsed_intent, restaurant_name, restaurant_phone)
    tool_result = execute_tool(parsed_intent, restaurant_name, restaurant_phone)

    return AgentResponse(
        restaurant_name=restaurant_name,
        restaurant_phone=restaurant_phone,
        parsed_intent=parsed_intent,
        tool_invocation=tool_invocation,
        tool_result=tool_result,
        summary=build_summary(parsed_intent, tool_result),
    )
