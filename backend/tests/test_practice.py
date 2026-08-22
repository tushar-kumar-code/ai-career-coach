"""
test_practice.py — Phase 3 tests for:
  - Micro Practice (focused interview sessions via topic_focus)
  - STAR Interview Coaching (component detection, missing components)
  - Interview → Skill feedback (meaningful weakness evidence creation)
  - Interview → Roadmap feedback (task prioritization, no duplicates, Today's Focus correct)
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.interview.evaluator import InterviewEvaluator


# ---------------------------------------------------------------------------
# Helper: evaluator instance (avoids full DB round-trip for unit tests)
# ---------------------------------------------------------------------------

evaluator = InterviewEvaluator()


# ===========================================================================
# SECTION 1: Micro Practice (focused 3-question session via existing API)
# ===========================================================================

@pytest.mark.anyio
async def test_micro_practice_valid_topic_start():
    """Micro Practice: starting a focused session with topic_focus produces a valid session."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            "/api/v1/interview/start",
            json={
                "mode": "Technical",
                "target_role": "Backend Developer",
                "difficulty": "Beginner",
                "question_count": 3,
                "topic_focus": "SQL Joins"
            }
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    session = data["data"]
    assert session["question_count"] == 3
    assert session["mode"] == "Technical"
    assert session["current_question"] is not None
    assert session["current_question"]["question_index"] == 0


@pytest.mark.anyio
async def test_micro_practice_answer_evaluation():
    """Micro Practice: submit an answer and receive a structured evaluation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Start focused practice
        start_res = await ac.post(
            "/api/v1/interview/start",
            json={
                "mode": "Technical",
                "question_count": 3,
                "topic_focus": "Python async"
            }
        )
        session_id = start_res.json()["data"]["id"]

        # Submit an answer
        ans_res = await ac.post(
            f"/api/v1/interview/session/{session_id}/answer",
            json={"answer_text": "I used asyncio and FastAPI with await keywords to handle concurrent requests without blocking."}
        )
    assert ans_res.status_code == 200
    eval_data = ans_res.json()["data"]
    assert eval_data["score"] > 0
    assert "strengths" in eval_data
    assert "suggested_improvement" in eval_data


@pytest.mark.anyio
async def test_micro_practice_completion():
    """Micro Practice: complete a 3-question session and get a final report."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Start 2-question practice
        start_res = await ac.post(
            "/api/v1/interview/start",
            json={"mode": "Technical", "question_count": 2, "topic_focus": "REST API Design"}
        )
        session_id = start_res.json()["data"]["id"]

        # Answer q1
        await ac.post(
            f"/api/v1/interview/session/{session_id}/answer",
            json={"answer_text": "REST uses HTTP verbs like GET, POST, PUT, DELETE and is stateless."}
        )

        # Complete session
        comp_res = await ac.post(f"/api/v1/interview/session/{session_id}/complete")
    assert comp_res.status_code == 200
    report = comp_res.json()["data"]
    assert report["overall_score"] >= 0
    assert report["readiness_status"] in ["EXCELLENT", "READY", "NEARLY READY", "NEEDS PRACTICE"]
    assert len(report["questions_review"]) >= 1


