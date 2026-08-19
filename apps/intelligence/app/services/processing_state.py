from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol


class ProcessingStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class ProcessingStage(str, Enum):
    INGESTION = "ingestion"
    NORMALIZATION = "normalization"
    EXTRACTION = "extraction"
    RESOLUTION = "resolution"
    RELATIONSHIPS = "relationships"
    TEMPORAL = "temporal"
    PROVENANCE = "provenance"
    MAPPING = "mapping"
    MEMORY = "memory"


@dataclass(frozen=True)
class ProcessingJob:
    job_id: str
    document_id: str
    user_id: str
    status: ProcessingStatus = ProcessingStatus.QUEUED
    current_stage: ProcessingStage | None = None
    progress: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    attempt: int = 0


class ProcessingJobStore(Protocol):
    def save(self, job: ProcessingJob) -> ProcessingJob: ...
    def get(self, job_id: str, user_id: str) -> ProcessingJob | None: ...


class InMemoryProcessingJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, ProcessingJob] = {}

    def save(self, job: ProcessingJob) -> ProcessingJob:
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str, user_id: str) -> ProcessingJob | None:
        job = self._jobs.get(job_id)
        if job is None or job.user_id != user_id:
            return None
        return job


class ProcessingStateService:
    def __init__(self, store: ProcessingJobStore) -> None:
        self._store = store

    def create_job(self, *, job_id: str, document_id: str, user_id: str) -> ProcessingJob:
        self._require_ids(job_id, document_id, user_id)
        return self._store.save(
            ProcessingJob(job_id=job_id, document_id=document_id, user_id=user_id)
        )

    def start(self, job_id: str, user_id: str) -> ProcessingJob:
        job = self._owned(job_id, user_id)
        if job.status not in {ProcessingStatus.QUEUED, ProcessingStatus.FAILED}:
            raise ValueError("only queued or failed jobs can start")
        now = datetime.now(timezone.utc)
        return self._store.save(replace(
            job,
            status=ProcessingStatus.PROCESSING,
            started_at=now,
            completed_at=None,
            error=None,
            attempt=job.attempt + 1,
        ))

    def update_stage(self, job_id: str, user_id: str, stage: ProcessingStage, progress: int) -> ProcessingJob:
        job = self._owned(job_id, user_id)
        if job.status != ProcessingStatus.PROCESSING:
            raise ValueError("job must be processing before updating a stage")
        if not 0 <= progress <= 100:
            raise ValueError("progress must be between 0 and 100")
        return self._store.save(replace(job, current_stage=stage, progress=progress))

    def complete(self, job_id: str, user_id: str) -> ProcessingJob:
        job = self._owned(job_id, user_id)
        if job.status != ProcessingStatus.PROCESSING:
            raise ValueError("only processing jobs can complete")
        return self._store.save(replace(
            job,
            status=ProcessingStatus.COMPLETE,
            progress=100,
            completed_at=datetime.now(timezone.utc),
            error=None,
        ))

    def fail(self, job_id: str, user_id: str, error: str) -> ProcessingJob:
        job = self._owned(job_id, user_id)
        if job.status != ProcessingStatus.PROCESSING:
            raise ValueError("only processing jobs can fail")
        if not error.strip():
            raise ValueError("error is required")
        return self._store.save(replace(
            job,
            status=ProcessingStatus.FAILED,
            completed_at=datetime.now(timezone.utc),
            error=error,
        ))

    def get_status(self, job_id: str, user_id: str) -> ProcessingJob:
        return self._owned(job_id, user_id)

    def _owned(self, job_id: str, user_id: str) -> ProcessingJob:
        self._require_ids(job_id, user_id)
        job = self._store.get(job_id, user_id)
        if job is None:
            raise LookupError("processing job not found")
        return job

    @staticmethod
    def _require_ids(*values: str) -> None:
        if any(not value.strip() for value in values):
            raise ValueError("job_id, document_id, and user_id are required")
