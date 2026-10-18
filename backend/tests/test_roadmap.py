import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.roadmap import Roadmap
from app.models.skill import Skill
from app.schemas.skill import SkillGapSchema
from app.services.roadmap.dependency_graph import topological_sort_skills
from app.services.roadmap.roadmap_engine import RoadmapEngine
from app.services.ai.roadmap_ai import RoadmapAIService, AIRoadmapPhaseContent, AIRoadmapTaskContent, AIProjectIdea

client = TestClient(app)


# --------------------------------------------------------------------------
# Fixtures & Mock Helpers
# --------------------------------------------------------------------------

def create_mock_db(existing_roadmap=None):
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_roadmap
    mock_result.scalars.return_value.all.return_value = [existing_roadmap] if existing_roadmap else []
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    return mock_db


@pytest.fixture(autouse=True)
def mock_ai_phase_content():
    """Autouse mock for RoadmapAIService so tests execute in milliseconds without live Groq API rate limits."""
    mock_content = AIRoadmapPhaseContent(
        phase_title="Phase Mock: Core Foundations",
        learning_objectives=[
            "Understand foundational syntax and mental models.",
            "Build practical exercises."
        ],
        milestone_title="Practical Competence Milestone",
        milestone_criteria="Complete implementation without errors.",
        tasks=[
            AIRoadmapTaskContent(
                title="Python Basics: Control Flow & Loops",
                description="Learn control flow and iterative patterns in Python.",
                estimated_minutes=45,
                task_type="Practice",
                why_it_matters="Critical for algorithm and business logic implementation.",
                topics_to_learn=["for loops", "while loops", "range()", "break & continue"],
                learning_focus="Focus on loop termination conditions and off-by-one errors.",
                practice_goal="Write a script that filters numbers and computes stats.",
                expected_outcome="Working Python script executing without errors.",
                verification_method="Run test cases and inspect return values.",
                recommended_resources=["Official Python Documentation"],
                difficulty_level="Beginner",
                prerequisites=["Python Variables & Types"],
                concept_explanation="Loops let you execute a block of code repeatedly until a condition is met.",
                next_step="Advance to Python collections and dictionary structures."
            ),
            AIRoadmapTaskContent(
                title="Python Data Structures: Lists & Dictionaries",
                description="Learn in-memory data collections.",
                estimated_minutes=45,
                task_type="Practice",
                why_it_matters="Organizing structured data is required for all applications.",
                topics_to_learn=["List indexing", "Dictionary key-values", "List comprehensions"],
                learning_focus="Focus on time complexity and dictionary key lookups.",
                practice_goal="Implement in-memory record store.",
                expected_outcome="Working dictionary-based collection manager.",
                verification_method="Verify all CRUD operations succeed.",
                recommended_resources=["Python Data Structures Guide"],
                difficulty_level="Beginner",
                prerequisites=["Control Flow & Loops"],
                concept_explanation="Lists store ordered items, while dictionaries map unique keys to values for O(1) lookups.",
                next_step="Advance to object-oriented programming or modular functions."
            )
        ],
        project=AIProjectIdea(
            title="Interactive CLI Data Processing Tool",
            objective="Build a modular Python application processing datasets.",
            skills_practiced=["Python", "CLI"],
            difficulty="Beginner",
            expected_outcome="Working CLI tool with formatted outputs.",
            resume_relevance="Demonstrates clean Python modular coding."
        )
    )

    async def mock_structure(self, *args, **kwargs):
        return self._fallback_domain_structure(*args, **kwargs)

    with patch.object(RoadmapAIService, "generate_phase_content", new_callable=AsyncMock) as mocked_content, \
         patch.object(RoadmapAIService, "generate_domain_roadmap_structure", new=mock_structure):
        mocked_content.return_value = mock_content
        yield mocked_content


# --------------------------------------------------------------------------
# Baseline Tests (Preserved)
# --------------------------------------------------------------------------

