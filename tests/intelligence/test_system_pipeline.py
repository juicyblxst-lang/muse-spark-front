from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import pytest

from app.services.entity_resolution import EntityCandidate
from app.services.extraction import ExtractedItem
from app.services.ingestion import DoclingIngestionService
from app.services.memory_mapper import MuseMemory
from app.services.relationships import RelationshipGraph
from app.services.system_pipeline import MuseComponentPipeline, PipelineDependencies
from app.services.temporal_analysis import TemporalAnalysis


FIXTURE = Path(__file__).parents[1] / "fixtures" / "muse_component_chain.md"


class Docling:
    def __init__(self, text: str) -> None:
        self.text = text
        self.paths: list[str] = []

    def convert(self, path: str):
        self.paths.append(path)
        document = type(
            "Document",
            (),
            {
                "texts": [type("Block", (), {"text": self.text, "label": "paragraph", "page": 1})()],
                "export_to_markdown": lambda _: self.text,
            },
        )()
        return type("Result", (), {"document": document})()


class Extraction:
    def __init__(self) -> None:
        self.documents = []

    async def extract(self, document, schema: dict[str, Any]):
        self.documents.append(document)
        return {
            "people": [{"name": "Alice", "description": "lead", "evidence": ["Alice started Muse in 2024."]}],
            "projects": [{"name": "Muse", "description": "project", "evidence": ["Alice started Muse in 2024."]}],
        }


class Resolver:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    async def candidates(self, *, user_id: str, mention: str, entity_type: str) -> Sequence[EntityCandidate]:
        self.calls.append((user_id, mention, entity_type))
        if mention == "Alice":
            return [EntityCandidate(entity_id="alice-1", name="Alice", entity_type="person", context=["Muse", "2024"])]
        if mention == "Muse":
            return [EntityCandidate(entity_id="muse-1", name="Muse", entity_type="project", context=["Alice", "2024"])]
        return []


class Relationships:
    def __init__(self) -> None:
        self.resolved = None

    async def extract_relationships(self, resolved, schema: dict[str, Any]):
        self.resolved = resolved
        return {"extraction_run_id": schema["extraction_run_id"], "relationships": []}


class Temporal:
    def __init__(self) -> None:
        self.relationships = None

    async def analyze_temporal(self, relationships, schema: dict[str, Any]):
        self.relationships = relationships
        return {"extraction_run_id": schema["extraction_run_id"], "events": []}


class Memory:
    def __init__(self) -> None:
        self.written: list[MuseMemory] = []

    def write_memory(self, memory: MuseMemory):
        self.written.append(memory)
        return "memory-1"


@pytest.mark.asyncio
async def test_full_component_pipeline_passes_each_stage_contract_forward(monkeypatch):
    source = FIXTURE.read_text(encoding="utf-8")
    docling = Docling(source)
    extraction = Extraction()
    resolver = Resolver()
    relationships = Relationships()
    temporal = Temporal()
    memory = Memory()
    ingestion = DoclingIngestionService()
    monkeypatch.setattr(ingestion, "_get_converter", lambda: docling)

    pipeline = MuseComponentPipeline(
        PipelineDependencies(
            extraction=extraction,
            resolver=resolver,
            relationships=relationships,
            temporal=temporal,
            memory=memory,
            ingestion=ingestion,
        )
    )

    result = await pipeline.run(
        str(FIXTURE),
        user_id="user-1",
        document_id="doc-1",
        extraction_run_id="run-1",
    )

    assert result.extraction_run_id == "run-1"
    assert extraction.documents == [result.document]
    assert relationships.resolved is result.resolution
    assert temporal.relationships is result.relationships
    assert result.relationships.extraction_run_id == result.temporal.extraction_run_id == "run-1"
    assert result.provenance
    assert all(record.document_id == "doc-1" for record in result.provenance)
    assert all(record.extraction_run_id == "run-1" for record in result.provenance)
    assert result.memory.sources
    assert result.memory.sources[0].document_id == "doc-1"
    assert result.memory.metadata["extraction_run_id"] == "run-1"
    assert memory.written == [result.memory]
    assert resolver.calls[0][0] == "user-1"
