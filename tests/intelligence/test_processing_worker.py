from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.processing_worker import ProcessingWorker


class FakeStorage:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.paths: list[str] = []

    def download(self, storage_path: str) -> bytes:
        self.paths.append(storage_path)
        return self.payload


class FakeRepository:
    def __init__(self):
        self.updates: list[tuple[str, str, dict]] = []

    def get_job(self, job_id: str, user_id: str):
        return {"id": job_id, "document_id": "doc-1"}

    def get_document(self, document_id: str, user_id: str):
        return {"id": document_id, "file_name": "sample.md", "version": 3}

    def update_job(self, job_id: str, user_id: str, values: dict) -> None:
        self.updates.append((job_id, user_id, values))


class FakePipeline:
    async def run(self, source_path: str, **kwargs):
        assert source_path.endswith("/sample.md")
        assert kwargs["user_id"] == "user-1"
        assert kwargs["document_id"] == "doc-1"
        callback = kwargs["stage_callback"]
        await callback("ingestion", 10)
        await callback("memory", 98)
        return SimpleNamespace(
            knowledge=SimpleNamespace(entities=[{"name": "Alice"}]),
            relationships=SimpleNamespace(relationships=[1, 2]),
            temporal=SimpleNamespace(events=[1]),
            memory_id="memory-1",
        )


class FakeProvider:
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.users: list[str] = []

    def build(self, user_id: str):
        self.users.append(user_id)
        return self.pipeline


@pytest.mark.asyncio
async def test_worker_downloads_document_runs_pipeline_and_updates_job():
    storage = FakeStorage(b"sample document")
    repository = FakeRepository()
    provider = FakeProvider(FakePipeline())
    worker = ProcessingWorker(storage=storage, repository=repository, pipelines=provider)

    result = await worker.run("job-1", "user-1")

    assert result.job_id == "job-1"
    assert result.document_id == "doc-1"
    assert storage.paths == ["user-1/doc-1/sample.md"]
    assert provider.users == ["user-1"]
    assert any(update[2]["current_stage"] == "ingestion" for update in repository.updates)
    complete = repository.updates[-1][2]
    assert complete["status"] == "complete"
    assert complete["progress"] == 100
    assert complete["discovered"] == {
        "memories": 1,
        "entities": 1,
        "relationships": 2,
        "timelineEvents": 1,
        "highlights": [],
    }