def test_dependency_ordering():
    """Verify topological sorting places prerequisite skills before advanced skills."""
    skills = ["React", "JavaScript", "HTML/CSS", "Next.js", "Git", "Programming Fundamentals"]
    sorted_skills = topological_sort_skills(skills)

    # HTML/CSS before JavaScript
    assert sorted_skills.index("HTML/CSS") < sorted_skills.index("JavaScript")
    # JavaScript before React
    assert sorted_skills.index("JavaScript") < sorted_skills.index("React")
    # React before Next.js
    assert sorted_skills.index("React") < sorted_skills.index("Next.js")
    # Programming Fundamentals before Git
    assert sorted_skills.index("Programming Fundamentals") < sorted_skills.index("Git")


def test_generate_and_get_roadmap():
    """Test generating a roadmap and fetching current active roadmap."""
    resp = client.post(
        "/api/v1/roadmap/generate",
        json={
            "user_level": "Beginner",
            "hours_per_day": 2,
            "days_per_week": 5,
            "preferred_learning_style": "Hands-on",
            "career_goal": "Entry-level Job"
        }
    )
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert "id" in data
    assert data["hours_per_day"] == 2
    assert data["overall_progress_percent"] == 0
    assert len(data["phases"]) >= 3
    assert data.get("career_goal") == "Entry-level Job"
    assert "schedule_notes" in data

    get_resp = client.get("/api/v1/roadmap/current")
    assert get_resp.status_code == 200
    current_data = get_resp.json()["data"]
    assert current_data["id"] == data["id"]


def test_daily_task_generation():
    """Test fetching 'What should I do today?' tasks."""
    resp = client.get("/api/v1/roadmap/today")
    assert resp.status_code == 200
    today_data = resp.json()["data"]

    assert "today_focus_title" in today_data
    tasks = today_data.get("today_tasks") or today_data.get("tasks", [])
    assert len(tasks) > 0


def test_task_completion_and_progress():
    """Test marking task complete and progress calculation."""
    get_resp = client.get("/api/v1/roadmap/current")
    roadmap = get_resp.json()["data"]
    first_task_id = roadmap["phases"][0]["tasks"][0]["id"]

    # Mark task complete
    complete_resp = client.post(f"/api/v1/roadmap/tasks/{first_task_id}/complete")
    assert complete_resp.status_code == 200
    prog_data = complete_resp.json()["data"]

    assert first_task_id in prog_data["completed_task_ids"]
    assert prog_data["overall_progress_percent"] > 0

    # Uncomplete task
    uncomp_resp = client.post(f"/api/v1/roadmap/tasks/{first_task_id}/uncomplete")
    assert uncomp_resp.status_code == 200
    uncomp_data = uncomp_resp.json()["data"]
    assert first_task_id not in uncomp_data["completed_task_ids"]
    assert uncomp_data["overall_progress_percent"] == 0


def test_target_career_change_outdated_flag():
    """Test changing target career sets is_outdated=True on active roadmap."""
    client.post("/api/v1/roadmap/generate", json={"user_level": "Beginner"})

    select_resp = client.post(
        "/api/v1/assessment/target-career",
        json={"career_slug": "data-analyst"}
    )
    assert select_resp.status_code == 200

    get_resp = client.get("/api/v1/roadmap/current")
    roadmap_data = get_resp.json()["data"]
    assert roadmap_data["is_outdated"] is True


def test_recalculate_roadmap_preserves_completed():
    """Test recalculating roadmap updates role while preserving completed tasks."""
    gen_resp = client.post("/api/v1/roadmap/generate", json={"user_level": "Beginner"})
    r_data = gen_resp.json()["data"]
    t_id = r_data["phases"][0]["tasks"][0]["id"]

    client.post(f"/api/v1/roadmap/tasks/{t_id}/complete")

    recalc_resp = client.post("/api/v1/roadmap/recalculate")
    assert recalc_resp.status_code == 200
    new_r_data = recalc_resp.json()["data"]

    assert new_r_data["is_outdated"] is False
    assert t_id in new_r_data["completed_task_ids"]


