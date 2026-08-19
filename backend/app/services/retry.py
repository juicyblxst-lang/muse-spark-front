from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol

from app.services.processing_state import ProcessingJob, ProcessingStatus, ProcessingStateService


class ErrorClass(str, Enum):
    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    VALIDATION = "VALIDATION"


@dataclass(frozen=True)
class ProcessingAttempt:
    attempt: int
    error_class: ErrorClass | None = None
    error: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class AttemptStore(Protocol):
    def append(self, job_id: str, attempt: ProcessingAttempt) -> None: ...
    def list_for_job(self, job_id: str) -> list[ProcessingAttempt]: ...


class InMemoryAttemptStore:
    def __init__(self) -> None:
        self._attempts: dict[str, list[ProcessingAttempt]] = {}

    def append(self, job_id: str, attempt: ProcessingAttempt) -> None:
        self._attempts.setdefault(job_id, []).append(attempt)

    def list_for_job(self, job_id: str) -> list[ProcessingAttempt]:
        return list(self._attempts.get(job_id, []))


class RetryService:
    MAX_ATTEMPTS = 3

    def __init__(self, state: ProcessingStateService, attempts: AttemptStore) -> None:
        self._state = state
        self._attempts = attempts

    def record_failure(
        self,
        job_id: str,
        user_id: str,
        error: str,
        error_class: ErrorClass,
    ) -> ProcessingJob:
        if not error.strip():
            raise ValueError("error is required")
        job = self._state.get_status(job_id, user_id)
        if job.status != ProcessingStatus.PROCESSING:
            raise ValueError("job must be processing")

        attempt = ProcessingAttempt(
            attempt=job.attempt,
            error_class=error_class,
            error=error,
            completed_at=datetime.now(timezone.utc),
        )
        self._attempts.append(job_id, attempt)

        # Validation and permanent failures never auto-retry.
        if error_class in {ErrorClass.VALIDATION, ErrorClass.PERMANENT}:
            return self._state.fail(job_id, user_id, error)

        # Transient failure: only retry while another bounded attempt remains.
        if error_class == ErrorClass.TRANSIENT and job.attempt < self.MAX_ATTEMPTS:
            return self._state.fail(job_id, user_id, error)

        return self._state.fail(job_id, user_id, error)

    def retry(self, job_id: str, user_id: str) -> ProcessingJob:
        job = self._state.get_status(job_id, user_id)
        if job.status != ProcessingStatus.FAILED:
            raise ValueError("only failed jobs can be explicitly retried")
        if job.attempt >= self.MAX_ATTEMPTS:
            raise ValueError("maximum retry attempts reached")
        return self._state.start(job_id, user_id)

    def attempts_for(self, job_id: str) -> list[ProcessingAttempt]:
        return self._attempts.list_for_job(job_id)
