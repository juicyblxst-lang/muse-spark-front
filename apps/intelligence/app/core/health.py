from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import APIRouter, HTTPException, status

from app.core.config import Settings, get_settings
from app.memory.storage import verify_memory_store


@dataclass(frozen=True)
class DependencyCheck:
    name: str
    ok: bool
    error: str | None = None


def check_supabase(settings: Settings) -> DependencyCheck:
    if not settings.supabase_url or not settings.supabase_publishable_key:
        return DependencyCheck("supabase", False, "Supabase configuration is missing")
    return DependencyCheck("supabase", True)


def check_sibyl(settings: Settings) -> DependencyCheck:
    try:
        verify_memory_store(settings.sibyl_db_path)
        return DependencyCheck("sibyl", True)
    except Exception as exc:
        return DependencyCheck("sibyl", False, str(exc))


def check_configuration(settings: Settings) -> DependencyCheck:
    try:
        if settings.max_upload_bytes <= 0 or settings.max_processing_attempts <= 0:
            raise ValueError("invalid processing limits")
        if not settings.sibyl_db_path:
            raise ValueError("Sibyl database path is missing")
        if not settings.storage_bucket:
            raise ValueError("storage bucket is missing")
        if settings.environment == "production":
            # Constructing Settings is the authoritative production validation.
            Settings(**settings.model_dump())
        return DependencyCheck("configuration", True)
    except Exception as exc:
        return DependencyCheck("configuration", False, str(exc))


def check_llm(settings: Settings) -> DependencyCheck:
    if settings.environment != "production":
        return DependencyCheck("llm", True)
    if not settings.llm_api_key or not settings.llm_model:
        return DependencyCheck("llm", False, "LLM configuration is missing")
    return DependencyCheck("llm", True)


class HealthService:
    def __init__(self, settings: Settings | None = None, checks: tuple[Callable[[Settings], DependencyCheck], ...] | None = None) -> None:
        self.settings = settings or get_settings()
        self.checks = checks or (check_supabase, check_sibyl, check_configuration, check_llm)

    def health(self) -> dict[str, str]:
        return {"status": "ok"}

    def ready(self) -> tuple[dict[str, object], int]:
        results = [check(self.settings) for check in self.checks]
        failed = [result for result in results if not result.ok]
        body = {
            "status": "ready" if not failed else "not_ready",
            "dependencies": {
                result.name: {"ok": result.ok, **({"error": result.error} if result.error else {})}
                for result in results
            },
        }
        return body, status.HTTP_200_OK if not failed else status.HTTP_503_SERVICE_UNAVAILABLE


router = APIRouter(tags=["health"])
_service = HealthService()


@router.get("/health")
def health() -> dict[str, str]:
    return _service.health()


@router.get("/ready")
def ready() -> dict[str, object]:
    body, code = _service.ready()
    if code != status.HTTP_200_OK:
        raise HTTPException(status_code=code, detail=body)
    return body
