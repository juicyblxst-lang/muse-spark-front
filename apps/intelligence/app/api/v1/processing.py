from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.core.auth import require_supabase_client
from app.services.orchestrator import ProcessingOrchestrator

router = APIRouter(prefix="/processing", tags=["processing"])

@router.get("/{job_id}")
async def get_processing_job(job_id: UUID, supabase: Client = Depends(require_supabase_client)) -> dict:
    user_response = supabase.auth.get_user()
    user = getattr(user_response, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired Supabase session.")
    result = supabase.table("processing_jobs").select("*").eq("id", str(job_id)).eq("user_id", user.id).maybe_single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Processing job not found.")
    job = result.data
    raw_stage = job.get("current_stage", "uploading")
    current_stage = "uploading" if raw_stage == "queued" else raw_stage
    return {
        "id": str(job["id"]),
        "documentId": str(job["document_id"]),
        "documentTitle": job.get("document_title") or "",
        "status": "running" if job.get("status") == "processing" else job.get("status", "queued"),
        "progress": job.get("progress", 0),
        "currentStage": current_stage,
        "stages": job.get("stages", []),
        "startedAt": job.get("started_at") or job.get("created_at"),
        "completedAt": job.get("completed_at"),
        "error": job.get("error"),
        "discovered": job.get("discovered", {"memories": 0, "entities": 0, "relationships": 0, "timelineEvents": 0, "highlights": []}),
    }

@router.post("/{document_id}/preview")
async def preview_pipeline(document_id: UUID) -> dict:
    result = await ProcessingOrchestrator().run()
    return {"document_id": str(document_id), "status": result.status, "stages": [{"stage": item.stage.value, "status": item.status, "detail": item.detail} for item in result.stages]}
