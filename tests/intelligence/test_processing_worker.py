from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from app.services.processing_worker import ProcessingWorker


@dataclass
class FakeStorage:
    payload: bytes = b"hello"
    paths: list[str] | None = None

    def download(self, storage_path: str) -> bytes:
        if self.paths is None:
            self.paths = []
        self.paths.append(storage_path)
        return self.payload


class FakeRepository:
    def __init__(self) -> None:
        self.job = {
            "id": "job-1",
            "document_id": "doc-1",
        }
        self.document = {
            "id": "doc-1",
            "file_name": "sample.md",
            "version": 3,
        }
        self.updates: list[tuple[str, str, dict]] = []

    def get_job(self, job_id: str, user_id: str):
        assert user_id == "user-1"
        return self.job if job_id == "job-1" else None

    def get_document(self, document_id: str, user_id: str):
        assert user_id == "user-1"
        return self.document if document_id == "doc-1" else None

    def update_job(self, job_id: str, user_id: str, values: dict) -> None:
        self.updates.append((job_id, user_id, values))


class FakePipeline:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def run(self, source_path: str, **kwargs):
        self.calls.append({"source_path": source_path, **kwargs})
        assert Path(source_path).read_bytes() == b"hello"
        assert kwargs == {
            "user_id": "user-1",
            "document_id": "doc-1",
            "document_version": "3",
            "stage_callback": kwargs["stage_callback"],
        }
        return type("Result", (), {
            "knowledge": type("Knowledge", (), {"entities": [{"id": "alice"}]})(),
            "relationships": type("Relationships", (), {"relationships": [{"id": "r1"}]})(),
            "temporal": type("Temporal", (), {"events": [{"id": "t1"}]})(),
        })()


class FakePipelines:
    def __init__(self, pipeline: FakePipeline) -> None:
        self.pipeline = pipeline
        self.user_ids: list[str] = []

    def build(self, user_id: str):
        self.user_ids.append(user_id)
        return self.pipeline


@pytest.mark.asyncio
async def test_worker_downloads_runs_pipeline_and_completes_job():
    repository = FakeRepository()
    storage = FakeStorage()
    pipeline = FakePipeline()
    providers = FakePipelines(pipeline)
    worker = ProcessingWorker(storage=storage, repository=repository, pipelines=providers)

    result = await worker.run("job-1", "user-1")

    assert result.job_id == "job-1"
    assert result.document_id == "doc-1"
    assert storage.paths == ["user-1/doc-1/sample.md"]
    assert providers.user_ids == ["user-1"]
    assert len(pipeline.calls) == 1
    assert repository.updates[0][2]["status"] == "processing"
    assert repository.updates[-1][2]["status"] == "complete"
    assert repository.updates[-1][2]["progress"] == 100
    assert repository.updates[-1][2]["current_stage"] == "memory"
    assert repository.updates[-1][2]["discovered"] == {
        "memories": 1,
        "entities": 1,
        "relationships": 1,
        "timelineEvents": 1,
        "highlights": [],
    }


@pytest.mark.asyncio
async def test_worker_marks_job_failed_when_pipeline_raises():
    repository = FakeRepository()
    storage = FakeStorage()

    class FailingPipeline:
        async def run(self, source_path: str, **kwargs):
            raise RuntimeError("pipeline exploded")

    class Provider:
        def build(self, user_id: str):
            return FailingPipeline()

    worker = ProcessingWorker(storage=storage, repository=repository, pipelines=Provider())

    with pytest.raises(RuntimeError, match="pipeline exploded"):
        await worker.run("job-1", "user-1")

    assert repository.updates[-1][2]["status"] == "failed"
    assert repository.updates[-1][2]["error"] == "pipeline exploded"


def test_worker_rejects_unknown_job():
    repository = FakeRepository()
    storage = FakeStorage()

    class Provider:
        def build(self, user_id: str):
            raise AssertionError("pipeline must not be built")

    worker = ProcessingWorker(storage=storage, repository=repository, pipelines=Provider())

    import asyncio

    with pytest.raises(LookupError, match="processing job not found"):
        asyncio.run(worker.run("missing", "user-1"))
