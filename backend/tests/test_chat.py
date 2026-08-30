from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_empty_message_validation():
    # 1. Login demo user
    login_res = client.post("/api/v1/auth/demo-login")
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]

    # 2. Test empty message
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/v1/chat", json={"message": "   "}, headers=headers)
    assert resp.status_code == 400
    assert "cannot be empty" in resp.json().get("detail", "").lower()


def test_chat_success_with_coach():
    # 1. Login demo user
    login_res = client.post("/api/v1/auth/demo-login")
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]

    # 2. Test valid chat request
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/v1/chat",
        json={
            "message": "What are 2 important tips for cracking a technical interview?",
            "target_role": "Backend Engineer"
        },
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "response" in data["data"]
    assert len(data["data"]["response"]) > 0
    assert "provider" in data["data"]
    assert "timestamp" in data["data"]
