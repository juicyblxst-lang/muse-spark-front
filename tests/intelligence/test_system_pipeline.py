from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import pytest

from app.services.entity_resolution import EntityCandidate
from app.services.extraction import ExtractionResult
from app.services.ingestion import DoclingIngestionService
from app.services.memory_mapper import MuseMemory
from app.services.provenance import ProvenanceStore
from app.services.relationships import RelationshipGraph
from app.services.system_pipeline import MuseComponentPipeline
from app.services.temporal_analysis import TemporalAnalysis


FIXTURE = Path(__file__).parents[1] / "fixtures" / "muse_component_chain.md"


class FakeDocling:
    def __init__(self, text: str):
        self.text = text
        self.calls: list[str] = []

    def convert(self, path: str):
        self.calls.append(path)
        document = type("Document", (), {})()
        document.texts = [type("Block", (), {"text": self.text, "label": "paragraph", "page": 1})()]
        document.export_to_markdown = lambda: self.text
        return type("Result", (), {"document": document})()


class FakeExtraction:
    def __init__(self):
        self.document = None

    async def extract(self, document, schema: dict[str, Any]):
        self.document = document
        return {"people": [{"name": "Alice", "evidence": ["Alice started the Muse project in 2024."]}]}


class FakeResolver:
    async def candidates(self, *, user_id: str, mention: str, entity_type: str) -> Sequence[EntityCandidate]:
        return [EntityCandidate(entity_id="alice-1", name="Alice", entity_type="person", context=["Muse project", "2024"])]


class FakeRelationships:
    def __init__(self):
        self.resolved = None

    async def extract_relationships(self, resolved, schema: dict[str, Any]):
        self.resolved = resolved
        return {"extraction_run_id": schema["extraction_run_id"], "relationships": []}


class FakeTemporal:
    def __init__(self):
        self.relationships = None

    async def analyze_temporal(self, relationships, schema: dict[str, Any]):
        self.relationships = relationships
        return {"extraction_run_id": schema["extraction_run_id"], "events": []}


class FakeSibyl:
    def __init__(self):
        self.memories: list[MuseMemory] = []

    def write_memory(self, memory: MuseMemory):
        self.memories.append(memory)
        return "memory-1"


@pytest.mark.asyncio
async def test_pipeline_connects_contracts_and_external_boundaries(monkeypatch):
    source = FIXTURE.read_text(encoding="utf-8")
    docling = FakeDocling(source)
    ingestion = DoclingIngestionService()
    monkeypatch.setattr(ingestion, "_get_converter", lambda: docling)

    extraction = FakeExtraction()
    relationships = FakeRelationships()
    temporal = FakeTemporal()
    sibyl = FakeSibyl()

    pipeline = MuseComponentPipeline(
        ingestion=ingestion,
        extraction_client=extraction,
        resolver=FakeResolver(),
        relationship_client=relationships,
        temporal_client=temporal,
        memory_writer=sibyl,
        provenance_store=ProvenanceStore(),
    )

    result = await pipeline.run(FIXTURE, user_id="user-1", document_id="doc-1")

    assert extraction.document is result.document
    assert relationships.resolved is result.resolution
    assert temporal.relationships is result.relationships
    assert result.extraction_run_id == result.relationships.extraction_run_id == result.temporal.extraction_run_id
    assert result.provenance
    assert all(record.document_id == "doc-1" for record in result.provenance)
    assert all(record.kind.value == "SOURCE" for record in result.provenance)
    assert result.memory.sources
    assert result.memory.sources[0].document_id == "doc-1"
    assert sibyl.memories == [result.memory]
    assert result.memory_id == "memory-1"
