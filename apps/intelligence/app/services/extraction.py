from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.services.normalization import MuseDocument


class ExtractedItem(BaseModel):
    """A semantic item extracted from a canonical Muse document."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    description: str | None = None
    evidence: list[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """Validated semantic extraction contract for downstream Muse stages."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    people: list[ExtractedItem] = Field(default_factory=list)
    organizations: list[ExtractedItem] = Field(default_factory=list)
    projects: list[ExtractedItem] = Field(default_factory=list)
    creative_works: list[ExtractedItem] = Field(default_factory=list)
    concepts: list[ExtractedItem] = Field(default_factory=list)


class StructuredExtractionError(RuntimeError):
    """Raised when a structured extraction result cannot be validated."""


class StructuredLLMClient(Protocol):
    """Provider-neutral contract for an LLM that returns structured data."""

    async def extract(self, document: MuseDocument, schema: dict[str, Any]) -> Any:
        ...


EXTRACTION_INSTRUCTIONS = """Identify semantic information in the supplied canonical document.
Return only data matching the supplied ExtractionResult schema.
Extract people, organizations, projects, creative works, and concepts.
Use evidence snippets from the source text when available.
Do not invent entities that are not supported by the document.
"""


async def extract_document(
    document: MuseDocument,
    client: StructuredLLMClient,
) -> ExtractionResult:
    """Run structured LLM extraction and validate its result as ExtractionResult.

    The LLM provider is deliberately injected. This keeps Muse independent of a
    specific model/vendor while ensuring downstream code never receives raw LLM
    text or an unvalidated dictionary.
    """
    try:
        raw = await client.extract(
            document,
            {
                "name": "ExtractionResult",
                "description": EXTRACTION_INSTRUCTIONS,
                "schema": ExtractionResult.model_json_schema(),
            },
        )
        return ExtractionResult.model_validate(raw)
    except (ValidationError, TypeError, ValueError) as exc:
        raise StructuredExtractionError("LLM output did not match ExtractionResult") from exc


def validate_extraction(payload: Any) -> ExtractionResult:
    """Validate an already-produced structured extraction payload."""
    try:
        return ExtractionResult.model_validate(payload)
    except (ValidationError, TypeError, ValueError) as exc:
        raise StructuredExtractionError("Invalid extraction payload") from exc


@dataclass(frozen=True)
class ExtractionStage:
    """Pipeline adapter for Build 07's extraction stage."""

    client: StructuredLLMClient

    async def run(self, document: MuseDocument) -> ExtractionResult:
        return await extract_document(document, self.client)
