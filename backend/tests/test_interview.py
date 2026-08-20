import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.anyio
async def test_interview_start_and_modes():
    """Test starting mock interview session across different modes."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Start Mixed Interview
        res_mix = await ac.post(
            "/api/v1/interview/start",
            json={
                "mode": "Mixed",
                "target_role": "Software Developer",
                "difficulty": "Beginner",
                "question_count": 5
            }
        )
        assert res_mix.status_code == 200
        data_mix = res_mix.json()
        assert data_mix["success"] is True
        session = data_mix["data"]
        assert session["mode"] == "Mixed"
        assert session["current_question"] is not None
        assert session["current_question"]["question_index"] == 0

        # Start Resume-Based Interview
        res_res = await ac.post(
            "/api/v1/interview/start",
            json={
                "mode": "Resume-Based",
                "target_role": "Software Developer",
                "difficulty": "Beginner",
                "question_count": 3
            }
        )
        assert res_res.status_code == 200
        assert res_res.json()["data"]["mode"] == "Resume-Based"


@pytest.mark.anyio
async def test_answer_submission_and_evaluation():
    """Test submitting answer and receiving structured multi-category evaluation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Start session
        start_res = await ac.post(
            "/api/v1/interview/start",
            json={"mode": "Technical", "question_count": 3}
        )
        session_id = start_res.json()["data"]["id"]

        # 2. Submit answer
        ans_res = await ac.post(
            f"/api/v1/interview/session/{session_id}/answer",
            json={
                "answer_text": "I used Python and FastAPI async request handlers with PostgreSQL connection pooling to optimize database latency and handle concurrent traffic."
            }
        )
        assert ans_res.status_code == 200
        eval_data = ans_res.json()["data"]
        assert eval_data["score"] > 0
        assert "technical_score" in eval_data
        assert "communication_score" in eval_data
        assert "strengths" in eval_data


@pytest.mark.anyio
async def test_adaptive_difficulty_and_next_question():
    """Test adaptive difficulty transition and fetching next question."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Start session
        start_res = await ac.post(
            "/api/v1/interview/start",
            json={"mode": "Technical", "difficulty": "Beginner", "question_count": 3}
        )
        session_id = start_res.json()["data"]["id"]

        # Submit strong answer
        await ac.post(
            f"/api/v1/interview/session/{session_id}/answer",
            json={
                "answer_text": "I designed microservices using Python, FastAPI, and Redis caching. We implemented database indexing and connection pools to support 5,000 concurrent users."
            }
        )

        # Trigger next question
        next_res = await ac.post(f"/api/v1/interview/session/{session_id}/next")
        assert next_res.status_code == 200
        session_data = next_res.json()["data"]
        assert session_data["current_question_index"] == 1
        assert session_data["difficulty"] in ["Intermediate", "Beginner"]


@pytest.mark.anyio
async def test_interview_completion_report_and_readiness():
    """Test interview session completion, report generation, and readiness endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Start session
        start_res = await ac.post(
            "/api/v1/interview/start",
            json={"mode": "Mixed", "question_count": 2}
        )
        session_id = start_res.json()["data"]["id"]

        # Answer question 1
        await ac.post(
            f"/api/v1/interview/session/{session_id}/answer",
            json={"answer_text": "I solved the API integration challenge by implementing robust retry mechanisms and async handlers."}
        )

        # 2. Complete session
        comp_res = await ac.post(f"/api/v1/interview/session/{session_id}/complete")
        print("COMP_RES:", comp_res.json())
        assert comp_res.status_code == 200
        report = comp_res.json()["data"]
        assert report["overall_score"] > 0
        assert report["readiness_status"] in ["EXCELLENT", "READY", "NEARLY READY", "NEEDS PRACTICE"]
        assert len(report["questions_review"]) > 0

        # 3. Check interview readiness endpoint
        readiness_res = await ac.get("/api/v1/interview/readiness")
        assert readiness_res.status_code == 200
        r_data = readiness_res.json()["data"]
        assert r_data["total_interviews_completed"] >= 1
        assert r_data["overall_readiness_status"] in ["EXCELLENT", "READY", "NEARLY READY", "NEEDS PRACTICE"]
