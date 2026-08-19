from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.memory.sibyl_client import MemoryService


class UserQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str = Field(min_length=1)
    query: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=100)


class RetrievedContext(BaseModel):
    """Bounded evidence package. This layer never generates an answer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    query: str
    memories: list[Any] = Field(default_factory=list)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    source_references: list[dict[str, Any]] = Field(default_factory=list)
    provenance: list[dict[str, Any]] = Field(default_factory=list)


class MemorySearcher(Protocol):
    def search_memory(self, query: str, *, user_id: str, limit: int = 20) -> list[Any]: ...


def _normalize_query(query: str) -> str:
    return " ".join(query.strip().split())


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "__dict__"):
        return {k: v for k, v in vars(value).items() if not k.startswith("_")}
    return {"value": value}


class RetrievalService:
    """Retrieve evidence from Muse memory without producing an answer."""

    def __init__(self, memory: MemorySearcher | MemoryService) -> None:
        self._memory = memory

    def retrieve(self, user_query: UserQuery) -> RetrievedContext:
        query = _normalize_query(user_query.query)
        results = self._memory.search_memory(
            query,
            user_id=user_query.user_id,
            limit=user_query.limit,
        )

        memories: list[Any] = []
        entities: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []
        timeline: list[dict[str, Any]] = []
        sources: list[dict[str, Any]] = []
        provenance: list[dict[str, Any]] = []

        for result in results[: user_query.limit]:
            item = _as_dict(result)
            body = item.get("body")
            body = _as_dict(body) if body is not None else item
            metadata = _as_dict(body.get("metadata", item.get("metadata", {})))

            memories.append(item)
            entities.extend(_as_dict(v) for v in body.get("entities", []))
            relationships.extend(_as_dict(v) for v in body.get("relationships", []))
            timeline.extend(_as_dict(v) for v in body.get("timelines", []))

            for source in body.get("sources", body.get("source_references", [])):
                sources.append(_as_dict(source))
            for source in body.get("provenance", metadata.get("provenance", [])):
                provenance.append(_as_dict(source))

        return RetrievedContext(
            query=query,
            memories=memories,
            entities=entities,
            relationships=relationships,
            timeline=timeline,
            source_references=sources,
            provenance=provenance,
        )
