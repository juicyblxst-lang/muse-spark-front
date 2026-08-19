from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from fastapi import Depends, HTTPException, Request, status

from app.core.auth import require_supabase_client

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md"}


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str


async def require_current_user(supabase=Depends(require_supabase_client)) -> AuthenticatedUser:
    response = supabase.auth.get_user()
    user = getattr(response, "user", None)
    user_id = getattr(user, "id", None)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired Supabase session.")
    return AuthenticatedUser(user_id=str(user_id))


def require_owner(resource_user_id: str, current_user: AuthenticatedUser) -> None:
    if resource_user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")


def validate_upload_metadata(filename: str, content_length: int | None) -> None:
    safe_name = Path(filename or "").name
    extension = Path(safe_name).suffix.lower()
    if not safe_name or safe_name != filename or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported or invalid file name.")
    if content_length is not None and content_length > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Request exceeds the upload limit.")


class RateLimitHook(Protocol):
    def check(self, *, user_id: str, route: str) -> None: ...


class NoopRateLimitHook:
    """Extension point for Redis/gateway-backed rate limiting in deployment."""

    def check(self, *, user_id: str, route: str) -> None:
        return None


rate_limit_hook: RateLimitHook = NoopRateLimitHook()


def enforce_rate_limit(request: Request, current_user: AuthenticatedUser = Depends(require_current_user)) -> AuthenticatedUser:
    rate_limit_hook.check(user_id=current_user.user_id, route=request.url.path)
    return current_user
