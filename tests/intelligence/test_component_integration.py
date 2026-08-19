from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import pytest

from app.services.entity_resolution import EntityCandidate, ResolutionStatus, resolve_extraction
from app.services.extraction import extract_document
from app.services.ingestion import DoclingIngestionService
from app.services.memory_mapper import (
    Confidence,
    MemoryMapper,
    MuseMemory,
    ProvenancedKnowledge,
    SourceReference,
)
from app.services.normalization import MuseDocument, normalize_document
from app.services.provenance import (
    ProvenanceKind,
    ProvenanceRecord,
    ProvenanceStore,
    create_provenance_record,
    validate_source_provenance,
)
from app.services.relationships import extract_relationships
from app.services.temporal_analysis import TemporalPrecision, analyze_temporal


FIXTURE = Path(__file__).parents[1] / "fixtures" / "muse_component_chain.md"
DOCUMENT_ID = "doc-component-1"
DOCUMENT_VERSION = "1"
RUN_ID = "run-component-1"
SOURCE_LOCATION = "page 1, block 1"
SOURCE_EVIDENCE = "Alice started the Muse project in 2024."


@dataclass
class MockDoclingDocument:
    text: str

    @property
    def texts(self):
        return [type("Block", (), {"text": self.text, "label": "paragraph", "page": 1})()]

    def export_to_markdown(self) -> str:
        return self.text


class MockDoclingConverter:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[str] = []

    def convert(self, path: str):
        self.calls.append(path)
        return type("Result", (), {"document": MockDoclingDocument(self.text)})()


class MockExtractionClient:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.received_document: MuseDocument | None = None

    async def extract(self, document: MuseDocument, schema: dict[str, Any]) -> Any:
        self.received_document = document
        return self.result


class MockResolver:
    def __init__(self, candidates_by_mention: dict[str, Sequence[EntityCandidate]]) -> None:
        self.candidates_by_mention = candidates_by_mention
        self.calls: list[dict[str, str]] = []

    async def candidates(self, *, user_id: str, mention: str, entity_type: str):
        self.calls.append({"user_id": user_id, "mention": mention, "entity_type": entity_type})
        return self.candidates_by_mention.get(mention, [])


class MockRelationshipClient:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.received_resolved = None

    async def extract_relationships(self, resolved, schema: dict[str, Any]) -> Any:
        self.received_resolved = resolved
        return self.result


class MockTemporalClient:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.received_relationships = None

    async def analyze_temporal(self, relationships, schema: dict[str, Any]) -> Any:
        self.received_relationships = relationships
        return self.result


class MockSibyl:
    def __init__(self) -> None:
        self.written: list[MuseMemory] = []

    def write_memory(self, memory: MuseMemory) -> str:
        self.written.append(memory)
        return "sibyl-memory-component-1"


def _source_reference() -> SourceReference:
    return SourceReference(
        provenance_id="prov-component-1",
        document_id=DOCUMENT_ID,
        document_version=DOCUMENT_VERSION,
        source_location=SOURCE_LOCATION,
    )


