from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.memory.sibyl_client import SibylMemoryService

app = FastAPI(
    title="Muse API",
    version=settings.api_version,
    description="HTTP/API foundation for Muse. Domain intelligence remains outside this layer.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "muse-api", "version": settings.api_version}


@app.get("/ready", tags=["health"])
async def ready() -> dict[str, str]:
    """Production readiness: verify the configured persistent Sibyl store opens."""
    try:
        SibylMemoryService(settings.sibyl_db_path).check_ready()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Muse memory store is not ready: {type(exc).__name__}") from exc
    return {"status": "ready", "service": "muse-api", "version": settings.api_version}
