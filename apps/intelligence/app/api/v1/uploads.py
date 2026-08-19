from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from supabase import Client
from app.core.auth import require_supabase_client

router = APIRouter(prefix="/uploads", tags=["uploads"])
BUCKET = "muse-documents"
MAX_BYTES = 50 * 1024 * 1024
ALLOWED_TYPES = {".pdf": "application/pdf", ".doc": "application/msword", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".txt": "text/plain", ".md": "text/markdown"}

def extension_for(filename: str) -> str:
    return Path(filename).suffix.lower()

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), supabase: Client = Depends(require_supabase_client)) -> dict:
    filename = Path(file.filename or "document").name
    extension = extension_for(filename)
    if extension not in ALLOWED_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type. Supported formats: PDF, DOC, DOCX, TXT, Markdown.")
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 50 MB limit.")

    user_response = supabase.auth.get_user()
    user = getattr(user_response, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired Supabase session.")

    document_result = supabase.table("documents").insert({
        "user_id": user.id,
        "title": Path(filename).stem or "Untitled document",
        "file_name": filename,
        "kind": extension.lstrip("."),
        "status": "queued",
        "size_bytes": len(data),
    }).execute()
    if not document_result.data:
        raise HTTPException(status_code=500, detail="Failed to create document record.")

    document = document_result.data[0]
    document_id = UUID(document["id"])
    storage_path = f"{user.id}/{document_id}/{filename}"
    try:
        supabase.storage.from_(BUCKET).upload(storage_path, data, {"content-type": file.content_type or ALLOWED_TYPES[extension], "upsert": "false"})
        job_result = supabase.table("processing_jobs").insert({
            "user_id": user.id,
            "document_id": str(document_id),
            "status": "queued",
            "progress": 0,
            "current_stage": "queued",
        }).execute()
        if not job_result.data:
            raise RuntimeError("Failed to create processing job.")
    except Exception as exc:
        supabase.table("documents").delete().eq("id", str(document_id)).execute()
        raise HTTPException(status_code=500, detail="Upload could not be completed.") from exc

    job = job_result.data[0]
    return {"documentId": str(document_id), "jobId": str(job["id"]), "storagePath": storage_path}
