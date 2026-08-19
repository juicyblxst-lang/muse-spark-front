from __future__ import annotations

from enum import StrEnum
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.services.relationships import RelationshipGraph


class TemporalPrecision(StrEnum):
    EXACT = "EXACT"
    MONTH = "MONTH"
    YEAR = "YEAR"
    RANGE = "RANGE"
    RELATIVE = "RELATIVE"
    UNKNOWN = "UNKNOWN"


class TemporalRelation(StrEnum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    DURING = "DURING"
    OVERLAPS = "OVERLAPS"
    SEQUENCE = "SEQUENCE"
    NONE = "NONE"


class TemporalReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str | None = None
    mention: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)


class TemporalEvent(BaseModel):
    """A temporal interpretation with explicit provenance and bounded precision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    temporal_event_id: str = Field(min_length=1)
    referenced_entity: TemporalReference
    precision: TemporalPrecision
    normalized_start: str | None = None
    normalized_end: str | None = None
    original_expression: str = Field(min_length=1)
    source_evidence: list[str] = Field(min_length=1)
    source_location: str = Field(min_length=1)
    extraction_run_id: str = Field(min_length=1)
    relation: TemporalRelation = TemporalRelation.NONE
    relation_target: TemporalReference | None = None
    uncertainty: str | None = None
    duration: str | None = None

    @model_validator(mode="after")
    def validate_precision(self) -> "TemporalEvent":
        if self.precision is TemporalPrecision.EXACT and not self.normalized_start:
            raise ValueError("EXACT temporal events require a normalized start")
        if self.precision is TemporalPrecision.RANGE and not (
            self.normalized_start or self.normalized_end
        ):
            raise ValueError("RANGE temporal events require normalized bounds")
        if self.relation is not TemporalRelation.NONE and self.relation_target is None:
            raise ValueError("temporal relations require a relation target")
        return self


class TemporalAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    extraction_run_id: str = Field(min_length=1)
    events: list[TemporalEvent] = Field(default_factory=list)


class StructuredTemporalClient(Protocol):
    async def analyze_temporal(
        self,
        relationships: RelationshipGraph,
        schema: dict[str, Any],
    ) -> Any:
        ...


class TemporalAnalysisError(RuntimeError):
    """Raised when temporal output is invalid or overstates source precision."""


TEMPORAL_INSTRUCTIONS = """Analyze temporal information supported by the supplied relationship graph.
Identify exact dates, years, months, relative dates, sequences, before/after relations,
durations, ranges, and uncertainty. Normalize dates only when the source supports that
precision. Never fabricate an exact date from an imprecise statement. Preserve the exact
original temporal expression and source evidence for every interpretation.
Use precision EXACT, MONTH, YEAR, RANGE, RELATIVE, or UNKNOWN. Relative expressions such
as 'three years ago', 'last summer', 'before I moved', or 'after we abandoned the project'
must remain RELATIVE unless an explicit reference date/context makes a safer normalization
possible. Temporal events must reference the original entity/event. Do not invent temporal
relationships.
"""


async def analyze_temporal(
    relationships: RelationshipGraph,
    *,
    client: StructuredTemporalClient,
    extraction_run_id: str | None = None,
) -> TemporalAnalysis:
    run_id = extraction_run_id or str(uuid4())
    raw = await client.analyze_temporal(
        relationships,
        {
            "name": "TemporalAnalysis",
            "description": TEMPORAL_INSTRUCTIONS,
            "schema": TemporalAnalysis.model_json_schema(),
            "extraction_run_id": run_id,
        },
    )
    try:
        result = TemporalAnalysis.model_validate(raw)
    except Exception as exc:
        raise TemporalAnalysisError("LLM output did not match TemporalAnalysis") from exc

    if result.extraction_run_id != run_id:
        raise TemporalAnalysisError("temporal extraction run ID mismatch")

    _validate_temporal_events(result)
    return result


def validate_temporal_analysis(result: TemporalAnalysis) -> TemporalAnalysis:
    _validate_temporal_events(result)
    return result


def _validate_temporal_events(result: TemporalAnalysis) -> None:
    for event in result.events:
        if not event.source_evidence:
            raise TemporalAnalysisError("temporal source evidence is required")
        if not event.source_location:
            raise TemporalAnalysisError("temporal source location is required")
        if event.precision is TemporalPrecision.RELATIVE:
            # Relative expressions must not masquerade as exact normalized dates.
            if event.normalized_start or event.normalized_end:
                raise TemporalAnalysisError(
                    "RELATIVE temporal events cannot contain normalized calendar bounds"
                )
        if event.precision is TemporalPrecision.UNKNOWN:
            if event.normalized_start or event.normalized_end:
                raise TemporalAnalysisError(
                    "UNKNOWN temporal precision cannot contain normalized calendar bounds"
                )
