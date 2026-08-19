from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, Sequence

from pydantic import BaseModel, ConfigDict, Field

from app.services.extraction import ExtractedItem, ExtractionResult


class ResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    NEW = "new"


class EntityCandidate(BaseModel):
    """Existing user entity considered as a possible match."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str
    name: str
    entity_type: str
    aliases: list[str] = Field(default_factory=list)
    context: list[str] = Field(default_factory=list)


class ResolvedMention(BaseModel):
    """A preserved source mention plus its resolution decision and evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mention: str
    entity_type: str
    status: ResolutionStatus
    entity_id: str | None = None
    candidate_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    context: list[str] = Field(default_factory=list)


class ResolvedExtraction(BaseModel):
    """Validated output of Muse entity resolution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mentions: list[ResolvedMention] = Field(default_factory=list)


class EntityResolver(Protocol):
    """User-scoped candidate provider; storage/database details stay outside this layer."""

    async def candidates(
        self,
        *,
        user_id: str,
        mention: str,
        entity_type: str,
    ) -> Sequence[EntityCandidate]:
        ...


@dataclass(frozen=True)
class ResolutionDecision:
    status: ResolutionStatus
    entity_id: str | None
    confidence: float
    evidence: list[str]


async def resolve_extraction(
    extraction: ExtractionResult,
    *,
    user_id: str,
    resolver: EntityResolver,
    min_confidence: float = 0.85,
) -> ResolvedExtraction:
    """Resolve extracted mentions against the user's existing entities.

    Resolution is deliberately conservative. Exact string equality is only one
    signal; aliases, type, context and document context must support the decision.
    When evidence is insufficient, ambiguity is preserved instead of being silently
    collapsed into an existing entity.
    """
    mentions: list[ResolvedMention] = []
    for entity_type, items in _iter_entities(extraction):
        for item in items:
            context = tuple(item.evidence)
            candidates = list(
                await resolver.candidates(
                    user_id=user_id,
                    mention=item.name,
                    entity_type=entity_type,
                )
            )
            decision = _decide(
                mention=item.name,
                entity_type=entity_type,
                context=context,
                candidates=candidates,
                min_confidence=min_confidence,
            )
            mentions.append(
                ResolvedMention(
                    mention=item.name,
                    entity_type=entity_type,
                    status=decision.status,
                    entity_id=decision.entity_id,
                    candidate_ids=[c.entity_id for c in candidates],
                    confidence=decision.confidence,
                    evidence=decision.evidence,
                    context=list(context),
                )
            )
    return ResolvedExtraction(mentions=mentions)


def _iter_entities(extraction: ExtractionResult):
    yield "person", extraction.people
    yield "organization", extraction.organizations
    yield "project", extraction.projects
    yield "creative_work", extraction.creative_works
    yield "concept", extraction.concepts


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _decide(
    *,
    mention: str,
    entity_type: str,
    context: Sequence[str],
    candidates: Sequence[EntityCandidate],
    min_confidence: float,
) -> ResolutionDecision:
    """Score candidates using multiple signals; never resolve on name alone."""
    if not candidates:
        return ResolutionDecision(
            status=ResolutionStatus.NEW,
            entity_id=None,
            confidence=0.0,
            evidence=["no existing candidates found"],
        )

    normalized_mention = _normalize(mention)
    context_text = _normalize(" ".join(context))
    scored: list[tuple[float, EntityCandidate, list[str]]] = []

    for candidate in candidates:
        score = 0.0
        evidence: list[str] = []
        normalized_names = [_normalize(candidate.name)] + [_normalize(a) for a in candidate.aliases]

        if normalized_mention in normalized_names:
            score += 0.35
            evidence.append("exact name or alias match")
        elif any(normalized_mention in name or name in normalized_mention for name in normalized_names):
            score += 0.15
            evidence.append("partial name match")

        if _normalize(candidate.entity_type) == _normalize(entity_type):
            score += 0.25
            evidence.append("entity type match")

        candidate_context = _normalize(" ".join(candidate.context))
        if context_text and candidate_context:
            context_tokens = set(context_text.split())
            candidate_tokens = set(candidate_context.split())
            overlap = len(context_tokens & candidate_tokens) / max(1, len(context_tokens | candidate_tokens))
            score += min(0.25, overlap * 0.5)
            if overlap > 0:
                evidence.append("context overlap")

        scored.append((min(score, 1.0), candidate, evidence))

    scored.sort(key=lambda row: row[0], reverse=True)
    best_score, best, best_evidence = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0

    # A name match alone tops out below the resolution threshold. This makes
    # ambiguous cases explicit and prevents the classic "Rose" collision.
    if best_score >= min_confidence and best_score - second_score >= 0.10:
        return ResolutionDecision(
            status=ResolutionStatus.RESOLVED,
            entity_id=best.entity_id,
            confidence=best_score,
            evidence=best_evidence,
        )

    return ResolutionDecision(
        status=ResolutionStatus.AMBIGUOUS,
        entity_id=None,
        confidence=best_score,
        evidence=best_evidence + ["insufficient evidence for unique resolution"],
    )