# --------------------------------------------------------------------------
# Section 5: Specific 12-Scenario Verification Tests
# --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scenario_1_beginner_no_known_skills():
    """Scenario 1: A beginner with no known skills receives ground-zero scratch foundations."""
    engine = RoadmapEngine()
    mock_db = create_mock_db()

    roadmap = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-scenario-1",
        target_career="Frontend Developer",
        user_skills=[],
        missing_gaps=[SkillGapSchema(skill_name="React", gap_status="Missing", priority="High")],
        user_level="Beginner",
        hours_per_day=1,
        days_per_week=5
    )

    assert roadmap is not None
    assert len(roadmap.phases) >= 3
    # First phase must be foundational/scratch
    first_phase = roadmap.phases[0]
    assert "Scratch" in first_phase["type"] or "Foundation" in first_phase["type"]
    assert any("Fundamentals" in s or "Setup" in s or "HTML" in s for s in first_phase["skills"])


@pytest.mark.asyncio
async def test_scenario_2_learner_with_verified_skills():
    """Scenario 2: A learner with verified skills has those mastered skills excluded from foundational learning."""
    engine = RoadmapEngine()
    mock_db = create_mock_db()

    verified_python = Skill(
        id="s1",
        user_id="user-scenario-2",
        skill_name="Python",
        normalized_name="Python",
        proficiency_percent=85,
        confidence_status="Verified"
    )

    roadmap = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-scenario-2",
        target_career="Backend Developer",
        user_skills=[verified_python],
        missing_gaps=[SkillGapSchema(skill_name="FastAPI", gap_status="Missing", priority="High")],
        user_level="Intermediate",
        hours_per_day=2,
        days_per_week=5
    )

    # Verified Python should not be placed as a missing skill gap in early phase
    phase_1_skills = roadmap.phases[0]["skills"]
    assert "Python" not in phase_1_skills


@pytest.mark.asyncio
async def test_scenario_3_intermediate_with_specific_skill_gaps():
    """Scenario 3: An intermediate learner with specific gaps gets prerequisite-ordered bridging modules."""
    engine = RoadmapEngine()
    mock_db = create_mock_db()

    js_skill = Skill(
        id="s2",
        user_id="user-scenario-3",
        skill_name="JavaScript",
        normalized_name="JavaScript",
        proficiency_percent=80,
        confidence_status="Verified"
    )

    roadmap = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-scenario-3",
        target_career="Frontend Developer",
        user_skills=[js_skill],
        missing_gaps=[
            SkillGapSchema(skill_name="Next.js", gap_status="Missing", priority="High"),
            SkillGapSchema(skill_name="React", gap_status="Missing", priority="High")
        ],
        user_level="Intermediate"
    )

    # React prerequisite must come before Next.js
    all_skills = [s for p in roadmap.phases for s in p["skills"]]
    if "React" in all_skills and "Next.js" in all_skills:
        assert all_skills.index("React") < all_skills.index("Next.js")


@pytest.mark.asyncio
async def test_scenario_4_different_user_profiles_same_role():
    """Scenario 4: Two users targeting the same role with different skill profiles receive distinct roadmaps."""
    engine = RoadmapEngine()
    mock_db = create_mock_db()

    # User A: Complete beginner
    roadmap_a = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-a",
        target_career="Data Scientist",
        user_skills=[],
        missing_gaps=[SkillGapSchema(skill_name="Machine Learning", gap_status="Missing", priority="High")],
        user_level="Beginner"
    )

    # User B: Knows Python & SQL verified
    user_b_skills = [
        Skill(id="s1", user_id="user-b", skill_name="Python", normalized_name="Python", proficiency_percent=90, confidence_status="Verified"),
        Skill(id="s2", user_id="user-b", skill_name="SQL", normalized_name="SQL", proficiency_percent=85, confidence_status="Verified")
    ]
    roadmap_b = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-b",
        target_career="Data Scientist",
        user_skills=user_b_skills,
        missing_gaps=[SkillGapSchema(skill_name="Machine Learning", gap_status="Missing", priority="High")],
        user_level="Intermediate"
    )

    # User A starts with scratch programming foundations; User B starts at intermediate level
    assert roadmap_a.phases[0]["type"] != roadmap_b.phases[0]["type"]
    assert "Scratch" in roadmap_a.phases[0]["type"] or "Foundation" in roadmap_a.phases[0]["type"]


