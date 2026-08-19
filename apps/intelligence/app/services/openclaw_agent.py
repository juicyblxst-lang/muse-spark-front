from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.services.retrieval import RetrievedContext, UserQuery


@dataclass(frozen=True)
class MuseTool:
    name: str
    description: str
    handler: Any


@dataclass(frozen=True)
class AgentRequest:
    user_query: UserQuery
    context: RetrievedContext
    tools: tuple[MuseTool, ...] = ()


@dataclass(frozen=True)
class AgentResponse:
    answer: str
    tool_calls: tuple[dict[str, Any], ...] = ()


class OpenClawRuntime(Protocol):
    def run(self, *, query: str, context: RetrievedContext, tools: tuple[MuseTool, ...]) -> AgentResponse: ...


class OpenClawAgent:
    """Muse's reasoning boundary around an OpenClaw-compatible runtime.

    OpenClaw receives retrieved evidence and explicitly exposed Muse tools only.
    It is never given database, filesystem, or Sibyl credentials/handles.
    """

    def __init__(self, runtime: OpenClawRuntime, tools: tuple[MuseTool, ...] = ()) -> None:
        self._runtime = runtime
        self._tools = tools

    def run(self, request: AgentRequest) -> AgentResponse:
        if request.user_query.user_id != request.context_user_id if hasattr(request, "context_user_id") else False:
            raise ValueError("query and context identity must match")
        return self._runtime.run(
            query=request.user_query.query,
            context=request.context,
            tools=request.tools or self._tools,
        )


def build_agent_request(user_query: UserQuery, context: RetrievedContext, tools: tuple[MuseTool, ...] = ()) -> AgentRequest:
    return AgentRequest(user_query=user_query, context=context, tools=tools)
