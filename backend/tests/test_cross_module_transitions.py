from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_roadmap_focus_skill_transition():
    # 1. Add skill to Today's focus
    resp = client.post("/api/v1/roadmap/focus-skill", json={"skill_name": "Docker & Containers"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["status"] in ["added", "prioritized", "already_focus"]
    assert "Docker & Containers" in data["data"]["task"]["title"] or "Docker & Containers" in data["data"]["task"]["skill"]

    # 2. Check today's tasks reflect this focus
    resp_today = client.get("/api/v1/roadmap/today")
    assert resp_today.status_code == 200
    today_data = resp_today.json()["data"]
    assert len(today_data["tasks"]) > 0
    assert any("Docker" in t["title"] or "Docker" in t["skill"] for t in today_data["tasks"])

    # 3. Requesting the same skill again detects already in focus
    resp_again = client.post("/api/v1/roadmap/focus-skill", json={"skill_name": "Docker & Containers"})
    assert resp_again.status_code == 200
    data_again = resp_again.json()
    assert data_again["data"]["status"] == "already_focus"


def test_interview_weak_topic_focused_practice():
    resp = client.post("/api/v1/interview/start", json={
        "mode": "Technical",
        "target_role": "Backend Engineer",
        "difficulty": "Beginner",
        "question_count": 3,
        "topic_focus": "PostgreSQL Indexing & Optimization"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    session = data["data"]
    assert session["mode"] == "Technical"
    assert session["current_question"] is not None
    q_text = session["current_question"]["question_text"]
    assert "PostgreSQL Indexing & Optimization" in q_text or "PostgreSQL" in q_text
