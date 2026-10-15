import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_level_test_generation_and_progression():
    """Test generating AI level test, failing score (<70%), and passing score (>=70%) unlocking next level."""
    # 1. Ensure active roadmap exists
    gen_resp = client.post("/api/v1/roadmap/generate", json={"user_level": "Beginner"})
    assert gen_resp.status_code == 200
    roadmap = gen_resp.json()["data"]
    phase_1 = roadmap["phases"][0]
    phase_1_id = phase_1["id"]
    phase_2 = roadmap["phases"][1]

    # Verify Level 1 is unlocked by default, and Level 2 is locked before test
    assert phase_1["is_unlocked"] is True
    assert phase_2["is_unlocked"] is False

    # 2. Generate AI Level Test for Phase 1
    test_gen_resp = client.post(f"/api/v1/roadmap/phases/{phase_1_id}/generate-test")
    assert test_gen_resp.status_code == 200
    test_data = test_gen_resp.json()["data"]

    assert test_data["phase_id"] == phase_1_id
    assert test_data["level_name"] == "Spawn Point"
    assert len(test_data["questions"]) >= 4

    questions = test_data["questions"]

    # 3. Test submitting with wrong answers (< 70% passing threshold)
    wrong_answers = {q["id"]: "A) Definitely wrong option xyz" for q in questions}
    fail_sub_resp = client.post(
        f"/api/v1/roadmap/phases/{phase_1_id}/submit-test",
        json={"answers": wrong_answers}
    )
    assert fail_sub_resp.status_code == 200
    fail_result = fail_sub_resp.json()["data"]
    assert fail_result["passed"] is False
    assert fail_result["next_level_unlocked"] is False

    # Phase 2 must still be locked
    current_rm = client.get("/api/v1/roadmap/current").json()["data"]
    assert current_rm["phases"][1]["is_unlocked"] is False

    # 4. Test submitting with all correct answers (>= 70% passing threshold)
    correct_answers = {q["id"]: q["correct_answer"] for q in questions}
    pass_sub_resp = client.post(
        f"/api/v1/roadmap/phases/{phase_1_id}/submit-test",
        json={"answers": correct_answers}
    )
    assert pass_sub_resp.status_code == 200
    pass_result = pass_sub_resp.json()["data"]
    assert pass_result["passed"] is True
    assert pass_result["score_percent"] == 100
    assert pass_result["next_level_unlocked"] is True
    assert pass_result["unlocked_level_name"] == "Starter Camp"

    # 5. Verify that Level 2 ("Starter Camp") is now unlocked in current roadmap!
    updated_rm = client.get("/api/v1/roadmap/current").json()["data"]
    assert updated_rm["phases"][0]["test_passed"] is True
    assert updated_rm["phases"][1]["is_unlocked"] is True