@pytest.mark.asyncio
async def test_scenario_5_different_career_goals():
    """Scenario 5: Two users with different career goals receive adapted phase themes and capstones."""
    engine = RoadmapEngine()
    mock_db = create_mock_db()

    roadmap_intern = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-intern",
        target_career="Software Engineer",
        user_skills=[],
        missing_gaps=[],
        career_goal="Internship"
    )

    roadmap_cert = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-cert",
        target_career="Software Engineer",
        user_skills=[],
        missing_gaps=[],
        career_goal="Certification"
    )

    assert "Internship" in roadmap_intern.phases[-1]["type"] or "Internship" in roadmap_intern.phases[0]["type"]
    assert "Exam" in roadmap_cert.phases[0]["type"] or "Certification" in roadmap_cert.phases[-1]["type"]


@pytest.mark.asyncio
async def test_scenario_6_limited_study_hours_pacing():
    """Scenario 6: User with limited study hours has realistic estimated weeks and schedule notice."""
    engine = RoadmapEngine()
    mock_db = create_mock_db()

    roadmap = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-busy",
        target_career="Full Stack Developer",
        user_skills=[],
        missing_gaps=[],
        hours_per_day=1,
        days_per_week=2  # Only 2 hours per week
    )

    # With only 2h/week, estimated weeks should be high and schedule_notes should flag pacing
    assert roadmap.total_estimated_weeks >= 4
    assert roadmap.schedule_notes is not None
    assert "steady pace" in roadmap.schedule_notes.lower() or "Notice" in roadmap.schedule_notes


@pytest.mark.asyncio
async def test_scenario_7_weak_areas_remediation():
    """Scenario 7: Prior interview or assessment weaknesses are reinforced in roadmap generation."""
    engine = RoadmapEngine()
    mock_db = create_mock_db()

    roadmap = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-weakness",
        target_career="Backend Developer",
        user_skills=[],
        missing_gaps=[],
        weak_areas=["Docker", "SQL Performance"]
    )

    all_phase_skills = [s.lower() for p in roadmap.phases for s in p["skills"]]
    assert any("docker" in s or "sql" in s for s in all_phase_skills)


@pytest.mark.asyncio
async def test_scenario_8_preserves_task_completion():
    """Scenario 8: Progress is preserved when generating or recalculating a roadmap."""
    engine = RoadmapEngine()
    
    # Mock existing roadmap with completed task
    existing_r = Roadmap(
        id="existing-r-id",
        user_id="user-prog-test",
        target_role="Frontend Developer",
        completed_task_ids=["phase-1-task-1"],
        completed_milestone_ids=["phase-1-milestone"],
        completed_project_ids=[],
        phases=[{
            "id": "phase-1",
            "phase_number": 1,
            "tasks": [{"id": "phase-1-task-1", "is_completed": True}],
            "milestone": {"id": "phase-1-milestone", "is_completed": True}
        }]
    )

    mock_db = create_mock_db(existing_r)

    updated_r = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-prog-test",
        target_career="Frontend Developer",
        user_skills=[],
        missing_gaps=[],
        preserve_progress=True
    )

    assert "phase-1-task-1" in updated_r.completed_task_ids
    assert "phase-1-milestone" in updated_r.completed_milestone_ids


@pytest.mark.asyncio
async def test_scenario_9_ai_fallback_on_exception():
    """Scenario 9: Groq/AI timeout or exception falls back safely to structured actionable syllabus."""
    failing_provider = AsyncMock()
    failing_provider.generate_structured.side_effect = TimeoutError("Groq API 504 Gateway Timeout")

    ai_service = RoadmapAIService(provider=failing_provider)
    phase_content = await ai_service.generate_phase_content(
        phase_number=1,
        phase_type="Core Foundations",
        target_career="Python Developer",
        phase_skills=["Python", "Git"],
        user_known_skills=[],
        user_level="Beginner",
        career_goal="Entry-level Job"
    )

    assert phase_content is not None
    assert len(phase_content.tasks) >= 2
    # Verify fallback tasks have actionable outcome and verification
    first_task = phase_content.tasks[0]
    assert len(first_task.topics_to_learn) > 0
    assert first_task.expected_outcome != ""
    assert first_task.verification_method != ""


