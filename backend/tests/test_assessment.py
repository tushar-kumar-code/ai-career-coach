import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_start_assessment():
    response = client.post("/api/v1/assessment/start")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_id" in data["data"]
    assert data["data"]["total_questions"] >= 16
    assert data["data"]["current_question"] is not None


def test_submit_answer_and_flow():
    # 1. Start session
    start_resp = client.post("/api/v1/assessment/start").json()
    session_id = start_resp["data"]["session_id"]
    q_id = start_resp["data"]["current_question"]["id"]
    opt_id = start_resp["data"]["current_question"]["options"][0]["id"]

    # 2. Submit answer
    ans_resp = client.post(
        "/api/v1/assessment/answer",
        json={
            "session_id": session_id,
            "question_id": q_id,
            "selected_option_id": opt_id
        }
    )
    assert ans_resp.status_code == 200
    ans_data = ans_resp.json()
    assert ans_data["success"] is True
    assert ans_data["data"]["answers_count"] >= 1


def test_career_catalog_and_details():
    # Fetch catalog
    cat_resp = client.get("/api/v1/assessment/careers")
    assert cat_resp.status_code == 200
    cat_data = cat_resp.json()
    assert cat_data["success"] is True
    assert len(cat_data["data"]) >= 12

    # Fetch specific details for software-developer
    dev_resp = client.get("/api/v1/assessment/careers/software-developer")
    assert dev_resp.status_code == 200
    dev_data = dev_resp.json()
    assert dev_data["data"]["title"] == "Software Developer"


def test_select_target_career():
    target_resp = client.post(
        "/api/v1/assessment/target-career",
        json={"career_slug": "full-stack-developer"}
    )
    assert target_resp.status_code == 200
    target_data = target_resp.json()
    assert target_data["success"] is True
    assert target_data["data"]["target_career"] == "Full Stack Developer"
