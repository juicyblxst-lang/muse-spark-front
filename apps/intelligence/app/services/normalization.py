from dataclasses import dataclass
from .ingestion import IngestedDocument

@dataclass(frozen=True)
class DocumentBlock:
    text: str
    label: str
    page: int | None

@dataclass(frozen=True)
class MuseDocument:
    source_path: str
    text: str
    blocks: tuple[DocumentBlock, ...]

def normalize_document(document: IngestedDocument) -> MuseDocument:
    return MuseDocument(document.source_path, document.text, tuple(DocumentBlock(b.text,b.label,b.page) for b in document.blocks))
