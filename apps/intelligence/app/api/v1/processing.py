from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.services.orchestrator import ProcessingOrchestrator

router = APIRouter(prefix="/processing", tags=["processing"])


@router.post("/{document_id}/preview")
async def preview_pipeline(document_id: UUID) -> dict:
    """Return the pipeline contract without executing intelligence stages."""
    result = await ProcessingOrchestrator().run()
    return {
        "document_id": str(document_id),
        "status": result.status,
        "stages": [
            {"stage": item.stage.value, "status": item.status, "detail": item.detail}
            for item in result.stages
        ],
    }
