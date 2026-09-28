import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.profile import UserProfile
from sqlalchemy import select

client = TestClient(app)


def test_invalid_token_rejected():
    """Verify that an invalid/malformed Bearer token is rejected with HTTP 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.malformed.token"}
    )
    assert response.status_code == 401
    detail = response.json().get("detail", "")
    assert "Invalid or expired authentication token" in detail


def test_missing_token_in_production():
    """Verify that in production mode, a request without Authorization header is rejected with HTTP 401."""
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Authentication required" in response.json().get("detail", "")
    finally:
        settings.ENVIRONMENT = original_env


def test_firebase_id_token_accepted_and_uid_received():
    """
    Verify that when Firebase Admin verifies an ID token,
    the backend correctly receives the Firebase UID and email.
    """
    mock_uid = "fb-candidate-uid-12345"
    mock_email = "candidate@firebase.test"
    mock_name = "Firebase Candidate"

    with patch("app.core.firebase.verify_firebase_id_token") as mock_verify:
        mock_verify.return_value = {
            "uid": mock_uid,
            "email": mock_email,
            "name": mock_name,
            "auth_time": 1700000000,
        }

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer mock-valid-firebase-id-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == mock_uid
        assert data["data"]["email"] == mock_email
        assert data["data"]["full_name"] == mock_name


@pytest.mark.asyncio
async def test_automatic_sqlite_user_and_profile_sync():
    """
    Verify that upon first authenticating with a Firebase ID token,
    the backend automatically provisions User and UserProfile in SQLite
    so foreign keys in other modules never break.
    """
    mock_uid = "fb-auto-sync-uid-777"
    mock_email = "autosync@firebase.test"
    mock_name = "Auto Sync User"

    with patch("app.core.firebase.verify_firebase_id_token") as mock_verify:
        mock_verify.return_value = {
            "uid": mock_uid,
            "email": mock_email,
            "name": mock_name,
        }

        # Make request to /auth/me
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer mock-token-for-sync"}
        )
        assert response.status_code == 200

        # Query the active test database directly to verify automatic provisioning
        from tests.conftest import TestAsyncSessionLocal
        async with TestAsyncSessionLocal() as session:
            stmt_user = select(User).where(User.id == mock_uid)
            res_user = await session.execute(stmt_user)
            db_user = res_user.scalar_one_or_none()
            assert db_user is not None
            assert db_user.email == mock_email
            assert db_user.full_name == mock_name

            stmt_prof = select(UserProfile).where(UserProfile.user_id == mock_uid)
            res_prof = await session.execute(stmt_prof)
            db_prof = res_prof.scalar_one_or_none()
            assert db_prof is not None
            assert db_prof.user_id == mock_uid

            # Clean up the test user
            await session.delete(db_prof)
            await session.delete(db_user)
            await session.commit()


def test_protected_routes_work_with_firebase_uid():
    """Verify that protected modules like skills and roadmaps accept the Firebase token."""
    mock_uid = "fb-test-routes-uid-888"

    with patch("app.core.firebase.verify_firebase_id_token") as mock_verify:
        mock_verify.return_value = {
            "uid": mock_uid,
            "email": "routes@firebase.test",
            "name": "Route Tester",
        }

        # Call skills inventory endpoint
        response = client.get(
            "/api/v1/skills",
            headers={"Authorization": "Bearer mock-firebase-token"}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True


def test_legacy_token_fallback():
    """Verify backwards compatibility: legacy HMAC JWT tokens are still verified if passed."""
    legacy_token = create_access_token(data={"sub": "legacy-test-user-555", "email": "legacy@test.com"})

    # Even without mocking Firebase (which will fail for this token),
    # the security dependency falls back to HMAC decoding
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {legacy_token}"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["id"] == "legacy-test-user-555"
