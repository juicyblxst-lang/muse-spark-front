from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, Sequence

@dataclass(frozen=True)
class EntityCandidate:
    entity_id: str
    name: str
    entity_type: str
    context: list[str]

class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"

@dataclass(frozen=True)
class ResolvedMention:
    mention: str
    entity_type: str
    status: ResolutionStatus
    entity_id: str | None
    candidate_ids: tuple[str, ...]
    confidence: float
    evidence: tuple[str, ...]

@dataclass(frozen=True)
class ResolvedExtraction:
    mentions: tuple[ResolvedMention, ...]

class EntityResolver(Protocol):
    async def candidates(self, *, user_id: str, mention: str, entity_type: str) -> Sequence[EntityCandidate]: ...

async def resolve_extraction(extraction: Any, *, user_id: str, resolver: EntityResolver) -> ResolvedExtraction:
    mentions=[]
    for entity_type, values in extraction.payload.items():
        if not isinstance(values, list): continue
        for value in values:
            if not isinstance(value, dict) or not value.get("name"): continue
            name=str(value["name"]); candidates=list(await resolver.candidates(user_id=user_id, mention=name, entity_type=entity_type.rstrip("s")))
            mentions.append(ResolvedMention(name, entity_type.rstrip("s"), ResolutionStatus.RESOLVED if candidates else ResolutionStatus.UNRESOLVED, candidates[0].entity_id if candidates else None, tuple(c.entity_id for c in candidates), 1.0 if candidates else 0.0, tuple(str(x) for x in value.get("evidence", []))))
    return ResolvedExtraction(tuple(mentions))
