"""
Tests for Career Digital Twin + Progress & Readiness Engine
============================================================
All tests use httpx AsyncClient with ASGITransport (matching existing test pattern).
Dev user ID = "dev-user-12345" (security.py fallback).
"""
import pytest
import datetime
from httpx import AsyncClient, ASGITransport
from app.main import app


# ---- Helper: base URL and common headers ----
BASE = "http://test"
DT_PREFIX = "/api/v1/digital-twin"


@pytest.mark.anyio
async def test_readiness_score_returns_valid_structure():
    """GET /readiness must return success=True and all 6 sub-score keys."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        res = await ac.get(f"{DT_PREFIX}/readiness")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        scores = data["data"]
        assert "overall_readiness_score" in scores
        assert "skill_readiness" in scores
        assert "resume_readiness" in scores
        assert "interview_readiness" in scores
        assert "roadmap_progress" in scores
        assert "job_match_readiness" in scores
        assert "portfolio_readiness" in scores
        assert "readiness_label" in scores
        assert 0 <= scores["overall_readiness_score"] <= 100


@pytest.mark.anyio
async def test_readiness_scores_are_between_0_and_100():
    """All sub-scores must be in range [0, 100] -- no hardcoded values."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        res = await ac.get(f"{DT_PREFIX}/readiness")
        scores = res.json()["data"]
        for key in ["skill_readiness", "resume_readiness", "interview_readiness",
                    "roadmap_progress", "job_match_readiness", "portfolio_readiness"]:
            assert 0 <= scores[key] <= 100, f"{key} out of range: {scores[key]}"


@pytest.mark.anyio
async def test_digital_twin_profile_structure():
    """GET /profile must return full twin structure with all required keys."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        res = await ac.get(f"{DT_PREFIX}/profile")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        twin = data["data"]
        assert "overall_readiness_score" in twin
        assert "sub_scores" in twin
        assert "top_strengths" in twin
        assert "priority_gaps" in twin
        assert "critical_missing_skills" in twin
        assert "next_action" in twin
        assert "evidence_summary" in twin
        assert isinstance(twin["top_strengths"], list)
        assert isinstance(twin["priority_gaps"], list)


@pytest.mark.anyio
async def test_gap_analysis_structure():
    """GET /gaps must return valid structure even for fresh users."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        res = await ac.get(f"{DT_PREFIX}/gaps")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        gaps = data["data"]
        assert "top_strengths" in gaps
        assert "priority_gaps" in gaps
        assert "critical_missing_skills" in gaps
        assert "total_gaps_found" in gaps
        assert isinstance(gaps["priority_gaps"], list)
        assert isinstance(gaps["critical_missing_skills"], list)


@pytest.mark.anyio
async def test_next_action_has_required_fields():
    """GET /next-action must always return a valid action with required fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        res = await ac.get(f"{DT_PREFIX}/next-action")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        action = data["data"]
        assert "action_type" in action
        assert "title" in action
        assert "why_it_matters" in action
        assert "expected_impact" in action
        assert "action_link" in action
        assert "impact_level" in action
        # Action link must be a valid path
        assert action["action_link"].startswith("/")


@pytest.mark.anyio
async def test_achievements_returns_list():
    """GET /achievements returns a list (may be empty for fresh user with no activity)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        res = await ac.get(f"{DT_PREFIX}/achievements")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        achievements = data["data"]
        assert isinstance(achievements, list)
        # Each achievement must have required fields
        for ach in achievements:
            assert "achievement_key" in ach
            assert "title" in ach
            assert "description" in ach
            assert "earned_at" in ach


@pytest.mark.anyio
async def test_readiness_history_returns_list():
    """GET /readiness/history returns a list of historical snapshots."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        res = await ac.get(f"{DT_PREFIX}/readiness/history")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        for snap in data["data"]:
            assert "date" in snap
            assert "overall" in snap
            assert 0 <= snap["overall"] <= 100


@pytest.mark.anyio
async def test_snapshot_save_and_retrieval():
    """POST /snapshot creates a snapshot; GET /readiness/history includes it."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        # Save snapshot
        save_res = await ac.post(f"{DT_PREFIX}/snapshot")
        assert save_res.status_code == 200
        save_data = save_res.json()
        assert save_data["success"] is True
        assert "snapshot_date" in save_data["data"]
        today_str = str(datetime.date.today())
        assert save_data["data"]["snapshot_date"] == today_str

        # Verify it appears in history
        hist_res = await ac.get(f"{DT_PREFIX}/readiness/history")
        history = hist_res.json()["data"]
        dates = [h["date"] for h in history]
        assert today_str in dates


@pytest.mark.anyio
async def test_weekly_report_structure():
    """GET /weekly-report must return report with all required structural fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        res = await ac.get(f"{DT_PREFIX}/weekly-report")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        report = data["data"]
        assert "week_start_date" in report
        assert "week_end_date" in report
        assert "score_changes" in report
        assert "activity" in report
        assert "improvements" in report
        assert "biggest_weakness" in report
        assert "recommended_focus" in report
        assert "current_scores" in report
        assert isinstance(report["improvements"], list)
        # Score changes keys
        sc = report["score_changes"]
        assert "overall_delta" in sc
        assert "skill_delta" in sc
        assert "resume_delta" in sc
        assert "interview_delta" in sc


@pytest.mark.anyio
async def test_overall_score_weighted_formula_consistency():
    """
    Verify the overall score matches the documented weighted formula:
    skill*0.30 + resume*0.20 + interview*0.20 + roadmap*0.15 + job_match*0.10 + portfolio*0.05
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as ac:
        res = await ac.get(f"{DT_PREFIX}/readiness")
        scores = res.json()["data"]

        expected = int(round(
            scores["skill_readiness"] * 0.30 +
            scores["resume_readiness"] * 0.20 +
            scores["interview_readiness"] * 0.20 +
            scores["roadmap_progress"] * 0.15 +
            scores["job_match_readiness"] * 0.10 +
            scores["portfolio_readiness"] * 0.05
        ))

        # Allow 1-point rounding difference
        assert abs(scores["overall_readiness_score"] - expected) <= 1, (
            f"Overall score {scores['overall_readiness_score']} doesn''t match formula result {expected}"
        )

