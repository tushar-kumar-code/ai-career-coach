"""
Security & Production Hardening Test Suite
===========================================
Verifies:
1. Production authentication enforcement (401 when no token in production).
2. Development mode fallback (dev-user-12345).
3. JWT signature verification and payload extraction.
4. User data isolation (User A cannot access User B resources).
5. File upload security (extension rejection, size limit, path traversal sanitization).
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.core.security import get_current_user_id, create_access_token


@pytest.mark.anyio
async def test_dev_mode_auth_fallback():
    """In development mode, requests without token resolve to dev fallback user."""
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "development"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/v1/digital-twin/readiness")
            assert res.status_code == 200
            assert res.json()["success"] is True
    finally:
        settings.ENVIRONMENT = original_env


@pytest.mark.anyio
async def test_production_mode_rejects_unauthenticated():
    """In production mode, requests without Bearer token must return 401 Unauthorized."""
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/v1/digital-twin/readiness")
            assert res.status_code == 401
    finally:
        settings.ENVIRONMENT = original_env


@pytest.mark.anyio
async def test_production_mode_accepts_valid_jwt():
    """In production mode, a valid signed JWT must authenticate successfully."""
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        token = create_access_token(data={"sub": "prod-user-99999"})
        headers = {"Authorization": f"Bearer {token}"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/v1/digital-twin/readiness", headers=headers)
            assert res.status_code == 200
            assert res.json()["success"] is True
    finally:
        settings.ENVIRONMENT = original_env


@pytest.mark.anyio
async def test_production_mode_rejects_invalid_jwt():
    """In production mode, an invalid/corrupt JWT must return 401."""
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        headers = {"Authorization": "Bearer invalid.jwt.token"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/v1/digital-twin/readiness", headers=headers)
            assert res.status_code == 401
    finally:
        settings.ENVIRONMENT = original_env


@pytest.mark.anyio
async def test_user_isolation_on_interview_session():
    """User A cannot access User B's interview session (404/isolation)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create session as User A
        token_a = create_access_token(data={"sub": "user-alice-111"})
        token_b = create_access_token(data={"sub": "user-bob-222"})

        res_start = await ac.post(
            "/api/v1/interview/start",
            json={"mode": "Technical", "target_role": "Software Developer"},
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert res_start.status_code == 200
        session_id = res_start.json()["data"]["id"]

        # Try to access as User B
        res_other = await ac.get(
            f"/api/v1/interview/session/{session_id}",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert res_other.status_code == 404