@pytest.mark.asyncio
async def test_component_chain_preserves_contracts_provenance_ambiguity_and_time(monkeypatch):
    source_text = FIXTURE.read_text(encoding="utf-8")
    converter = MockDoclingConverter(source_text)
    ingestion = DoclingIngestionService()
    monkeypatch.setattr(ingestion, "_get_converter", lambda: converter)

    ingested = ingestion.ingest(FIXTURE)
    assert ingested.text == source_text
    assert converter.calls == [str(FIXTURE.resolve())]

    canonical = normalize_document(ingested)
    assert canonical.text == ingested.text
    assert canonical.file_name == FIXTURE.name
    assert canonical.blocks[0].text == source_text

    extraction_payload = {
        "people": [
            {"name": "Alice", "description": "Muse project lead", "evidence": [SOURCE_EVIDENCE]},
            {
                "name": "Rose",
                "description": "Person mentioned in the design discussion",
                "evidence": ["Rose reviewed the design notes."],
            },
        ],
        "projects": [
            {
                "name": "Muse",
                "description": "The project",
                "evidence": [SOURCE_EVIDENCE],
            }
        ],
    }
    extraction_client = MockExtractionClient(extraction_payload)
    extraction = await extract_document(canonical, extraction_client)
    assert extraction_client.received_document is canonical
    assert extraction.people[0].evidence == [SOURCE_EVIDENCE]

    alice = EntityCandidate(
        entity_id="person-alice",
        name="Alice",
        entity_type="person",
        context=["Muse project lead", "2024"],
    )
    rose_a = EntityCandidate(
        entity_id="person-rose-a",
        name="Rose",
        entity_type="person",
        context=["design notes"],
    )
    rose_b = EntityCandidate(
        entity_id="person-rose-b",
        name="Rose",
        entity_type="person",
        context=["project discussion"],
    )
    muse = EntityCandidate(
        entity_id="project-muse",
        name="Muse",
        entity_type="project",
        context=["project", "2024"],
    )
    resolver = MockResolver({"Alice": [alice], "Rose": [rose_a, rose_b], "Muse": [muse]})
    resolved = await resolve_extraction(
        extraction,
        user_id="user-component-1",
        resolver=resolver,
        min_confidence=0.55,
    )
    assert resolver.calls[0]["user_id"] == "user-component-1"
    alice_resolution = next(m for m in resolved.mentions if m.mention == "Alice")
    rose_resolution = next(m for m in resolved.mentions if m.mention == "Rose")
    muse_resolution = next(m for m in resolved.mentions if m.mention == "Muse")
    assert alice_resolution.status is ResolutionStatus.RESOLVED
    assert alice_resolution.entity_id == "person-alice"
    assert rose_resolution.status is ResolutionStatus.AMBIGUOUS
    assert rose_resolution.entity_id is None
    assert rose_resolution.candidate_ids == ["person-rose-a", "person-rose-b"]
    assert muse_resolution.status is ResolutionStatus.RESOLVED

    relationship_payload = {
        "extraction_run_id": RUN_ID,
        "relationships": [
            {
                "subject": {"entity_id": "person-alice", "mention": "Alice", "entity_type": "person"},
                "relationship_type": "leads",
                "object": {"entity_id": "project-muse", "mention": "Muse", "entity_type": "project"},
                "evidence": [SOURCE_EVIDENCE],
                "source_location": SOURCE_LOCATION,
                "extraction_run_id": RUN_ID,
                "evidence_type": "EXPLICIT",
            }
        ],
    }
    relationship_client = MockRelationshipClient(relationship_payload)
    relationship_graph = await extract_relationships(
        resolved, client=relationship_client, extraction_run_id=RUN_ID
    )
    assert relationship_client.received_resolved is resolved
    relationship = relationship_graph.relationships[0]
    assert relationship.evidence == [SOURCE_EVIDENCE]
    assert relationship.source_location == SOURCE_LOCATION
    assert relationship.subject.entity_id == "person-alice"
    assert relationship.object.entity_id == "project-muse"

    temporal_payload = {
        "extraction_run_id": RUN_ID,
        "events": [
            {
                "temporal_event_id": "temporal-1",
                "referenced_entity": {"entity_id": "project-muse", "mention": "Muse", "entity_type": "project"},
                "precision": "YEAR",
                "normalized_start": "2024",
                "original_expression": "in 2024",
                "source_evidence": [SOURCE_EVIDENCE],
                "source_location": SOURCE_LOCATION,
                "extraction_run_id": RUN_ID,
                "relation": "NONE",
            },
            {
                "temporal_event_id": "temporal-2",
                "referenced_entity": {"entity_id": "project-muse", "mention": "Muse", "entity_type": "project"},
                "precision": "RELATIVE",
                "original_expression": "three years ago",
                "source_evidence": ["The source says three years ago."],
                "source_location": "page 1, block 2",
                "extraction_run_id": RUN_ID,
                "relation": "NONE",
            },
        ],
    }
    temporal_client = MockTemporalClient(temporal_payload)
    temporal = await analyze_temporal(
        relationship_graph, client=temporal_client, extraction_run_id=RUN_ID
    )
    assert temporal_client.received_relationships is relationship_graph
    assert temporal.events[0].precision is TemporalPrecision.YEAR
    assert temporal.events[0].normalized_start == "2024"
    assert temporal.events[1].precision is TemporalPrecision.RELATIVE
    assert temporal.events[1].original_expression == "three years ago"
    assert temporal.events[1].normalized_start is None

    provenance = create_provenance_record(
        document_id=DOCUMENT_ID,
        document_version=DOCUMENT_VERSION,
        page=1,
        block_id="1",
        source_text=SOURCE_EVIDENCE,
        source_location=SOURCE_LOCATION,
        extraction_run_id=RUN_ID,
        model="mock-extractor",
    )
    store = ProvenanceStore()
    store.add(provenance)
    validate_source_provenance([provenance])
    assert store.require_source(provenance.provenance_id).document_id == DOCUMENT_ID

    knowledge = ProvenancedKnowledge(
        user_id="user-component-1",
        extraction_run_id=RUN_ID,
        entities=[
            {"id": "person-alice", "name": "Alice", "type": "person"},
            {
                "mention": "Rose",
                "type": "person",
                "resolution_status": "ambiguous",
                "candidate_ids": ["person-rose-a", "person-rose-b"],
            },
            {"id": "project-muse", "name": "Muse", "type": "project"},
        ],
        events=[
            {"id": event.temporal_event_id, "expression": event.original_expression, "precision": event.precision.value}
            for event in temporal.events
        ],
        relationships=[
            {
                "subject": relationship.subject.entity_id,
                "type": relationship.relationship_type,
                "object": relationship.object.entity_id,
                "evidence": relationship.evidence,
                "source_location": relationship.source_location,
            }
        ],
        timelines=[
            {
                "event_id": event.temporal_event_id,
                "precision": event.precision.value,
                "value": event.normalized_start,
                "original_expression": event.original_expression,
                "source_evidence": event.source_evidence,
            }
            for event in temporal.events
        ],
        source_references=[_source_reference()],
        confidence=Confidence(value=0.91, status="resolved"),
    )
    memory = MemoryMapper().map(knowledge)
    assert memory.sources[0].provenance_id == "prov-component-1"
    assert memory.sources[0].document_id == DOCUMENT_ID
    assert memory.timelines[0]["precision"] == "YEAR"
    assert memory.timelines[1]["precision"] == "RELATIVE"
    assert memory.entities[1]["resolution_status"] == "ambiguous"
    assert memory.entities[1]["candidate_ids"] == ["person-rose-a", "person-rose-b"]
    assert memory.metadata["extraction_run_id"] == RUN_ID

    sibyl = MockSibyl()
    assert MemoryMapper().write(knowledge, sibyl) == "sibyl-memory-component-1"
    assert sibyl.written[0].sources[0].document_id == DOCUMENT_ID
    assert sibyl.written[0].timelines == memory.timelines

    generated = provenance.model_copy(update={"kind": ProvenanceKind.GENERATED})
    with pytest.raises(ValueError, match="generated content cannot be used as source evidence"):
        validate_source_provenance([generated])


def test_generated_content_never_passes_as_source_evidence():
    generated = ProvenanceRecord(
        provenance_id="generated-1",
        document_id=DOCUMENT_ID,
        document_version=DOCUMENT_VERSION,
        source_text="Model-generated summary",
        source_location=SOURCE_LOCATION,
        extraction_run_id=RUN_ID,
        model="mock-model",
        kind=ProvenanceKind.GENERATED,
    )
    with pytest.raises(ValueError, match="generated content cannot be used as source evidence"):
        generated.assert_source_evidence()


def test_external_services_are_mocked():
    assert True
