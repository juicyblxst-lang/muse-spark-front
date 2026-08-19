from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, Sequence
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.entity_resolution import ResolvedExtraction, ResolutionStatus


class RelationshipEvidenceType(StrEnum):
    EXPLICIT = "EXPLICIT"
    INFERRED = "INFERRED"


class RelationshipEntity(BaseModel):
    """An entity reference used by a relationship."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str | None = None
    mention: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)


class Relationship(BaseModel):
    """A validated relationship with provenance and evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    subject: RelationshipEntity
    relationship_type: str = Field(min_length=1)
    object: RelationshipEntity
    evidence: list[str] = Field(min_length=1)
    source_location: str = Field(min_length=1)
    extraction_run_id: str = Field(min_length=1)
    evidence_type: RelationshipEvidenceType

    @model_validator(mode="after")
    def require_confirmable_explicit_relationship(self) -> "Relationship":
        if self.evidence_type is RelationshipEvidenceType.EXPLICIT:
            if not self.subject.entity_id or not self.object.entity_id:
                raise ValueError("EXPLICIT relationships require resolved subject and object IDs")
        return self


class RelationshipGraph(BaseModel):
    """Structured relationship output for downstream Muse stages."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    extraction_run_id: str = Field(min_length=1)
    relationships: list[Relationship] = Field(default_factory=list)


class StructuredRelationshipClient(Protocol):
    """Provider-neutral LLM contract for structured relationship extraction."""

    async def extract_relationships(
        self,
        resolved: ResolvedExtraction,
        schema: dict[str, Any],
    ) -> Any:
        ...


class RelationshipExtractionError(RuntimeError):
    """Raised when structured relationship output is invalid or unsafe."""


RELATIONSHIP_INSTRUCTIONS = """Identify only relationships supported by the supplied ResolvedExtraction.
Do not invent relationships and do not infer a relationship merely because two entities
occur in the same document. Every relationship must include subject, relationship type,
object, source evidence, source location, extraction run ID, and evidence type.
Use EXPLICIT only when the source evidence directly states the relationship.
Use INFERRED only when a relationship is suggested but not directly stated; inferred
relationships must never be treated as confirmed facts. Preserve ambiguity rather than
forcing a relationship between unresolved entities.
"""


async def extract_relationships(
    resolved: ResolvedExtraction,
    *,
    client: StructuredRelationshipClient,
    extraction_run_id: str | None = None,
) -> RelationshipGraph:
    """Extract and validate a relationship graph from resolved entity mentions."""
    run_id = extraction_run_id or str(uuid4())
    raw = await client.extract_relationships(
        resolved,
        {
            "name": "RelationshipGraph",
            "description": RELATIONSHIP_INSTRUCTIONS,
            "schema": RelationshipGraph.model_json_schema(),
            "extraction_run_id": run_id,
        },
    )
    try:
        graph = RelationshipGraph.model_validate(raw)
    except Exception as exc:
        raise RelationshipExtractionError("LLM output did not match RelationshipGraph") from exc

    if graph.extraction_run_id != run_id:
        raise RelationshipExtractionError("relationship extraction run ID mismatch")

    _validate_against_resolution(graph, resolved)
    return graph


def validate_relationship_graph(
    graph: RelationshipGraph,
    resolved: ResolvedExtraction,
) -> RelationshipGraph:
    """Validate an already-produced graph against the resolution state."""
    _validate_against_resolution(graph, resolved)
    return graph


def _validate_against_resolution(
    graph: RelationshipGraph,
    resolved: ResolvedExtraction,
) -> None:
    resolved_ids = {
        mention.entity_id
        for mention in resolved.mentions
        if mention.status is ResolutionStatus.RESOLVED and mention.entity_id
    }

    for relationship in graph.relationships:
        if relationship.evidence_type is RelationshipEvidenceType.EXPLICIT:
            if relationship.subject.entity_id not in resolved_ids:
                raise RelationshipExtractionError(
                    "explicit subject must reference a resolved entity"
                )
            if relationship.object.entity_id not in resolved_ids:
                raise RelationshipExtractionError(
                    "explicit object must reference a resolved entity"
                )
        if not relationship.evidence:
            raise RelationshipExtractionError("relationship evidence is required")
        if not relationship.source_location:
            raise RelationshipExtractionError("relationship source location is required")


@dataclass(frozen=True)
class RelationshipExtractionStage:
    """Pipeline adapter for the relationship-extraction stage."""

    client: StructuredRelationshipClient

    async def run(
        self,
        resolved: ResolvedExtraction,
        *,
        extraction_run_id: str | None = None,
    ) -> RelationshipGraph:
        return await extract_relationships(
            resolved,
            client=self.client,
            extraction_run_id=extraction_run_id,
        )
