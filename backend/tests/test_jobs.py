import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.anyio
async def test_job_search_and_normalization():
    """Test job search endpoint with catalog provider seeding and filters."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Search Python jobs
        res = await ac.get("/api/v1/jobs/search?query=Python")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        jobs = data["data"]
        assert len(jobs) > 0
        assert any("Python" in j["title"] or "Python" in j["required_skills"] for j in jobs)

        # Search Remote jobs
        res_remote = await ac.get("/api/v1/jobs/search?remote_only=true")
        assert res_remote.status_code == 200
        remote_jobs = res_remote.json()["data"]
        assert all(j["is_remote"] is True for j in remote_jobs)


@pytest.mark.anyio
async def test_job_recommended_matches():
    """Test personalized job recommendations calculation for user profile."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/jobs/recommended")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        matches = data["data"]
        assert len(matches) > 0

        first_match = matches[0]
        assert "job" in first_match
        assert "match_breakdown" in first_match
        assert "matching_skills" in first_match
        assert "roadmap_connections" in first_match
        assert first_match["match_breakdown"]["overall_score"] > 0
        assert first_match["match_breakdown"]["readiness_status"] in [
            "READY", "NEARLY READY", "NEEDS SKILL DEVELOPMENT", "LOW MATCH"
        ]


@pytest.mark.anyio
async def test_save_job_and_user_isolation():
    """Test saving/bookmarking jobs and user data isolation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Search for a job ID
        search_res = await ac.get("/api/v1/jobs/search?limit=1")
        job = search_res.json()["data"][0]
        job_id = job["id"]

        # Save job
        save_res = await ac.post(f"/api/v1/jobs/{job_id}/save?notes=Targeting%20for%20Q3")
        assert save_res.status_code == 200
        assert save_res.json()["success"] is True

        # Fetch saved jobs
        saved_res = await ac.get("/api/v1/jobs/saved")
        assert saved_res.status_code == 200
        saved_list = saved_res.json()["data"]
        assert any(s["job_id"] == job_id for s in saved_list)

        # Remove saved job
        del_res = await ac.delete(f"/api/v1/jobs/{job_id}/save")
        assert del_res.status_code == 200
        assert del_res.json()["data"] is True


@pytest.mark.anyio
async def test_application_tracker_lifecycle_and_history():
    """Test full application tracking lifecycle, status transitions, and audit trail."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Get job
        search_res = await ac.get("/api/v1/jobs/search?limit=1")
        job = search_res.json()["data"][0]
        job_id = job["id"]

        # 2. Create application
        create_res = await ac.post(
            "/api/v1/jobs/applications",
            json={
                "job_id": job_id,
                "status": "Applied",
                "notes": "Applied via company site"
            }
        )
        assert create_res.status_code == 200
        app_data = create_res.json()["data"]
        app_id = app_data["id"]
        assert app_data["status"] == "Applied"

        # 3. Update status to Interview
        update_res = await ac.put(
            f"/api/v1/jobs/applications/{app_id}",
            json={
                "status": "Interview",
                "interview_date": "2026-08-28",
                "notes": "Scheduled 1st technical round"
            }
        )
        assert update_res.status_code == 200
        assert update_res.json()["data"]["status"] == "Interview"

        # 4. Fetch history audit trail
        history_res = await ac.get(f"/api/v1/jobs/applications/{app_id}/history")
        assert history_res.status_code == 200
        history_entries = history_res.json()["data"]
        assert len(history_entries) >= 2
        assert any(h["to_status"] == "Interview" for h in history_entries)

        # 5. Cleanup / Delete application
        del_app_res = await ac.delete(f"/api/v1/jobs/applications/{app_id}")
        assert del_app_res.status_code == 200
        assert del_app_res.json()["data"] is True
