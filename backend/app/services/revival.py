from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class RevivalInput:
    user_request: str
    memories: list[Any] = field(default_factory=list)
    entities: list[Any] = field(default_factory=list)
    relationships: list[Any] = field(default_factory=list)
    temporal_context: list[Any] = field(default_factory=list)
    source_evidence: list[Any] = field(default_factory=list)


@dataclass(frozen=True)
class RevivalCandidate:
    title: str
    original_idea: str
    why_it_was_abandoned: str
    related_old_material: list[Any]
    connections_found: list[Any]
    what_is_different_now: str
    possible_new_direction: str
    source_references: list[Any]
    source_facts: list[str] = field(default_factory=list)
    inferences: list[str] = field(default_factory=list)
    creative_suggestions: list[str] = field(default_factory=list)


class RevivalRuntime(Protocol):
    def generate(self, *, request: RevivalInput) -> RevivalCandidate: ...


class RevivalEngine:
    """Orchestrates revival reasoning over supplied evidence.

    The engine does not retrieve from storage or documents. A runtime may be an
    LLM/OpenClaw implementation, but it receives only the evidence package
    supplied by Muse. Source facts, inferences, and creative suggestions are
    separate fields so generated material cannot masquerade as source evidence.
    """

    def __init__(self, runtime: RevivalRuntime) -> None:
        self._runtime = runtime

    def generate(self, request: RevivalInput) -> RevivalCandidate:
        if not request.user_request.strip():
            raise ValueError("user_request is required")
        candidate = self._runtime.generate(request=request)
        return self._validate(candidate)

    @staticmethod
    def _validate(candidate: RevivalCandidate) -> RevivalCandidate:
        if not candidate.title.strip():
            raise ValueError("revival title is required")
        if not candidate.original_idea.strip():
            raise ValueError("original_idea is required")
        if not isinstance(candidate.source_facts, list):
            raise TypeError("source_facts must be a list")
        if not isinstance(candidate.inferences, list):
            raise TypeError("inferences must be a list")
        if not isinstance(candidate.creative_suggestions, list):
            raise TypeError("creative_suggestions must be a list")
        return candidate


def build_revival_request(
    user_request: str,
    *,
    memories: list[Any] | None = None,
    entities: list[Any] | None = None,
    relationships: list[Any] | None = None,
    temporal_context: list[Any] | None = None,
    source_evidence: list[Any] | None = None,
) -> RevivalInput:
    return RevivalInput(
        user_request=user_request,
        memories=memories or [],
        entities=entities or [],
        relationships=relationships or [],
        temporal_context=temporal_context or [],
        source_evidence=source_evidence or [],
    )