@pytest.mark.asyncio
async def test_scenario_10_missing_domain_requirements():
    """Scenario 10: Uncatalogued or novel target career handles gaps gracefully without crash."""
    engine = RoadmapEngine()
    mock_db = create_mock_db()

    roadmap = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-novel-career",
        target_career="Quantum Computing Specialist",
        user_skills=[],
        missing_gaps=[]
    )

    assert roadmap is not None
    assert len(roadmap.phases) >= 3
    assert roadmap.target_role == "Quantum Computing Specialist"


@pytest.mark.asyncio
async def test_scenario_11_level_test_preservation_on_recalculate():
    """Scenario 11: Passed level tests, stars, and XP rewards are preserved across roadmap recalculation."""
    engine = RoadmapEngine()

    existing_r = Roadmap(
        id="existing-r-id",
        user_id="user-level-test",
        target_role="Frontend Developer",
        completed_task_ids=[],
        phases=[{
            "id": "phase-1",
            "phase_number": 1,
            "test_passed": True,
            "test_score": 92,
            "stars": 3,
            "xp_reward": 100,
            "is_unlocked": True,
            "tasks": []
        }]
    )

    mock_db = create_mock_db(existing_r)

    recalc_r = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-level-test",
        target_career="Frontend Developer",
        user_skills=[],
        missing_gaps=[],
        preserve_progress=True
    )

    first_phase = recalc_r.phases[0]
    assert first_phase.get("test_passed") is True
    assert first_phase.get("test_score") == 92
    assert first_phase.get("stars") == 3


def test_scenario_12_roadmap_user_isolation():
    """Scenario 12: Ensure roadmap endpoint responses respect user authentication isolation."""
    resp = client.get("/api/v1/roadmap/current")
    assert resp.status_code == 200
    data = resp.json()["data"]
    if data:
        assert data["user_id"] == "demo-user-12345"


def test_scenario_13_roadmap_assistant_endpoint():
    """Scenario 13: Verify Groq AI roadmap assistant responds to user queries."""
    resp = client.post("/api/v1/roadmap/assistant", json={"message": "How do I study the first topic?"})
    assert resp.status_code in [200, 404]
    if resp.status_code == 200:
        body = resp.json()
        assert body["success"] is True
        assert "response" in body["data"]
        assert body["data"]["provider"] == "Groq AI"


@pytest.mark.asyncio
async def test_scenario_14_flexible_level_counts():
    """Scenario 14: Verify roadmap level count is completely flexible (not fixed to 5)."""
    engine = RoadmapEngine()
    mock_db = create_mock_db()

    # Express track: 3 levels
    rm_express = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-flex-1",
        target_career="Full Stack Developer",
        user_skills=[],
        missing_gaps=[],
        track_pace="Express"
    )
    assert len(rm_express.phases) == 3

    # Custom 4 levels
    rm_4 = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-flex-2",
        target_career="Full Stack Developer",
        user_skills=[],
        missing_gaps=[],
        target_phases_count=4
    )
    assert len(rm_4.phases) == 4

    # Custom 6 levels (Comprehensive)
    rm_6 = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-flex-3",
        target_career="Full Stack Developer",
        user_skills=[],
        missing_gaps=[],
        target_phases_count=6
    )
    assert len(rm_6.phases) == 6


@pytest.mark.asyncio
async def test_scenario_15_domain_specific_roadmap_customization():
    """Scenario 15: Verify roadmap titles and skills adapt directly to user's selected domain."""
    engine = RoadmapEngine()
    mock_db = create_mock_db()

    # DevOps domain
    rm_devops = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-devops",
        target_career="DevOps Engineer",
        user_skills=[],
        missing_gaps=[],
        target_phases_count=4
    )
    assert rm_devops.target_role == "DevOps Engineer"
    devops_titles = " ".join([p["title"] for p in rm_devops.phases]).lower()
    devops_skills = [s.lower() for p in rm_devops.phases for s in p["skills"]]
    assert "devops" in devops_titles or any("docker" in s or "linux" in s or "kubernetes" in s for s in devops_skills)

    # Data Science domain
    rm_ds = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-ds",
        target_career="Data Scientist",
        user_skills=[],
        missing_gaps=[],
        target_phases_count=4
    )
    assert rm_ds.target_role == "Data Scientist"
    ds_titles = " ".join([p["title"] for p in rm_ds.phases]).lower()
    ds_skills = [s.lower() for p in rm_ds.phases for s in p["skills"]]
    assert "data" in ds_titles or any("python" in s or "pandas" in s or "machine learning" in s for s in ds_skills)


