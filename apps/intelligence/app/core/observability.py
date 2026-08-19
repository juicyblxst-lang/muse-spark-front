from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any, Protocol


_RESERVED = {"message", "request_id", "job_id", "document_id", "user_id", "stage", "status", "duration", "error"}
_SENSITIVE_KEYS = {"authorization", "token", "access_token", "refresh_token", "api_key", "secret", "password", "service_role_key", "source_text", "document_text", "raw_document"}


@dataclass(frozen=True)
class ProcessingLog:
    request_id: str
    job_id: str
    document_id: str
    user_id: str
    stage: str
    status: str
    duration: float
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ObservabilityLogger(Protocol):
    def processing(self, event: ProcessingLog) -> None: ...


class StructuredLogger:
    def __init__(self, name: str = "muse") -> None:
        self._logger = logging.getLogger(name)

    def processing(self, event: ProcessingLog) -> None:
        payload = event.to_dict()
        self._logger.info(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))

    def event(self, message: str, **fields: Any) -> None:
        safe = {key: _sanitize(key, value) for key, value in fields.items() if key not in _RESERVED}
        payload = {"message": message, **safe}
        self._logger.info(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))


def _sanitize(key: str, value: Any) -> Any:
    normalized = key.lower()
    if any(secret in normalized for secret in _SENSITIVE_KEYS):
        return "[REDACTED]"
    if normalized.endswith("headers") and isinstance(value, dict):
        return {k: ("[REDACTED]" if k.lower() == "authorization" else v) for k, v in value.items()}
    return value


logger: ObservabilityLogger = StructuredLogger()


def timed_processing(
    *,
    request_id: str,
    job_id: str,
    document_id: str,
    user_id: str,
    stage: str,
    log: ObservabilityLogger = logger,
):
    start = time.perf_counter()

    def emit(status: str, error: str | None = None) -> ProcessingLog:
        event = ProcessingLog(
            request_id=request_id,
            job_id=job_id,
            document_id=document_id,
            user_id=user_id,
            stage=stage,
            status=status,
            duration=time.perf_counter() - start,
            error=error,
        )
        log.processing(event)
        return event

    return emit