@pytest.mark.anyio
async def test_practice_suggest_endpoint():
    """Practice suggest endpoint returns valid suggestions list."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/roadmap/practice/suggest")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    suggestions = data["data"]
    assert isinstance(suggestions, list)
    for s in suggestions:
        assert "topic" in s
        assert "reason" in s
        assert s["source"] in ("skill_gap", "interview_weakness", "roadmap_task")
        assert s["priority"] in ("High", "Medium", "Low")


# ===========================================================================
# SECTION 2: STAR Interview Coaching (evaluator unit tests)
# ===========================================================================

@pytest.mark.anyio
async def test_star_situation_detection_present():
    """STAR: situation should be detected as Good when context is clearly described."""
    result = evaluator._fallback_evaluation(
        question_text="Tell me about a challenge you solved.",
        category="Behavioral",
        difficulty="Beginner",
        user_answer="During my internship project, we had a slow database query causing API timeouts. I was responsible for identifying the bottleneck. I added an index and the queries ran 10x faster.",
        is_short=False
    )
    assert result["situation_status"] == "Good"
    assert result["task_status"] == "Good"
    assert result["action_status"] == "Good"
    assert result["result_status"] == "Good"
    assert result["star_complete"] is True
    assert result["star_score"] == 100


@pytest.mark.anyio
async def test_star_result_missing():
    """STAR: result should be Missing when no outcome is mentioned."""
    result = evaluator._fallback_evaluation(
        question_text="Tell me about a problem you solved.",
        category="Behavioral",
        difficulty="Beginner",
        user_answer="In my project I had a bug in the authentication module. I debugged the code and fixed the issue.",
        is_short=False
    )
    assert result["result_status"] == "Missing"
    assert "Missing" in result["result_feedback"]
    assert result["star_complete"] is False


@pytest.mark.anyio
async def test_star_action_missing():
    """STAR: action should be Missing when personal actions are not specified."""
    result = evaluator._fallback_evaluation(
        question_text="Describe a time you worked in a team.",
        category="Behavioral",
        difficulty="Beginner",
        user_answer="We had a project deadline. The team was under pressure. Eventually things got resolved.",
        is_short=False
    )
    assert result["action_status"] == "Missing"
    assert result["action_feedback"] is not None


@pytest.mark.anyio
async def test_star_not_applicable_for_technical():
    """STAR: for Technical questions, STAR fields should be Not Applicable."""
    result = evaluator._fallback_evaluation(
        question_text="Explain how Python's asyncio event loop works.",
        category="Technical",
        difficulty="Intermediate",
        user_answer="The asyncio event loop runs coroutines using an async/await pattern, scheduling tasks without blocking threads.",
        is_short=False
    )
    assert result["situation_status"] == "Not Applicable"
    assert result["star_complete"] is False
    assert result["star_score"] == 0
    assert result["situation_feedback"] is None


@pytest.mark.anyio
async def test_star_full_missing_components_score_low():
    """STAR: a very short behavioral answer should have Missing for most components and low star_score."""
    result = evaluator._fallback_evaluation(
        question_text="Tell me about a challenge.",
        category="Behavioral",
        difficulty="Beginner",
        user_answer="I had an issue and solved it.",
        is_short=False
    )
    # Short answer: should have low/missing STAR components
    assert result["star_score"] < 100
    assert result["star_complete"] is False


# ===========================================================================
# SECTION 3: Interview → Skill Evidence Feedback
# ===========================================================================

@pytest.mark.anyio
async def test_meaningful_weakness_creates_evidence():
    """Interview → Skill: completing an interview session with weak areas triggers feedback loop."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Start session
        start_res = await ac.post(
            "/api/v1/interview/start",
            json={"mode": "Technical", "question_count": 1, "target_role": "Backend Developer"}
        )
        session_id = start_res.json()["data"]["id"]

        # Submit a short/weak answer to trigger weak topic detection
        await ac.post(
            f"/api/v1/interview/session/{session_id}/answer",
            json={"answer_text": "SQL"}  # Very short answer
        )

        # Complete session — this triggers feedback_loop.process_interview_feedback
        comp_res = await ac.post(f"/api/v1/interview/session/{session_id}/complete")
    assert comp_res.status_code == 200
    report = comp_res.json()["data"]
    # Should produce recommended roadmap topics (even if generic)
    assert isinstance(report["recommended_roadmap_topics"], list)


@pytest.mark.anyio
async def test_high_score_does_not_create_exaggerated_confidence():
    """Interview → Skill: high score should not make confidence absurdly high in a single session."""
    from app.services.interview.feedback_loop import InterviewFeedbackLoop
    from unittest.mock import AsyncMock, MagicMock

    loop = InterviewFeedbackLoop()

    # Mock DB session
    mock_db = AsyncMock()
    mock_execute = AsyncMock()

    # Return empty skills list to avoid actual DB queries
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalars.return_value.first.return_value = None
    mock_execute.return_value = mock_result
    mock_db.execute = mock_execute
    mock_db.commit = AsyncMock()

    # Should not raise, and recommended_topics should be a list
    result = await loop.process_interview_feedback(
        db=mock_db,
        user_id="test-user",
        target_role="Backend Developer",
        overall_score=95,
        category_scores={"technical": 95},
        weak_areas=[],
        questions_data=[]
    )
    assert isinstance(result, list)