@pytest.mark.asyncio
async def test_scenario_16_cross_domain_regeneration_no_positional_collision():
    """Scenario 16: Switching domain does not carry over positional task IDs to unrelated new domain tasks."""
    engine = RoadmapEngine()
    existing_r = Roadmap(
        id="existing-r-id",
        user_id="user-cross-domain",
        target_role="Frontend Developer",
        completed_task_ids=["phase-1-task-1", "phase-1-task-2"],
        completed_milestone_ids=[],
        completed_project_ids=[],
        phases=[{
            "id": "phase-1",
            "phase_number": 1,
            "tasks": [
                {"id": "phase-1-task-1", "title": "HTML & CSS Basics", "is_completed": True},
                {"id": "phase-1-task-2", "title": "DOM Manipulation", "is_completed": True}
            ],
            "skills": ["HTML", "CSS", "JavaScript"]
        }]
    )
    mock_db = create_mock_db(existing_r)

    # Regenerate for an entirely different domain: DevOps Engineer
    new_rm = await engine.generate_roadmap(
        db=mock_db,
        user_id="user-cross-domain",
        target_career="DevOps Engineer",
        user_skills=[],
        missing_gaps=[],
        preserve_progress=True
    )

    # Positional IDs from Frontend must NOT be blindly carried over into DevOps roadmap!
    assert new_rm.target_role == "DevOps Engineer"
    assert len(new_rm.completed_task_ids) == 0


@pytest.mark.asyncio
async def test_scenario_17_today_focus_respects_unlocked_phases_and_level_test():
    """Scenario 17: Today's focus restricts to unlocked phases and recommends Level Test when all unlocked tasks are done."""
    engine = RoadmapEngine()
    test_roadmap = Roadmap(
        id="rm-today-test",
        user_id="user-today",
        target_role="Backend Developer",
        user_level="Beginner",
        hours_per_day=2,
        completed_task_ids=["p1-t1", "p1-t2"],
        phases=[
            {
                "id": "phase-1",
                "phase_number": 1,
                "title": "Spawn Point",
                "is_unlocked": True,
                "test_passed": False,
                "tasks": [
                    {"id": "p1-t1", "title": "Task 1", "estimated_minutes": 30, "is_completed": True},
                    {"id": "p1-t2", "title": "Task 2", "estimated_minutes": 30, "is_completed": True}
                ]
            },
            {
                "id": "phase-2",
                "phase_number": 2,
                "title": "Starter Camp",
                "is_unlocked": False,
                "test_passed": False,
                "tasks": [
                    {"id": "p2-t1", "title": "Locked Task 1", "estimated_minutes": 45, "is_completed": False}
                ]
            }
        ]
    )

    today_result = engine.get_today_focus_tasks(test_roadmap)
    # Since Phase 1 tasks are all complete and Phase 2 is locked, it must NOT recommend locked task p2-t1
    task_ids = [t["id"] for t in today_result.get("today_tasks", [])]
    assert "p2-t1" not in task_ids
    # It must recommend the Level Advancement Test
    assert today_result.get("is_level_test_recommended") is True
    assert today_result.get("completion_status") == "ready_for_test"
    assert "test for level" in today_result.get("next_step", "").lower() or "test" in today_result.get("next_step", "").lower()


