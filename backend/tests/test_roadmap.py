import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.roadmap.dependency_graph import topological_sort_skills, get_skill_prerequisites

client = TestClient(app)


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
    # Generate roadmap
    resp = client.post(
        "/api/v1/roadmap/generate",
        json={
            "user_level": "Beginner",
            "hours_per_day": 2,
            "days_per_week": 5,
            "preferred_learning_style": "Hands-on"
        }
    )
    assert resp.status_code == 200
    data = resp.json()["data"]

    assert "id" in data
    assert data["hours_per_day"] == 2
    assert data["overall_progress_percent"] == 0
    assert len(data["phases"]) >= 3

    # Get current roadmap
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
    # Ensure active roadmap exists
    client.post("/api/v1/roadmap/generate", json={"user_level": "Beginner"})

    # Change target career via assessment endpoint
    select_resp = client.post(
        "/api/v1/assessment/target-career",
        json={"career_slug": "data-analyst"}
    )
    assert select_resp.status_code == 200

    # Get current roadmap - should now be flagged as outdated
    get_resp = client.get("/api/v1/roadmap/current")
    roadmap_data = get_resp.json()["data"]
    assert roadmap_data["is_outdated"] == True


def test_recalculate_roadmap_preserves_completed():
    """Test recalculating roadmap updates role while preserving completed tasks."""
    gen_resp = client.post("/api/v1/roadmap/generate", json={"user_level": "Beginner"})
    r_data = gen_resp.json()["data"]
    t_id = r_data["phases"][0]["tasks"][0]["id"]

    client.post(f"/api/v1/roadmap/tasks/{t_id}/complete")

    # Recalculate roadmap
    recalc_resp = client.post("/api/v1/roadmap/recalculate")
    assert recalc_resp.status_code == 200
    new_r_data = recalc_resp.json()["data"]

    assert new_r_data["is_outdated"] == False
    assert t_id in new_r_data["completed_task_ids"]
