from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class Confidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: float = Field(ge=0, le=1)
    status: str = Field(min_length=1)


class SourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provenance_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    document_version: str = Field(min_length=1)
    source_location: str = Field(min_length=1)


class ProvenancedKnowledge(BaseModel):
    """Canonical knowledge boundary consumed by the mapper."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str = Field(min_length=1)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    timelines: list[dict[str, Any]] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(default_factory=list)
    confidence: Confidence | None = None
    extraction_run_id: str = Field(min_length=1)


class MuseMemory(BaseModel):
    """Transport representation expected by the Sibyl adapter boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: str = Field(min_length=1)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    relationships: list[dict[str, Any]] = Field(default_factory=list)
    timelines: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SibylMemoryWriter(Protocol):
    """Minimal mocked/real Sibyl interface; no storage implementation belongs here."""

    def write_memory(self, memory: MuseMemory) -> Any: ...


class MemoryMapper:
    """Translate canonical Muse knowledge into Sibyl-compatible memory only."""

    def map(self, knowledge: ProvenancedKnowledge) -> MuseMemory:
        metadata: dict[str, Any] = {
            "extraction_run_id": knowledge.extraction_run_id,
            "provenance": [source.model_dump(mode="json") for source in knowledge.source_references],
        }
        if knowledge.confidence is not None:
            metadata["confidence"] = knowledge.confidence.model_dump(mode="json")

        return MuseMemory(
            user_id=knowledge.user_id,
            entities=list(knowledge.entities),
            events=list(knowledge.events),
            relationships=list(knowledge.relationships),
            timelines=list(knowledge.timelines),
            sources=list(knowledge.source_references),
            metadata=metadata,
        )

    def write(self, knowledge: ProvenancedKnowledge, writer: SibylMemoryWriter) -> Any:
        """Delegate the already-mapped memory to Sibyl; the mapper never persists it itself."""
        return writer.write_memory(self.map(knowledge))