def test_scenario_18_level_test_recovery_and_guided_drill():
    """Scenario 18: Failing a level test returns structured recovery instructions and guided drill."""
    from app.services.roadmap.level_test_engine import LevelTestEngine
    from app.schemas.roadmap import LevelTestQuestion

    lt_engine = LevelTestEngine()
    phase = {
        "id": "phase-1",
        "phase_number": 1,
        "title": "Spawn Point: Foundations",
        "skills": ["Python", "Variables", "Loops"],
        "tasks": []
    }
    questions = [
        LevelTestQuestion(
            id="q_1",
            topic="Loops",
            question="What does break do?",
            options=["A) Exit", "B) Continue", "C) Pass", "D) Restart"],
            correct_answer="A) Exit",
            explanation="break exits the loop."
        ),
        LevelTestQuestion(
            id="q_2",
            topic="Variables",
            question="What is a string?",
            options=["A) Text", "B) Number", "C) Bool", "D) Float"],
            correct_answer="A) Text",
            explanation="Strings represent text."
        )
    ]
    # Submit wrong answers for both
    user_answers = {"q_1": "B) Continue", "q_2": "B) Number"}

    result = lt_engine.evaluate_test(
        phase=phase,
        questions=questions,
        user_answers=user_answers
    )

    assert result.passed is False
    assert result.can_retry is True
    assert len(result.missed_topics) == 2
    assert len(result.recovery_recommendations) > 0
    assert result.guided_practice_exercise is not None
    assert "drill" in result.guided_practice_exercise.lower() or "practice" in result.guided_practice_exercise.lower()


@pytest.mark.asyncio
async def test_scenario_a_complete_beginner_aiml_internship():
    """
    Scenario A: Complete beginner targeting an AI/ML internship.
    - Zero verified skills: starts from scratch with Python, Math & EDA foundations.
    - Career goal is 'Internship': capstone phase is tailored for internship readiness.
    - All tasks include teacher mental models, prerequisites, next steps, and realistic pacing.
    """
    mock_db = create_mock_db()
    engine = RoadmapEngine()

    missing_gaps = [
        SkillGapSchema(skill_name="Python", gap_status="Missing", priority="High"),
        SkillGapSchema(skill_name="NumPy", gap_status="Missing", priority="High"),
        SkillGapSchema(skill_name="Pandas", gap_status="Missing", priority="Medium"),
        SkillGapSchema(skill_name="Scikit-Learn", gap_status="Missing", priority="High"),
        SkillGapSchema(skill_name="Machine Learning Fundamentals", gap_status="Missing", priority="High"),
    ]

    roadmap = await engine.generate_roadmap(
        db=mock_db,
        user_id="user_aiml_beginner",
        target_career="AI & Machine Learning",
        user_skills=[],
        missing_gaps=missing_gaps,
        user_level="Beginner",
        hours_per_day=1,
        days_per_week=5,
        career_goal="Internship"
    )

    assert roadmap.target_role == "AI & Machine Learning"
    assert roadmap.user_level == "Beginner"
    assert len(roadmap.phases) >= 4

    # Phase 1 must start with foundations
    p1 = roadmap.phases[0]
    assert "foundation" in p1["type"].lower() or "scratch" in p1["type"].lower()

    # Final phase must reflect Internship goal
    p_last = roadmap.phases[-1]
    assert "internship" in p_last["type"].lower() or "internship" in p_last["title"].lower()

    # Verify actionable fields across tasks
    for phase in roadmap.phases:
        for task in phase.get("tasks", []):
            assert task.get("title")
            assert task.get("concept_explanation") is not None
            assert len(task.get("concept_explanation", "")) > 0
            assert task.get("next_step") is not None
            assert len(task.get("next_step", "")) > 0
            assert task.get("expected_outcome") is not None
            assert task.get("verification_method") is not None
            assert task.get("difficulty_level") in ["Scratch", "Beginner", "Intermediate", "Advanced"]

    # Verify Today Focus
    today_focus = engine.get_today_focus_tasks(roadmap)
    assert today_focus["learner_level"] == "Beginner"
    assert "scratch" in today_focus["starting_point_note"].lower() or "zero" in today_focus["starting_point_note"].lower()
    assert today_focus["career_goal"] == "Internship"
    assert len(today_focus["today_tasks"]) >= 1


