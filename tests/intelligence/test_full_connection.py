from __future__ import annotations

from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Sequence

import pytest
from starlette.datastructures import Headers
from starlette.datastructures import UploadFile

from app.api.v1.uploads import upload_document
from app.services.entity_resolution import EntityCandidate
from app.services.extraction import ExtractedItem
from app.services.openclaw_agent import OpenClawAgent, build_agent_request
from app.services.processing_worker import ProcessingWorker
from app.services.relationships import RelationshipGraph
from app.services.retrieval import RetrievalService, UserQuery
from app.services.revival import RevivalCandidate, RevivalEngine, build_revival_request
from app.services.system_pipeline import MuseComponentPipeline, PipelineDependencies
from app.services.temporal_analysis import TemporalAnalysis
from app.services.ingestion import DoclingIngestionService
from app.services.memory_mapper import MuseMemory


FIXTURE = Path(__file__).parents[1] / "fixtures" / "muse_component_chain.md"


class FakeDocling:
    def __init__(self, text: str) -> None:
        self.text = text

    def convert(self, path: str):
        document = type(
            "Document",
            (),
            {
                "texts": [
                    type(
                        "Block",
                        (),
                        {"text": self.text, "label": "paragraph", "page": 1},
                    )()
                ],
                "export_to_markdown": lambda _: self.text,
            },
        )()
        return type("Result", (), {"document": document})()


class FakeExtraction:
    async def extract(self, document, schema: dict[str, Any]):
        return {
            "people": [
                {
                    "name": "Alice",
                    "description": "Muse creator",
                    "evidence": ["Alice started Muse in 2024."],
                }
            ],
            "projects": [
                {
                    "name": "Muse",
                    "description": "creative memory project",
                    "evidence": ["Alice started Muse in 2024."],
                }
            ],
        }


class FakeResolver:
    async def candidates(
        self, *, user_id: str, mention: str, entity_type: str
    ) -> Sequence[EntityCandidate]:
        if mention == "Alice":
            return [
                EntityCandidate(
                    entity_id="alice-1",
                    name="Alice",
                    entity_type="person",
                    context=["Muse", "2024"],
                )
            ]
        if mention == "Muse":
            return [
                EntityCandidate(
                    entity_id="muse-1",
                    name="Muse",
                    entity_type="project",
                    context=["Alice", "2024"],
                )
            ]
        return []


class FakeRelationships:
    async def extract_relationships(self, resolved, schema: dict[str, Any]):
        return {"extraction_run_id": schema["extraction_run_id"], "relationships": []}


class FakeTemporal:
    async def analyze_temporal(self, relationships, schema: dict[str, Any]):
        return {"extraction_run_id": schema["extraction_run_id"], "events": []}


class FakeMemory:
    def __init__(self) -> None:
        self.written: list[MuseMemory] = []

    def write_memory(self, memory: MuseMemory):
        self.written.append(memory)
        return "memory-1"

    def search_memory(self, query: str, *, user_id: str, limit: int = 20):
        return [memory for memory in self.written if memory.user_id == user_id][:limit]


class FakeStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def upload(self, path: str, payload: bytes, options: dict[str, Any]) -> None:
        self.files[path] = payload

    def download(self, path: str) -> bytes:
        return self.files[path]


class FakeRepository:
    def __init__(self, storage: FakeStorage) -> None:
        self.storage = storage
        self.documents: dict[str, dict[str, Any]] = {}
        self.jobs: dict[str, dict[str, Any]] = {}
        self.updates: list[tuple[str, str, dict[str, Any]]] = []

    def get_job(self, job_id: str, user_id: str):
        job = self.jobs.get(job_id)
        return job if job and job["user_id"] == user_id else None

    def get_document(self, document_id: str, user_id: str):
        document = self.documents.get(document_id)
        return document if document and document["user_id"] == user_id else None

    def update_job(self, job_id: str, user_id: str, values: dict[str, Any]) -> None:
        self.updates.append((job_id, user_id, values))
        self.jobs[job_id].update(values)


class FakeSupabase:
    def __init__(self, repository: FakeRepository, storage: FakeStorage) -> None:
        self.repository = repository
        self.storage = storage
        self._document_counter = 0
        self._job_counter = 0
        self.auth = SimpleNamespace(
            get_user=lambda: SimpleNamespace(user=SimpleNamespace(id="user-1"))
        )
        self.storage_api = self

    def table(self, name: str):
        return FakeTable(self, name)

    def from_(self, bucket: str):
        assert bucket == "muse-documents"
        return self

    def upload(self, path: str, data: bytes, options: dict[str, Any]):
        self.storage.upload(path, data, options)


class FakeTable:
    def __init__(self, client: FakeSupabase, name: str) -> None:
        self.client = client
        self.name = name
        self.payload: dict[str, Any] | None = None
        self.filters: dict[str, str] = {}

    def insert(self, payload: dict[str, Any]):
        self.payload = payload
        return self

    def delete(self):
        return self

    def eq(self, key: str, value: str):
        self.filters[key] = value
        return self

    def execute(self):
        if self.name == "documents" and self.payload is not None:
            self.client._document_counter += 1
            document_id = f"00000000-0000-0000-0000-{self.client._document_counter:012d}"
            document = {"id": document_id, "version": 1, **self.payload}
            self.client.repository.documents[document_id] = document
            return SimpleNamespace(data=[document])
        if self.name == "processing_jobs" and self.payload is not None:
            self.client._job_counter += 1
            job_id = f"00000000-0000-0000-0000-{self.client._job_counter + 100:012d}"
            job = {"id": job_id, **self.payload}
            self.client.repository.jobs[job_id] = job
            return SimpleNamespace(data=[job])
        return SimpleNamespace(data=[])


