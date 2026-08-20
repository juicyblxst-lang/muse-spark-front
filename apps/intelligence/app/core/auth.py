from fastapi import Depends, HTTPException, Request, Response, status
from supabase import Client, create_client

from app.auth import ACCESS_COOKIE, REFRESH_COOKIE, User, current_user
from app.core.config import settings


async def require_current_user(request: Request, response: Response) -> User:
    return await current_user(request, response)


async def require_supabase_client(request: Request) -> Client:
    access_token = request.cookies.get(ACCESS_COOKIE)
    refresh_token = request.cookies.get(REFRESH_COOKIE, "")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Cookie"},
        )

    if not settings.supabase_url or not settings.supabase_publishable_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured.",
        )

    client = create_client(settings.supabase_url, settings.supabase_publishable_key)
    client.auth.set_session(access_token=access_token, refresh_token=refresh_token)

    user_response = client.auth.get_user()
    user = getattr(user_response, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Supabase session.",
            headers={"WWW-Authenticate": "Cookie"},
        )

    return client
