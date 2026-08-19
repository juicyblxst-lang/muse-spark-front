from typing import Any

from app.services.memory_mapper import (
    Confidence,
    MemoryMapper,
    MuseMemory,
    ProvenancedKnowledge,
    SourceReference,
)


class MockSibyl:
    def __init__(self) -> None:
        self.written: list[MuseMemory] = []

    def write_memory(self, memory: MuseMemory) -> Any:
        self.written.append(memory)
        return "sibyl-memory-1"


def knowledge() -> ProvenancedKnowledge:
    return ProvenancedKnowledge(
        user_id="user-1",
        extraction_run_id="run-1",
        entities=[{"id": "e1", "name": "Rose", "type": "person"}],
        events=[{"id": "ev1", "type": "conversation"}],
        relationships=[{"subject": "e1", "type": "created", "object": "idea-1"}],
        timelines=[{"event_id": "ev1", "precision": "YEAR", "value": "2026"}],
        source_references=[
            SourceReference(
                provenance_id="p1",
                document_id="doc-1",
                document_version="1",
                source_location="page 2, block b4",
            )
        ],
        confidence=Confidence(value=0.91, status="resolved"),
    )


def test_mapper_translates_without_persistence() -> None:
    memory = MemoryMapper().map(knowledge())

    assert memory.user_id == "user-1"
    assert memory.entities[0]["name"] == "Rose"
    assert memory.events[0]["id"] == "ev1"
    assert memory.relationships[0]["type"] == "created"
    assert memory.timelines[0]["precision"] == "YEAR"
    assert memory.sources[0].provenance_id == "p1"
    assert memory.metadata["extraction_run_id"] == "run-1"
    assert memory.metadata["confidence"]["value"] == 0.91


def test_mapper_delegates_to_mocked_sibyl() -> None:
    sibyl = MockSibyl()

    result = MemoryMapper().write(knowledge(), sibyl)

    assert result == "sibyl-memory-1"
    assert len(sibyl.written) == 1
    assert sibyl.written[0].user_id == "user-1"
    assert sibyl.written[0].sources[0].document_id == "doc-1"