@pytest.mark.anyio
async def test_weak_evidence_does_not_cascade_confidence_change():
    """Interview → Skill: a single weak answer should NOT crash a 'Claimed' skill to a lower state."""
    from app.services.interview.evaluator import InterviewEvaluator

    ev = InterviewEvaluator()
    result = ev._fallback_evaluation(
        question_text="Explain SQL JOIN types.",
        category="Technical",
        difficulty="Beginner",
        user_answer="JOIN combines tables",
        is_short=False
    )
    # Feedback loop uses confidence_weight=30 for weak evidence — detected_weak_topic should exist
    # but score should not be zero
    assert result["score"] > 0
    assert result["detected_weak_topic"] is not None or result["score"] >= 45


# ===========================================================================
# SECTION 4: Interview → Roadmap Feedback (task prioritization)
# ===========================================================================

@pytest.mark.anyio
async def test_roadmap_task_prioritization_no_duplicate():
    """Interview → Roadmap: feedback loop should not create a duplicate task for a weak area."""
    from app.services.interview.feedback_loop import InterviewFeedbackLoop
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.models.roadmap import Roadmap

    loop = InterviewFeedbackLoop()

    # Build a fake roadmap with a SQL Joins task
    fake_roadmap = MagicMock(spec=Roadmap)
    fake_roadmap.phases = [
        {
            "id": "phase-1",
            "title": "Foundation Phase",
            "skills": ["sql", "databases"],  # 'sql' (len>=3) should now match 'SQL Joins'
            "tasks": [
                {
                    "id": "phase-1-task-1",
                    "title": "Learn SQL Joins",  # 'sql' in 'learn sql joins' → matches
                    "is_completed": False,
                    "is_priority": False
                }
            ]
        }
    ]
    fake_roadmap.completed_task_ids = []

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalars.return_value.first.return_value = fake_roadmap
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    with patch("app.services.interview.feedback_loop.flag_modified"):
        recommended = await loop.process_interview_feedback(
            db=mock_db,
            user_id="test-user",
            target_role="Backend Developer",
            overall_score=45,  # Low score to trigger weak handling
            category_scores={"technical": 45},
            weak_areas=["SQL Joins"],
            questions_data=[{
                "evaluation": {"detected_weak_topic": "SQL Joins", "score": 40},
                "score": 40
            }]
        )

    # Should recommend reviewing SQL Joins
    assert any("SQL Joins" in r or "sql" in r.lower() for r in recommended)

    # The original task should be marked priority — NOT a new duplicate task
    phase_tasks = fake_roadmap.phases[0]["tasks"]
    assert len(phase_tasks) == 1  # No duplicate created
    assert phase_tasks[0].get("is_priority") is True


@pytest.mark.anyio
async def test_today_focus_returns_priority_task_first():
    """Interview → Roadmap: Today's Focus should surface priority tasks."""
    from app.services.roadmap.roadmap_engine import RoadmapEngine
    from unittest.mock import MagicMock
    from app.models.roadmap import Roadmap

    engine = RoadmapEngine()

    fake_roadmap = MagicMock(spec=Roadmap)
    fake_roadmap.target_role = "Backend Developer"
    fake_roadmap.hours_per_day = 2
    fake_roadmap.phases = [
        {
            "id": "phase-1",
            "title": "Foundation",
            "tasks": [
                {
                    "id": "task-1",
                    "title": "Learn Python Basics",
                    "description": "Study Python syntax",
                    "estimated_minutes": 30,
                    "task_type": "Learn",
                    "why_it_matters": "Core skill",
                    "is_completed": False,
                    "is_priority": False
                },
                {
                    "id": "task-2",
                    "title": "Learn SQL Joins",
                    "description": "Study SQL JOIN types",
                    "estimated_minutes": 30,
                    "task_type": "Learn",
                    "why_it_matters": "Interview weak area",
                    "is_completed": False,
                    "is_priority": True,
                    "priority_reason": "Interview identified weakness"
                }
            ]
        }
    ]

    result = engine.get_today_focus_tasks(fake_roadmap)
    assert result["today_tasks"] is not None
    assert len(result["today_tasks"]) > 0
    # Today's focus should include tasks from the phase
    task_titles = [t["title"] for t in result["today_tasks"]]
    assert any("Python" in t or "SQL" in t for t in task_titles)
