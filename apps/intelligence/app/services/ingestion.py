from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class IngestedDocument:
    """Stable Muse-facing representation of a Docling conversion."""

    source_path: str
    document: Any
    text: str
    page_count: int | None
    metadata: dict[str, Any]


class DocumentIngestionError(RuntimeError):
    """Raised when a document cannot be converted into Muse's structured form."""


class DoclingIngestionService:
    """Converts supported local files with Docling without owning pipeline intelligence."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

    def __init__(self) -> None:
        self._converter = None

    def _get_converter(self):
        if self._converter is None:
            try:
                from docling.document_converter import DocumentConverter
            except ImportError as exc:
                raise DocumentIngestionError(
                    "Docling is not installed in this runtime. "
                    "Install the Build 08 ingestion dependencies in the ingestion environment."
                ) from exc
            self._converter = DocumentConverter()
        return self._converter

    def ingest(self, source_path: str | Path) -> IngestedDocument:
        path = Path(source_path).expanduser().resolve()
        if not path.is_file():
            raise DocumentIngestionError(f"Source file does not exist: {path}")
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise DocumentIngestionError(
                "Unsupported ingestion format. Supported formats: PDF, DOCX, TXT, Markdown."
            )

        try:
            result = self._get_converter().convert(str(path))
            document = result.document
            text = document.export_to_markdown()
        except DocumentIngestionError:
            raise
        except Exception as exc:
            raise DocumentIngestionError(f"Docling failed to ingest {path.name}") from exc

        page_count = self._page_count(document)
        metadata = {
            "file_name": path.name,
            "extension": path.suffix.lower(),
            "source": str(path),
        }
        return IngestedDocument(
            source_path=str(path),
            document=document,
            text=text,
            page_count=page_count,
            metadata=metadata,
        )

    @staticmethod
    def _page_count(document: Any) -> int | None:
        pages = getattr(document, "pages", None)
        if pages is None:
            return None
        try:
            return len(pages)
        except TypeError:
            return None


ingestion_service = DoclingIngestionService()