class FakePipelineProvider:
    def __init__(self, pipeline: MuseComponentPipeline) -> None:
        self.pipeline = pipeline

    def build(self, user_id: str):
        assert user_id == "user-1"
        return self.pipeline


class FakeOpenClaw:
    def __init__(self) -> None:
        self.contexts = []

    def run(self, *, query: str, context, tools):
        self.contexts.append(context)
        return type(
            "Response",
            (),
            {"answer": "Muse remembers the 2024 project.", "tool_calls": ()},
        )()


class FakeRevival:
    def __init__(self) -> None:
        self.requests = []

    def generate(self, *, request):
        self.requests.append(request)
        return RevivalCandidate(
            title="Revisit Muse",
            original_idea="A creative memory project started in 2024.",
            why_it_was_abandoned="The test fixture does not state why it was abandoned.",
            related_old_material=request.memories,
            connections_found=request.relationships,
            what_is_different_now="The idea can be revisited with today's context.",
            possible_new_direction="Explore a smaller prototype.",
            source_references=request.source_evidence,
            source_facts=["Alice started Muse in 2024."],
            inferences=["The project may be worth revisiting."],
            creative_suggestions=["Build a small prototype."],
        )


@pytest.mark.asyncio
async def test_full_connection_uploads_processes_retrieves_and_revives():
    source = FIXTURE.read_text(encoding="utf-8")
    storage = FakeStorage()
    repository = FakeRepository(storage)
    supabase = FakeSupabase(repository, storage)

    upload = UploadFile(
        file=BytesIO(source.encode("utf-8")),
        filename=FIXTURE.name,
        headers=Headers({"content-type": "text/markdown"}),
    )
    upload_contract = await upload_document(upload, supabase)

    assert set(upload_contract) == {"documentId", "jobId", "storagePath"}
    assert upload_contract["storagePath"] in storage.files

    ingestion = DoclingIngestionService()
    docling = FakeDocling(source)
    ingestion._get_converter = lambda: docling
    memory = FakeMemory()
    pipeline = MuseComponentPipeline(
        PipelineDependencies(
            extraction=FakeExtraction(),
            resolver=FakeResolver(),
            relationships=FakeRelationships(),
            temporal=FakeTemporal(),
            memory=memory,
            ingestion=ingestion,
        )
    )

    stage_events: list[tuple[str, int]] = []

    async def stage_callback(stage: str, progress: int) -> None:
        stage_events.append((stage, progress))

    original_run = pipeline.run

    async def run_with_stage(source_path: str, **kwargs):
        return await original_run(source_path, stage_callback=stage_callback, **kwargs)

    pipeline.run = run_with_stage  # type: ignore[method-assign]

    worker = ProcessingWorker(
        storage=storage,
        repository=repository,
        pipelines=FakePipelineProvider(pipeline),
    )
    worker_result = await worker.run(upload_contract["jobId"], "user-1")

    assert worker_result.document_id == upload_contract["documentId"]
    assert repository.jobs[upload_contract["jobId"]]["status"] == "complete"
    assert stage_events == [
        ("ingestion", 10),
        ("normalization", 20),
        ("extraction", 35),
        ("resolution", 50),
        ("relationships", 62),
        ("temporal", 72),
        ("provenance", 82),
        ("mapping", 92),
        ("memory", 98),
    ]
    assert worker_result.pipeline.memory_id == "memory-1"
    assert worker_result.pipeline.memory.sources
    assert worker_result.pipeline.memory.sources[0].document_id == upload_contract["documentId"]
    assert "2024" in str(worker_result.pipeline.temporal.events) or "2024" in source

    retrieval = RetrievalService(memory)
    query = UserQuery(user_id="user-1", query="What did Alice start in 2024?")
    context = retrieval.retrieve(query)

    assert context.memories
    assert context.source_references
    assert context.provenance
    assert any(entity.get("name") == "Alice" for entity in context.entities)
    assert any(source_ref.get("document_id") == upload_contract["documentId"] for source_ref in context.source_references)

    openclaw = FakeOpenClaw()
    response = OpenClawAgent(openclaw).run(build_agent_request(query, context))
    assert response.answer
    assert openclaw.contexts == [context]

    revival_runtime = FakeRevival()
    revival_request = build_revival_request(
        "Find an abandoned idea I could revisit now.",
        memories=context.memories,
        entities=context.entities,
        relationships=context.relationships,
        temporal_context=context.timeline,
        source_evidence=context.source_references,
    )
    candidate = RevivalEngine(revival_runtime).generate(revival_request)

    assert revival_runtime.requests == [revival_request]
    assert candidate.source_references == context.source_references
    assert "Build a small prototype." not in candidate.source_facts
    assert "Build a small prototype." in candidate.creative_suggestions
    assert all(
        upload_contract["documentId"] == source_ref.get("document_id")
        for source_ref in candidate.source_references
    )
