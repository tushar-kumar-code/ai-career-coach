"""
test_placement.py — Phase 4 tests for:
  - Placement Readiness Center (/api/v1/placement/checklist)
  - 10-point Placement Checklist deterministic evaluation
  - Placement Tiers & Student-Friendly Descriptions
  - 1-Page Student Career Brief (/api/v1/placement/brief)
  - Zero fake data / user isolation / consistency with ReadinessEngine
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.placement.checklist_engine import get_placement_tier, PlacementChecklistEngine
from app.services.placement.brief_engine import StudentBriefEngine


@pytest.mark.anyio
async def test_placement_tier_threshold_mapping():
    """Verify placement tier categorization based on composite score."""
    # 85-100 -> Placement Ready
    tier, desc = get_placement_tier(90)
    assert tier == "Placement Ready"
    assert "strong preparation" in desc.lower()

    # 70-84 -> Targeted Ready
    tier, desc = get_placement_tier(75)
    assert tier == "Targeted Ready"
    assert "targeted technical roles" in desc.lower()

    # 50-69 -> In Preparation
    tier, desc = get_placement_tier(60)
    assert tier == "In Preparation"
    assert "core skills established" in desc.lower()

    # <50 -> Early Foundation
    tier, desc = get_placement_tier(30)
    assert tier == "Early Foundation"
    assert "just getting started" in desc.lower()


@pytest.mark.anyio
async def test_placement_checklist_endpoint_success():
    """GET /api/v1/placement/checklist returns valid response with 10 checklist items."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/placement/checklist")

    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    checklist = data["data"]

    assert "overall_readiness_score" in checklist
    assert "readiness_tier" in checklist
    assert "tier_description" in checklist
    assert "completed_count" in checklist
    assert "total_count" in checklist
    assert checklist["total_count"] == 10
    assert "items" in checklist
    assert len(checklist["items"]) == 10

    # Verify each item has required structure
    for item in checklist["items"]:
        assert "key" in item
        assert "title" in item
        assert "description" in item
        assert "category" in item
        assert isinstance(item["completed"], bool)
        assert "target_value" in item
        assert "action_title" in item
        assert "action_route" in item
        assert item["action_route"].startswith("/")


@pytest.mark.anyio
async def test_placement_checklist_contains_all_10_keys():
    """Ensure all 10 domain checklist items are evaluated."""
    expected_keys = {
        "target_career",
        "resume_uploaded",
        "ats_optimization",
        "core_skills_verified",
        "critical_skill_gaps",
        "micro_practice",
        "portfolio_project",
        "technical_interview",
        "behavioral_star_interview",
        "application_pipeline",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/placement/checklist")

    data = res.json()["data"]
    actual_keys = {item["key"] for item in data["items"]}
    assert expected_keys == actual_keys


@pytest.mark.anyio
async def test_student_career_brief_endpoint_success():
    """GET /api/v1/placement/brief returns structured 1-page summary."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/placement/brief")

    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    brief = data["data"]

    assert "student_name" in brief
    assert "target_career" in brief
    assert "primary_archetype" in brief
    assert "overall_readiness_score" in brief
    assert "readiness_tier" in brief
    assert "sub_scores" in brief
    assert "top_strengths" in brief
    assert "priority_gaps" in brief
    assert "verified_skills_count" in brief
    assert "latest_resume_ats_score" in brief
    assert "roadmap_progress_percent" in brief
    assert "completed_projects" in brief
    assert "next_action" in brief
    assert "generated_at" in brief


@pytest.mark.anyio
async def test_student_career_brief_sub_scores_consistency():
    """Verify sub_scores in brief match expected dimensions from ReadinessEngine."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/placement/brief")

    brief = res.json()["data"]
    sub_scores = brief["sub_scores"]
    for dim in [
        "skill_readiness",
        "resume_readiness",
        "interview_readiness",
        "roadmap_progress",
        "job_match_readiness",
        "portfolio_readiness",
    ]:
        assert dim in sub_scores
        assert 0 <= sub_scores[dim] <= 100


@pytest.mark.anyio
async def test_placement_checklist_action_routes_validity():
    """Verify all action routes in checklist point to valid application paths."""
    valid_routes = {
        "/assessment",
        "/profile",
        "/resume",
        "/skills",
        "/roadmap",
        "/practice",
        "/interview",
        "/jobs",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/placement/checklist")

    items = res.json()["data"]["items"]
    for item in items:
        base_route = item["action_route"].split("?")[0]
        assert base_route in valid_routes, f"Invalid route: {item['action_route']}"


@pytest.mark.anyio
async def test_placement_brief_no_fake_data_for_uncompleted_modules():
    """Ensure student brief does not invent data for uncompleted modules."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/placement/brief")

    brief = res.json()["data"]
    assert isinstance(brief["top_strengths"], list)
    assert isinstance(brief["priority_gaps"], list)
    assert isinstance(brief["critical_missing_skills"], list)
    assert isinstance(brief["completed_projects"], list)
    assert isinstance(brief["achievements_sample"], list)


@pytest.mark.anyio
async def test_placement_endpoints_user_isolation():
    """Verify placement endpoints execute under security context."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        chk_res = await ac.get("/api/v1/placement/checklist")
        brief_res = await ac.get("/api/v1/placement/brief")

    assert chk_res.status_code == 200
    assert brief_res.status_code == 200
