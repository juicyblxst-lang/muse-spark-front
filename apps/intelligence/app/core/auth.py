from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from app.core.config import settings

security = HTTPBearer(auto_error=False)


def get_supabase_client(token: str) -> Client:
    if not settings.supabase_url or not settings.supabase_publishable_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured.",
        )
    client = create_client(settings.supabase_url, settings.supabase_publishable_key)
    client.auth.set_session(access_token=token, refresh_token="")
    return client


async def require_supabase_client(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> Client:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A Supabase access token is required.",
        )
    return get_supabase_client(credentials.credentials)
