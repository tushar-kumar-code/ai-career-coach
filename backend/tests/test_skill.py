import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.skill.normalizer import SkillNormalizer

client = TestClient(app)


def test_skill_normalization():
    normalizer = SkillNormalizer()
    assert normalizer.normalize("react.js") == "React"
    assert normalizer.normalize("reactjs") == "React"
    assert normalizer.normalize("python3") == "Python"
    assert normalizer.normalize("postgresql") == "PostgreSQL"
    assert normalizer.normalize("fastapi") == "FastAPI"
    assert normalizer.normalize("k8s") == "Kubernetes"
    assert normalizer.normalize("node.js") == "Node.js"
    assert normalizer.normalize("power bi") == "PowerBI"
    assert normalizer.normalize("rest apis") == "REST APIs"


def test_get_skill_profile_gaps_and_recommended():
    # 1. Fetch Skill Profile
    response = client.get("/api/v1/skills/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_skills_count" in data["data"]
    assert "verified_count" in data["data"]
    assert "supported_count" in data["data"]
    assert "claimed_count" in data["data"]
    assert "strong_skills" in data["data"]
    assert "skills_to_improve" in data["data"]
    assert "missing_skills" in data["data"]

    # 2. Fetch Skill Gaps
    g_response = client.get("/api/v1/skills/gaps")
    assert g_response.status_code == 200
    g_data = g_response.json()
    assert g_data["success"] is True
    assert isinstance(g_data["data"], list)

    # 3. Fetch Recommended Skills
    r_response = client.get("/api/v1/skills/recommended")
    assert r_response.status_code == 200
    r_data = r_response.json()
    assert r_data["success"] is True
    assert isinstance(r_data["data"], list)

    # 4. Fetch All User Skills list
    s_response = client.get("/api/v1/skills")
    assert s_response.status_code == 200
    s_data = s_response.json()
    assert s_data["success"] is True
    assert isinstance(s_data["data"], list)


def test_recalculate_skill_profile():
    response = client.post("/api/v1/skills/recalculate")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "target_career" in data["data"]
    assert "total_skills_count" in data["data"]


def test_target_career_change_synchronization():
    # 1. Set target career to "Frontend Developer"
    t_resp = client.post(
        "/api/v1/assessment/target-career",
        json={"career_slug": "frontend-developer"}
    )
    assert t_resp.status_code == 200

    # 2. Fetch updated skill profile and verify target career updated
    p_resp = client.get("/api/v1/skills/profile")
    assert p_resp.status_code == 200
    p_data = p_resp.json()
    assert p_data["data"]["target_career"] == "Frontend Developer"

    # 3. Set target career to "Backend Developer"
    b_resp = client.post(
        "/api/v1/assessment/target-career",
        json={"career_slug": "backend-developer"}
    )
    assert b_resp.status_code == 200

    # 4. Verify updated target career
    p_resp2 = client.get("/api/v1/skills/profile")
    assert p_resp2.status_code == 200
    assert p_resp2.json()["data"]["target_career"] == "Backend Developer"


def test_skill_details_and_evidence():
    # Recalculate to make sure user skills exist
    client.post("/api/v1/skills/recalculate")

    # Fetch user skills
    s_res = client.get("/api/v1/skills")
    skills = s_res.json().get("data", [])

    if skills:
        skill_id = skills[0]["id"]
        d_res = client.get(f"/api/v1/skills/{skill_id}")
        assert d_res.status_code == 200
        d_data = d_res.json()
        assert d_data["success"] is True
        assert "skill" in d_data["data"]
        assert "evidence_records" in d_data["data"]
        assert "recommended_next_action" in d_data["data"]

    # Invalid skill_id returns 404
    err_res = client.get("/api/v1/skills/invalid-skill-id-999")
    assert err_res.status_code == 404
