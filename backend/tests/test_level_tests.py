import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.ai.roadmap_ai import RoadmapAIService, AIRoadmapPhaseContent, AIRoadmapTaskContent, AIProjectIdea
from app.schemas.roadmap import LevelTestResponse, LevelTestQuestion

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_ai_services():
    """Autouse mock for RoadmapAIService and test generation so tests run deterministically in milliseconds."""
    mock_content = AIRoadmapPhaseContent(
        phase_title="Spawn Point: Foundations",
        learning_objectives=["Master foundational logic."],
        milestone_title="Spawn Milestone",
        milestone_criteria="Complete setup.",
        tasks=[
            AIRoadmapTaskContent(
                title="Python Syntax Basics",
                description="Learn core syntax.",
                estimated_minutes=30,
                task_type="Practice",
                why_it_matters="Foundation for all programming.",
                topics_to_learn=["Syntax", "Variables"],
                learning_focus="Variables and print statements.",
                practice_goal="Print formatted statements.",
                expected_outcome="Working script.",
                verification_method="Run script.",
                recommended_resources=["Python Docs"],
                difficulty_level="Beginner",
                prerequisites=[]
            )
        ],
        project=AIProjectIdea(
            title="Setup Project",
            objective="Configure env.",
            skills_practiced=["Python"],
            difficulty="Beginner",
            expected_outcome="Configured env.",
            resume_relevance="Basic setup."
        )
    )

    mock_questions = [
        LevelTestQuestion(
            id="q_1",
            topic="Variables",
            question="What is the result of type(5)?",
            options=["A) <class 'int'>", "B) <class 'str'>", "C) <class 'float'>", "D) <class 'bool'>"],
            correct_answer="A) <class 'int'>",
            explanation="5 is an integer in Python."
        ),
        LevelTestQuestion(
            id="q_2",
            topic="Loops",
            question="Which keyword stops a loop immediately?",
            options=["A) break", "B) continue", "C) pass", "D) return"],
            correct_answer="A) break",
            explanation="The break statement terminates the current loop."
        ),
        LevelTestQuestion(
            id="q_3",
            topic="Data Types",
            question="Which data structure is immutable in Python?",
            options=["A) tuple", "B) list", "C) dict", "D) set"],
            correct_answer="A) tuple",
            explanation="Tuples cannot be modified after creation."
        ),
        LevelTestQuestion(
            id="q_4",
            topic="Functions",
            question="Which keyword defines a function?",
            options=["A) def", "B) function", "C) func", "D) lambda"],
            correct_answer="A) def",
            explanation="def keyword introduces a function definition."
        )
    ]

    async def mock_structure(self, *args, **kwargs):
        return self._fallback_domain_structure(*args, **kwargs)

    with patch.object(RoadmapAIService, "generate_phase_content", new_callable=AsyncMock) as mocked_phase, \
         patch.object(RoadmapAIService, "generate_domain_roadmap_structure", new=mock_structure), \
         patch("app.api.v1.roadmap.level_test_engine.generate_test", new_callable=AsyncMock) as mocked_test:
        mocked_phase.return_value = mock_content
        mocked_test.return_value = LevelTestResponse(
            phase_id="phase-1",
            phase_number=1,
            phase_title="Spawn Point: Foundations",
            level_name="Spawn Point",
            target_career="Full Stack Developer",
            passing_score_percent=70,
            xp_reward=100,
            questions=mock_questions
        )
        yield


def test_level_test_generation_and_progression():
    """Test generating AI level test, failing score (<70%), recovery guidance, and passing score (>=70%) unlocking next level."""
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
    # Verify adaptive recovery guidance fields
    assert fail_result["can_retry"] is True
    assert len(fail_result["recovery_recommendations"]) > 0
    assert fail_result["guided_practice_exercise"] is not None
    assert "drill" in fail_result["guided_practice_exercise"].lower() or "practice" in fail_result["guided_practice_exercise"].lower()

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

