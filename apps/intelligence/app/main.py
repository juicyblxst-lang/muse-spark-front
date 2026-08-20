from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .storage import SQLiteStore
import os

app = FastAPI(title="Muse Intelligence", version="0.1.0")

allowed_origins = [origin.strip() for origin in os.getenv("MUSE_CORS_ORIGINS", "").split(",") if origin.strip()]
if allowed_origins:
    app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "muse-intelligence"}

@app.get("/ready")
async def readiness() -> dict[str, str]:
    database_path = os.getenv("MUSE_DATABASE_PATH")
    if not database_path:
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "MUSE_DATABASE_PATH is not configured"})
    SQLiteStore(database_path)
    return {"status": "ready", "database": "configured"}

@app.get("/api/v1/auth/me")
async def current_user():
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is not configured")

def not_ready(feature: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=f"Muse {feature} API is not configured")

@app.get("/api/v1/dashboard")
async def dashboard():
    not_ready("dashboard")

@app.get("/api/v1/documents")
async def documents():
    not_ready("document")

@app.post("/api/v1/documents/uploads")
async def create_upload():
    not_ready("upload")

@app.get("/api/v1/memories/forgotten")
async def forgotten_memories():
    not_ready("memory")
