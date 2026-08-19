from __future__ import annotations

import asyncio
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from app.services.system_pipeline import MuseComponentPipeline, PipelineRun


class ProcessingStorage(Protocol):
    def download(self, storage_path: str) -> bytes: ...


class ProcessingRepository(Protocol):
    def get_job(self, job_id: str, user_id: str) -> dict[str, Any] | None: ...
    def get_document(self, document_id: str, user_id: str) -> dict[str, Any] | None: ...
    def update_job(self, job_id: str, user_id: str, values: dict[str, Any]) -> None: ...


class PipelineProvider(Protocol):
    def build(self, user_id: str) -> MuseComponentPipeline: ...


@dataclass(frozen=True)
class ProcessingRunResult:
    job_id: str
    document_id: str
    pipeline: PipelineRun


class ProcessingWorker:
    """Execute one queued job against the real component pipeline."""

    def __init__(self, *, storage: ProcessingStorage, repository: ProcessingRepository, pipelines: PipelineProvider) -> None:
        self.storage = storage
        self.repository = repository
        self.pipelines = pipelines

    async def run(self, job_id: str, user_id: str) -> ProcessingRunResult:
        job = self.repository.get_job(job_id, user_id)
        if job is None:
            raise LookupError("processing job not found")
        document_id = str(job["document_id"])
        document = self.repository.get_document(document_id, user_id)
        if document is None:
            raise LookupError("document not found")

        self._update(job_id, user_id, status="processing", progress=0, current_stage="ingestion", error=None)
        filename = Path(str(document["file_name"])).name
        storage_path = f"{user_id}/{document_id}/{filename}"
        try:
            payload = await asyncio.to_thread(self.storage.download, storage_path)
            with tempfile.TemporaryDirectory(prefix="muse-processing-") as temp_dir:
                source = Path(temp_dir) / filename
                source.write_bytes(payload)
                pipeline = self.pipelines.build(user_id)

                async def stage(stage_name: str, progress: int) -> None:
                    self._update(job_id, user_id, status="processing", progress=progress, current_stage=stage_name)

                result = await pipeline.run(
                    str(source),
                    user_id=user_id,
                    document_id=document_id,
                    document_version=str(document.get("version", "1")),
                    stage_callback=stage,
                )

            self._update(
                job_id,
                user_id,
                status="complete",
                progress=100,
                current_stage="memory",
                completed_at=datetime.now(timezone.utc).isoformat(),
                error=None,
                discovered={
                    "memories": 1,
                    "entities": len(result.knowledge.entities),
                    "relationships": len(result.relationships.relationships),
                    "timelineEvents": len(result.temporal.events),
                    "highlights": [],
                },
            )
            return ProcessingRunResult(job_id=job_id, document_id=document_id, pipeline=result)
        except Exception as exc:
            self._update(job_id, user_id, status="failed", completed_at=datetime.now(timezone.utc).isoformat(), error=str(exc))
            raise

    def _update(self, job_id: str, user_id: str, **values: Any) -> None:
        self.repository.update_job(job_id, user_id, values)
