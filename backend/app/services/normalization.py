from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class MuseDocumentBlock:
    """Canonical Muse block; downstream code never needs to know Docling types."""

    block_type: str
    text: str
    page: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MuseDocument:
    """Stable Muse document schema independent of the ingestion provider."""

    title: str | None
    source_path: str
    file_name: str
    file_type: str
    text: str
    blocks: tuple[MuseDocumentBlock, ...]
    page_count: int | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blocks"] = [asdict(block) for block in self.blocks]
        return payload


class DocumentNormalizationError(RuntimeError):
    """Raised when an ingested document cannot become the canonical Muse schema."""


def normalize_document(ingested: Any) -> MuseDocument:
    """Normalize Build 08 output into the stable Muse document contract.

    The function intentionally consumes the small public surface of the ingestion
    result rather than exposing Docling classes to the rest of the application.
    """
    try:
        source_path = str(ingested.source_path)
        metadata = dict(ingested.metadata or {})
        text = str(ingested.text or "")
    except (AttributeError, TypeError, ValueError) as exc:
        raise DocumentNormalizationError("Invalid ingestion result") from exc

    file_name = str(metadata.get("file_name") or source_path.rsplit("/", 1)[-1])
    file_type = str(metadata.get("extension") or "").lower().lstrip(".")
    if not file_type:
        file_type = "unknown"

    title = _extract_title(ingested, metadata, file_name)
    blocks = tuple(_normalize_blocks(ingested, text))

    return MuseDocument(
        title=title,
        source_path=source_path,
        file_name=file_name,
        file_type=file_type,
        text=text,
        blocks=blocks,
        page_count=getattr(ingested, "page_count", None),
        metadata=metadata,
    )


def _extract_title(ingested: Any, metadata: dict[str, Any], file_name: str) -> str | None:
    title = metadata.get("title")
    if title:
        return str(title)

    document = getattr(ingested, "document", None)
    doc_metadata = getattr(document, "metadata", None)
    if isinstance(doc_metadata, dict) and doc_metadata.get("title"):
        return str(doc_metadata["title"])

    stem = file_name.rsplit(".", 1)[0].strip()
    return stem or None


def _normalize_blocks(ingested: Any, fallback_text: str) -> Iterable[MuseDocumentBlock]:
    document = getattr(ingested, "document", None)
    raw_blocks = getattr(document, "texts", None) if document is not None else None

    if raw_blocks:
        for item in raw_blocks:
            text = _item_text(item)
            if not text:
                continue
            yield MuseDocumentBlock(
                block_type=_item_type(item),
                text=text,
                page=_item_page(item),
                metadata={},
            )
        return

    if fallback_text.strip():
        yield MuseDocumentBlock(block_type="document", text=fallback_text)


def _item_text(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    for attr in ("text", "content"):
        value = getattr(item, attr, None)
        if value:
            return str(value).strip()
    return ""


def _item_type(item: Any) -> str:
    value = getattr(item, "label", None) or getattr(item, "type", None)
    return str(value).lower() if value else "text"


def _item_page(item: Any) -> int | None:
    value = getattr(item, "page", None)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
