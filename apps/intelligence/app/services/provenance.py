from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

class ProvenanceKind(str, Enum): SOURCE = "SOURCE"
@dataclass(frozen=True)
class ProvenanceRecord:
    provenance_id: str
    document_id: str
    document_version: str
    page: int | None
    block_id: str
    source_text: str
    source_location: str
    extraction_run_id: str
    model: str
    kind: ProvenanceKind = ProvenanceKind.SOURCE
class ProvenanceStore:
    def __init__(self): self.records=[]
    def add(self, record): self.records.append(record)
def create_provenance_record(**kwargs): return ProvenanceRecord(provenance_id=str(uuid4()), **kwargs)
