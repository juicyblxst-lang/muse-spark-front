from __future__ import annotations

import hashlib
import re
import unicodedata
from enum import StrEnum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field


class DeduplicationStatus(StrEnum):
    DUPLICATE = "duplicate"
    POSSIBLE_DUPLICATE = "possible_duplicate"
    UNIQUE = "unique"


class DocumentFingerprint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


def content_hash(content: bytes) -> DocumentFingerprint:
    """Return a deterministic SHA-256 fingerprint for uploaded document bytes."""
    return DocumentFingerprint(content_hash=hashlib.sha256(content).hexdigest())


class DocumentDuplicateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: DeduplicationStatus
    fingerprint: DocumentFingerprint
    matched_document_id: str | None = None


def deduplicate_document(
    content: bytes,
    existing: Iterable[tuple[str, DocumentFingerprint]],
) -> DocumentDuplicateResult:
    fingerprint = content_hash(content)
    for document_id, existing_fingerprint in existing:
        if fingerprint.content_hash == existing_fingerprint.content_hash:
            return DocumentDuplicateResult(
                status=DeduplicationStatus.DUPLICATE,
                fingerprint=fingerprint,
                matched_document_id=document_id,
            )
    return DocumentDuplicateResult(status=DeduplicationStatus.UNIQUE, fingerprint=fingerprint)


class CanonicalEntity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    context: list[str] = Field(default_factory=list)


class EntityCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    entity: CanonicalEntity
    score: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)


class EntityDuplicateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: DeduplicationStatus
    candidates: list[EntityCandidate] = Field(default_factory=list)


def normalize_entity_name(value: str) -> str:
    """Normalize presentation differences without erasing semantic identity."""
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[\u2010-\u2015\-_/]+", " ", value)
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def _token_overlap(left: str, right: str) -> float:
    a, b = set(normalize_entity_name(left).split()), set(normalize_entity_name(right).split())
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _best_score(mention: CanonicalEntity, candidate: CanonicalEntity) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0

    mention_name = normalize_entity_name(mention.name)
    candidate_names = [candidate.name, *candidate.aliases]
    if any(mention_name == normalize_entity_name(name) for name in candidate_names):
        score += 0.65
        reasons.append("normalized_name_or_alias_match")
    else:
        overlap = max((_token_overlap(mention.name, name) for name in candidate_names), default=0.0)
        score += 0.35 * overlap
        if overlap:
            reasons.append("normalized_token_overlap")

    if normalize_entity_name(mention.entity_type) == normalize_entity_name(candidate.entity_type):
        score += 0.25
        reasons.append("entity_type_match")
    else:
        return 0.0, ["entity_type_mismatch"]

    mention_context = {normalize_entity_name(x) for x in mention.context if x.strip()}
    candidate_context = {normalize_entity_name(x) for x in candidate.context if x.strip()}
    if mention_context and candidate_context:
        overlap = len(mention_context & candidate_context) / len(mention_context | candidate_context)
        score += 0.10 * overlap
        if overlap:
            reasons.append("context_overlap")
    return min(score, 1.0), reasons


def deduplicate_entity(
    mention: CanonicalEntity,
    candidates: Iterable[CanonicalEntity],
) -> EntityDuplicateResult:
    scored = [
        EntityCandidate(entity=candidate, score=score, reasons=reasons)
        for candidate in candidates
        for score, reasons in [_best_score(mention, candidate)]
        if score > 0
    ]
    scored.sort(key=lambda item: item.score, reverse=True)
    if not scored:
        return EntityDuplicateResult(status=DeduplicationStatus.UNIQUE)

    top = scored[0]
    second = scored[1] if len(scored) > 1 else None
    if top.score >= 0.90 and (second is None or top.score - second.score >= 0.10):
        return EntityDuplicateResult(status=DeduplicationStatus.DUPLICATE, candidates=scored)
    return EntityDuplicateResult(status=DeduplicationStatus.POSSIBLE_DUPLICATE, candidates=scored)
