from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class IngestedBlock:
    text: str
    label: str = "paragraph"
    page: int | None = None

@dataclass(frozen=True)
class IngestedDocument:
    source_path: str
    text: str
    blocks: tuple[IngestedBlock, ...]

class DoclingIngestionService:
    def _get_converter(self):
        try:
            from docling.document_converter import DocumentConverter
            return DocumentConverter()
        except ImportError as exc:
            raise RuntimeError("Docling is required for document ingestion") from exc

    def ingest(self, source_path: str | Path) -> IngestedDocument:
        path = str(source_path)
        result = self._get_converter().convert(path)
        document = result.document
        text = document.export_to_markdown()
        blocks = tuple(IngestedBlock(getattr(block, "text", ""), getattr(block, "label", "paragraph"), getattr(block, "page", None)) for block in getattr(document, "texts", []))
        return IngestedDocument(path, text, blocks)