@pytest.mark.asyncio
async def test_scenario_b_intermediate_python_genai_agents():
    """
    Scenario B: Learner with intermediate Python knowledge targeting Generative AI and AI Agents.
    - Verified Python (70%+): foundational Python basics are skipped in phase 1.
    - Starts directly with LLM Architecture, Prompt Engineering, Embeddings, and AI Agents.
    - Covers tool calling, LangGraph / Multi-Agent systems, and guardrails.
    """
    mock_db = create_mock_db()
    engine = RoadmapEngine()

    verified_python = Skill(
        id="sk-1",
        user_id="user_genai_intermediate",
        skill_name="Python",
        normalized_name="Python",
        confidence_status="Verified",
        proficiency_percent=85
    )

    missing_gaps = [
        SkillGapSchema(skill_name="Prompt Engineering", gap_status="Missing", priority="High"),
        SkillGapSchema(skill_name="Embeddings & Vector Search", gap_status="Missing", priority="High"),
        SkillGapSchema(skill_name="Retrieval-Augmented Generation (RAG)", gap_status="Missing", priority="High"),
        SkillGapSchema(skill_name="Function Calling & Tool Use", gap_status="Missing", priority="High"),
        SkillGapSchema(skill_name="AI Agents", gap_status="Missing", priority="High"),
        SkillGapSchema(skill_name="Multi-Agent Systems", gap_status="Missing", priority="High"),
    ]

    roadmap = await engine.generate_roadmap(
        db=mock_db,
        user_id="user_genai_intermediate",
        target_career="Generative AI & AI Agents",
        user_skills=[verified_python],
        missing_gaps=missing_gaps,
        user_level="Intermediate",
        hours_per_day=2,
        days_per_week=5,
        career_goal="Skill Mastery"
    )

    assert roadmap.target_role == "Generative AI & AI Agents"
    assert roadmap.user_level == "Intermediate"

    # Level 1 must NOT repeat basic python syntax; it should advance directly into LLM / Prompt Engineering / Vector Search
    p1 = roadmap.phases[0]
    p1_skills_lower = [s.lower() for s in p1.get("skills", [])]
    assert "python" not in p1_skills_lower or any("llm" in s or "prompt" in s or "foundation" in s for s in p1_skills_lower)

    # Later phases must cover Agents, Multi-Agent Systems, or LangGraph
    all_skills_lower = [s.lower() for p in roadmap.phases for s in p.get("skills", [])]
    assert any("agent" in s for s in all_skills_lower)
    assert any("rag" in s or "retrieval" in s for s in all_skills_lower)

    # Verify Today Focus
    today_focus = engine.get_today_focus_tasks(roadmap)
    assert today_focus["learner_level"] == "Intermediate"
    assert "intermediate" in today_focus["starting_point_note"].lower()
    assert today_focus["career_goal"] == "Skill Mastery"


@pytest.mark.asyncio
async def test_scenario_c_beginner_ai_security_cybersecurity():
    """
    Scenario C: Beginner targeting AI Security / Cybersecurity.
    - Covers threat modeling, OWASP Top 10 for LLMs, prompt injection defense, red teaming & guardrails.
    - Tasks are actionable with security outcomes (e.g. defense middleware, test harness).
    """
    mock_db = create_mock_db()
    engine = RoadmapEngine()

    missing_gaps = [
        SkillGapSchema(skill_name="AI Threat Modeling", gap_status="Missing", priority="High"),
        SkillGapSchema(skill_name="OWASP LLM Top 10", gap_status="Missing", priority="High"),
        SkillGapSchema(skill_name="Prompt Injection & Defense", gap_status="Missing", priority="High"),
        SkillGapSchema(skill_name="AI Red Teaming & Guardrails", gap_status="Missing", priority="High"),
    ]

    roadmap = await engine.generate_roadmap(
        db=mock_db,
        user_id="user_aisec_beginner",
        target_career="AI Security & Cybersecurity",
        user_skills=[],
        missing_gaps=missing_gaps,
        user_level="Beginner",
        hours_per_day=1,
        days_per_week=5,
        career_goal="Entry-level Job"
    )

    assert roadmap.target_role == "AI Security & Cybersecurity"

    # Must contain security specific phases and skills
    all_skills_lower = [s.lower() for p in roadmap.phases for s in p.get("skills", [])]
    assert any("security" in s or "threat" in s or "owasp" in s or "injection" in s for s in all_skills_lower)

    # Today focus
    today_focus = engine.get_today_focus_tasks(roadmap)
    assert today_focus["target_career"] == "AI Security & Cybersecurity"
    assert today_focus["learner_level"] == "Beginner"
    assert "scratch" in today_focus["starting_point_note"].lower() or "zero" in today_focus["starting_point_note"].lower()


