from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import Client

from app.core.auth import require_supabase_client
from app.core.config import settings
from app.memory.sibyl_client import SibylMemoryService
from app.services.retrieval import RetrievalService, UserQuery

router = APIRouter(prefix="/memories", tags=["memories"])


class MemorySearchRequest(BaseModel):
    query: str = Field(min_length=1)
    page: int = Field(default=1, ge=1)
    pageSize: int = Field(default=20, ge=1, le=100)


def _memory_service() -> SibylMemoryService:
    return SibylMemoryService(settings.sibyl_db_path)


@router.post("/search")
async def search_memories(
    request: MemorySearchRequest,
    supabase: Client = Depends(require_supabase_client),
) -> dict:
    user_response = supabase.auth.get_user()
    user = getattr(user_response, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired Supabase session.")

    context = RetrievalService(_memory_service()).retrieve(
        UserQuery(user_id=str(user.id), query=request.query, limit=request.pageSize)
    )
    results = []
    for index, memory in enumerate(context.memories):
        item = memory if isinstance(memory, dict) else {"value": memory}
        results.append({
            "memory": item,
            "score": max(0.0, 1.0 - index * 0.01),
            "matchedTerms": request.query.split(),
            "reason": "Retrieved from the user's Muse memory store.",
        })

    return {
        "items": results,
        "total": len(results),
        "page": request.page,
        "pageSize": request.pageSize,
        "hasMore": False,
        "query": context.query,
        "suggestions": [],
    }
