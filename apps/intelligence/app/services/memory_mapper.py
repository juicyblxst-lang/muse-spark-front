from dataclasses import dataclass
from typing import Any, Protocol

@dataclass(frozen=True)
class Confidence:
    value: float
    status: str
@dataclass(frozen=True)
class SourceReference:
    provenance_id: str
    document_id: str
    document_version: str
    source_location: str
@dataclass(frozen=True)
class ProvenancedKnowledge:
    user_id: str
    entities: list[dict[str,Any]]
    events: list[dict[str,Any]]
    relationships: list[dict[str,Any]]
    timelines: list[dict[str,Any]]
    source_references: list[SourceReference]
    confidence: Confidence
    extraction_run_id: str
@dataclass(frozen=True)
class MuseMemory:
    user_id: str
    entities: list[dict[str,Any]]
    events: list[dict[str,Any]]
    relationships: list[dict[str,Any]]
    sources: list[SourceReference]
class SibylMemoryWriter(Protocol):
    def write_memory(self, memory: MuseMemory) -> Any: ...
class MemoryMapper:
    def map(self, knowledge: ProvenancedKnowledge) -> MuseMemory:
        return MuseMemory(knowledge.user_id,knowledge.entities,knowledge.events,knowledge.relationships,knowledge.source_references)
    @staticmethod
    def write(knowledge, writer): return writer.write_memory(MemoryMapper().map(knowledge))
