from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FactStatus(str, Enum):
    SOURCE = "SOURCE"
    EXTRACTED = "EXTRACTED"
    INFERRED = "INFERRED"
    GENERATED = "GENERATED"
    USER_CONFIRMED = "USER_CONFIRMED"


@dataclass(frozen=True)
class ClassifiedFact:
    value: Any
    status: FactStatus
    source_reference: Any | None = None

    @property
    def is_source_fact(self) -> bool:
        return self.status in {FactStatus.SOURCE, FactStatus.EXTRACTED}

    @property
    def is_generated(self) -> bool:
        return self.status == FactStatus.GENERATED


def classify(
    value: Any,
    status: FactStatus,
    *,
    source_reference: Any | None = None,
) -> ClassifiedFact:
    if status in {FactStatus.SOURCE, FactStatus.EXTRACTED} and source_reference is None:
        raise ValueError("source_reference is required for SOURCE and EXTRACTED facts")
    return ClassifiedFact(value=value, status=status, source_reference=source_reference)


def assert_not_source_fact(fact: ClassifiedFact) -> None:
    """Guard presentation layers from treating generated/inferred content as source."""
    if fact.status in {FactStatus.INFERRED, FactStatus.GENERATED}:
        raise ValueError(f"{fact.status.value} information cannot be presented as SOURCE")


def frontend_payload(fact: ClassifiedFact) -> dict[str, Any]:
    """Stable API shape for frontend provenance/status badges."""
    return {
        "value": fact.value,
        "status": fact.status.value,
        "source_reference": fact.source_reference,
    }
