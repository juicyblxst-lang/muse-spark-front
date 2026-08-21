from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.services.openclaw_agent import AgentResponse, MuseTool, OpenClawRuntime
from app.services.retrieval import RetrievedContext


class OpenClawHttpRuntime(OpenClawRuntime):
    """Concrete OpenClaw Gateway runtime using its OpenAI-compatible HTTP API.

    The Gateway endpoint must be explicitly enabled and protected by its own
    authentication. Muse sends bounded retrieved evidence and tool schemas;
    it never sends database handles, Supabase credentials, or Sibyl clients.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (base_url or settings.openclaw_base_url).rstrip("/")
        secret = settings.openclaw_api_key.get_secret_value() if settings.openclaw_api_key else ""
        self.api_key = api_key or secret
        self.model = model or settings.llm_model or "openclaw/default"
        self.timeout = timeout

    def _endpoint(self) -> str:
        if not self.base_url:
            raise HTTPException(status_code=503, detail="OpenClaw runtime is not configured.")
        return f"{self.base_url}/v1/chat/completions"

    @staticmethod
    def _context_message(context: RetrievedContext) -> str:
        evidence = {
            "query": context.query,
            "memories": context.memories,
            "entities": context.entities,
            "relationships": context.relationships,
            "timeline": context.timeline,
            "source_references": context.source_references,
            "provenance": context.provenance,
        }
        return (
            "Use only the evidence below to answer the user's query. "
            "Do not invent facts, memories, sources, or history. "
            "If the evidence is insufficient, say so.\n\n"
            f"EVIDENCE:\n{json.dumps(evidence, ensure_ascii=False, default=str)}"
        )

    @staticmethod
    def _tool_schema(tool: MuseTool) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True,
                },
            },
        }

    def run(self, *, query: str, context: RetrievedContext, tools: tuple[MuseTool, ...]) -> AgentResponse:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Muse. Answer from retrieved user-owned evidence only. "
                        "Preserve provenance and never fabricate personal history."
                    ),
                },
                {"role": "user", "content": self._context_message(context)},
                {"role": "user", "content": query},
            ],
        }
        if tools:
            payload["tools"] = [self._tool_schema(tool) for tool in tools]
            payload["tool_choice"] = "auto"

        try:
            response = httpx.post(
                self._endpoint(),
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="Unable to reach OpenClaw Gateway.") from exc

        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"OpenClaw Gateway returned HTTP {response.status_code}.",
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="OpenClaw returned invalid JSON.") from exc

        choices = data.get("choices") or []
        if not choices or not isinstance(choices[0], dict):
            raise HTTPException(status_code=502, detail="OpenClaw returned no completion choice.")

        message = choices[0].get("message") or {}
        answer = message.get("content") or ""
        raw_tool_calls = message.get("tool_calls") or []
        tool_calls = tuple(
            call for call in raw_tool_calls if isinstance(call, dict)
        )
        return AgentResponse(answer=str(answer), tool_calls=tool_calls)
