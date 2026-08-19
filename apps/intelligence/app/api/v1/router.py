from fastapi import APIRouter

from app.api.v1.processing import router as processing_router
from app.api.v1.uploads import router as uploads_router

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
async def api_health() -> dict[str, str]:
    return {"status": "ok", "api": "v1"}


api_router.include_router(uploads_router)
api_router.include_router(processing_router)
