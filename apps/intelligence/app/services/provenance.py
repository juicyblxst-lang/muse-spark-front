from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Iterable
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ProvenanceKind(StrEnum):
    SOURCE = "SOURCE"
    GENERATED = "GENERATED"


class ProvenanceRecord(BaseModel):
    """Immutable pointer from a Muse assertion back to uploaded source material."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provenance_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1)
    document_id: str = Field(min_length=1)
    document_version: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1)
    block_id: str | None = None
    source_text: str = Field(min_length=1)
    source_location: str = Field(min_length=1)
    extraction_run_id: str = Field(min_length=1)
    model: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    kind: ProvenanceKind = ProvenanceKind.SOURCE

    @property
    def is_source_evidence(self) -> bool:
        return self.kind is ProvenanceKind.SOURCE

    def assert_source_evidence(self) -> None:
        """Fail closed if generated material is presented as uploaded evidence."""
        if not self.is_source_evidence:
            raise ValueError("generated content cannot be used as source evidence")


class ProvenanceError(ValueError):
    """Raised when provenance cannot establish a source-backed assertion."""


class ProvenanceStore:
    """Small in-memory provenance index; persistence is deliberately injectable."""

    def __init__(self) -> None:
        self._records: dict[str, ProvenanceRecord] = {}

    def add(self, record: ProvenanceRecord) -> ProvenanceRecord:
        record.assert_source_evidence()
        self._records[record.provenance_id] = record
        return record

    def get(self, provenance_id: str) -> ProvenanceRecord:
        try:
            return self._records[provenance_id]
        except KeyError as exc:
            raise ProvenanceError(f"provenance record not found: {provenance_id}") from exc

    def for_document(self, document_id: str) -> list[ProvenanceRecord]:
        return [record for record in self._records.values() if record.document_id == document_id]

    def require_source(self, provenance_id: str) -> ProvenanceRecord:
        record = self.get(provenance_id)
        record.assert_source_evidence()
        return record


def create_provenance_record(
    *,
    document_id: str,
    document_version: str,
    page: int | None,
    block_id: str | None,
    source_text: str,
    source_location: str,
    extraction_run_id: str,
    model: str,
) -> ProvenanceRecord:
    """Create source-only provenance for material extracted from an uploaded document."""
    return ProvenanceRecord(
        document_id=document_id,
        document_version=document_version,
        page=page,
        block_id=block_id,
        source_text=source_text,
        source_location=source_location,
        extraction_run_id=extraction_run_id,
        model=model,
        kind=ProvenanceKind.SOURCE,
    )


def validate_source_provenance(records: Iterable[ProvenanceRecord]) -> None:
    """Fail closed if any record supplied as evidence is generated content."""
    for record in records:
        record.assert_source_evidence()
