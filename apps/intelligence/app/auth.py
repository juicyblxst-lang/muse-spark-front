from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

ACCESS_COOKIE = "muse_access_token"
REFRESH_COOKIE = "muse_refresh_token"

class AuthRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3)
    password: str = Field(min_length=6)

class SignUpRequest(AuthRequest):
    displayName: str = Field(min_length=1, max_length=200)

class User(BaseModel):
    id: str
    email: str
    displayName: str
    avatarUrl: str | None = None
    createdAt: str

class Session(BaseModel):
    token: str
    expiresAt: str
    user: User

def _settings() -> tuple[str, str]:
    import os
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    if not url or not key:
        raise HTTPException(status_code=503, detail="Supabase authentication is not configured.")
    return url, key

def _secure() -> bool:
    import os
    value = os.getenv("MUSE_COOKIE_SECURE")
    if value is not None:
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return os.getenv("ENVIRONMENT", "development").lower() == "production"

def _cookie_options() -> dict[str, Any]:
    secure = _secure()
    return {"httponly": True, "secure": secure, "samesite": "none" if secure else "lax", "path": "/"}

def _set_cookies(response: Response, payload: dict[str, Any]) -> None:
    access = payload.get("access_token")
    refresh = payload.get("refresh_token")
    if not access or not refresh:
        raise HTTPException(status_code=502, detail="Supabase did not return a complete session.")
    options = _cookie_options()
    response.set_cookie(ACCESS_COOKIE, str(access), max_age=int(payload.get("expires_in") or 3600), **options)
    response.set_cookie(REFRESH_COOKIE, str(refresh), **options)

def _clear_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")

def _user(payload: dict[str, Any]) -> User:
    metadata = payload.get("user_metadata") or payload.get("raw_user_meta_data") or {}
    email = str(payload.get("email") or "")
    display = metadata.get("displayName") or metadata.get("full_name") or (email.split("@", 1)[0] if email else "Muse user")
    return User(id=str(payload["id"]), email=email, displayName=str(display), avatarUrl=metadata.get("avatar_url"), createdAt=str(payload.get("created_at") or datetime.now(timezone.utc).isoformat()))

def _session(payload: dict[str, Any]) -> Session:
    if not payload.get("access_token") or not isinstance(payload.get("user"), dict):
        raise HTTPException(status_code=502, detail="Supabase did not return a complete session.")
    expires = payload.get("expires_at")
    if expires is None:
        expires = int(datetime.now(timezone.utc).timestamp()) + int(payload.get("expires_in") or 3600)
    return Session(token=str(payload["access_token"]), expiresAt=datetime.fromtimestamp(int(expires), timezone.utc).isoformat(), user=_user(payload["user"]))

async def _request(method: str, path: str, *, token: str | None = None, query: dict[str, str] | None = None, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    base, key = _settings()
    headers = {"apikey": key, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(method, f"{base}/auth/v1{path}", headers=headers, params=query, json=body)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Unable to reach Supabase Auth.") from exc
    try:
        payload = response.json() if response.content else {}
    except ValueError:
        payload = {}
    return response.status_code, payload if isinstance(payload, dict) else {}

async def sign_in(request: AuthRequest, response: Response) -> Session:
    code, payload = await _request("POST", "/token", query={"grant_type": "password"}, body={"email": request.email.strip(), "password": request.password})
    if code >= 400:
        raise HTTPException(status_code=401 if code in {400, 401} else 502, detail=str(payload.get("msg") or payload.get("error_description") or payload.get("message") or "Invalid email or password."))
    session = _session(payload)
    _set_cookies(response, payload)
    return session

async def sign_up(request: SignUpRequest, response: Response) -> Session:
    code, payload = await _request("POST", "/signup", body={"email": request.email.strip(), "password": request.password, "data": {"displayName": request.displayName.strip()}})
    if code >= 400:
        raise HTTPException(status_code=400 if code < 500 else 502, detail=str(payload.get("msg") or payload.get("error_description") or payload.get("message") or "Unable to create account."))
    if not payload.get("access_token") or not payload.get("refresh_token"):
        raise HTTPException(status_code=409, detail="Account created. Confirm your email address, then sign in.")
    session = _session(payload)
    _set_cookies(response, payload)
    return session

async def _refresh(refresh_token: str, response: Response) -> Session | None:
    code, payload = await _request("POST", "/token", query={"grant_type": "refresh_token"}, body={"refresh_token": refresh_token})
    if code >= 400 or not payload.get("access_token") or not payload.get("refresh_token"):
        return None
    session = _session(payload)
    _set_cookies(response, payload)
    return session

async def current_user(request: Request, response: Response) -> User:
    access = request.cookies.get(ACCESS_COOKIE)
    refresh = request.cookies.get(REFRESH_COOKIE)
    if access:
        code, payload = await _request("GET", "/user", token=access)
        if code < 400 and payload.get("id"):
            return _user(payload)
    if refresh:
        session = await _refresh(refresh, response)
        if session is not None:
            return session.user
    _clear_cookies(response)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.", headers={"WWW-Authenticate": "Cookie"})

async def sign_out(request: Request, response: Response) -> None:
    access = request.cookies.get(ACCESS_COOKIE)
    if access:
        await _request("POST", "/logout", token=access)
    _clear_cookies(response)
