from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth import router

app = FastAPI()
app.include_router(router, prefix="/api/v1")


def test_auth_me_requires_a_session():
    response = TestClient(app).get("/api/v1/auth/me")
    assert response.status_code == 401


def test_auth_sign_in_sets_httponly_session_cookies():
    payload = {"access_token": "access-test", "refresh_token": "refresh-test", "expires_in": 3600, "user": {"id": "user-1", "email": "alice@example.com", "user_metadata": {"displayName": "Alice"}, "created_at": "2026-01-01T00:00:00Z"}}
    with patch("app.auth._request", new=AsyncMock(return_value=(200, payload))):
        response = TestClient(app).post("/api/v1/auth/sign-in", json={"email": "alice@example.com", "password": "secret123"})
    assert response.status_code == 200
    assert response.json()["user"]["id"] == "user-1"
    cookies = response.headers.get_list("set-cookie")
    assert any("muse_access_token=access-test" in value and "HttpOnly" in value for value in cookies)
    assert any("muse_refresh_token=refresh-test" in value and "HttpOnly" in value for value in cookies)


def test_auth_sign_up_does_not_fabricate_session_when_confirmation_required():
    payload = {"user": {"id": "user-2", "email": "bob@example.com", "user_metadata": {"displayName": "Bob"}}}
    with patch("app.auth._request", new=AsyncMock(return_value=(200, payload))):
        response = TestClient(app).post("/api/v1/auth/sign-up", json={"email": "bob@example.com", "password": "secret123", "displayName": "Bob"})
    assert response.status_code == 409
    assert "Confirm your email" in response.json()["detail"]


def test_auth_me_refreshes_an_expired_access_token():
    refreshed = {"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": 3600, "user": {"id": "user-3", "email": "carol@example.com", "user_metadata": {}, "created_at": "2026-01-01T00:00:00Z"}}
    with patch("app.auth._request", new=AsyncMock(side_effect=[(401, {}), (200, refreshed)])):
        client = TestClient(app)
        client.cookies.set("muse_access_token", "expired")
        client.cookies.set("muse_refresh_token", "refresh")
        response = client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["id"] == "user-3"
    assert any("muse_access_token=new-access" in value for value in response.headers.get_list("set-cookie"))
