"""
Integration test suite for Firebase persistence and user data isolation.

Covers:
1. Firebase User Profile persistence (UserRepository)
2. Career Assessment persistence (AssessmentRepository)
3. Resume In-Memory processing & Firebase Storage (DocumentExtractor + ResumeRepository)
4. Skills & Evidence persistence (SkillsRepository)
5. Roadmap persistence & task toggles (RoadmapRepository)
6. Adaptive Interview persistence (InterviewRepository)
7. Digital Twin & Readiness snapshots persistence (DigitalTwinRepository)
8. Saved Jobs & Application Tracker persistence (JobsRepository)
9. Strict User Isolation / IDOR prevention across two distinct Firebase UIDs
10. Verification that backend/uploads/resumes/ contains NO permanent user files
11. API route integration with authenticated Firebase Bearer tokens
"""

import os
import io
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.firestore.client import FirestoreClient
from app.services.firestore.user_repo import UserRepository
from app.services.firestore.assessment_repo import AssessmentRepository
from app.services.firestore.resume_repo import ResumeRepository
from app.services.firestore.skills_repo import SkillsRepository
from app.services.firestore.roadmap_repo import RoadmapRepository
from app.services.firestore.interview_repo import InterviewRepository
from app.services.firestore.digital_twin_repo import DigitalTwinRepository
from app.services.firestore.jobs_repo import JobsRepository
from app.services.resume.extractor import DocumentExtractor

client = TestClient(app)

UID_ALICE = "firebase-user-alice-111"
UID_BOB = "firebase-user-bob-222"


@pytest.mark.asyncio
async def test_user_profile_persistence():
    """Verify UserProfile creation and retrieval in Firestore."""
    profile_data = {
        "email": "alice@firebase.test",
        "full_name": "Alice Engineer",
        "target_career": "Full Stack Developer",
        "primary_archetype": "Systems Builder",
        "job_readiness_score": 85,
        "has_completed_assessment": True
    }
    saved = await UserRepository.upsert_user(UID_ALICE, profile_data)
    assert saved["uid"] == UID_ALICE

    retrieved = await UserRepository.get_user(UID_ALICE)
    assert retrieved is not None
    assert retrieved["email"] == "alice@firebase.test"
    assert retrieved["target_career"] == "Full Stack Developer"
    assert retrieved["job_readiness_score"] == 85


@pytest.mark.asyncio
async def test_assessment_persistence():
    """Verify Assessment responses and completion saved and queried under users/{uid}."""
    session_id = "assessment-sess-001"
    session_payload = {
        "status": "COMPLETED",
        "current_step": 6,
        "selected_target_career": "Full Stack Developer",
        "computed_archetype": "Systems Builder",
        "dimension_answers": {
            "q1": {"option_text": "Building scalable backend services"}
        },
        "ai_analysis_json": {
            "primary_archetype": "Systems Builder",
            "readiness_score": 85
        }
    }
    await AssessmentRepository.save_assessment(UID_ALICE, session_id, session_payload)

    retrieved = await AssessmentRepository.get_assessment(UID_ALICE, session_id)
    assert retrieved is not None
    assert retrieved["status"] == "COMPLETED"
    assert retrieved["computed_archetype"] == "Systems Builder"

    latest_comp = await AssessmentRepository.get_latest_completed_assessment(UID_ALICE)
    assert latest_comp is not None
    assert latest_comp["id"] == session_id

    has_comp = await AssessmentRepository.has_completed_assessment(UID_ALICE)
    assert has_comp is True


@pytest.mark.asyncio
async def test_resume_in_memory_and_storage_persistence():
    """
    Verify resume processing occurs in memory and uploads to Firebase Storage,
    and NO permanent files remain in backend/uploads/resumes/.
    """
    extractor = DocumentExtractor()
    import pymupdf
    pdf_doc = pymupdf.open()
    page = pdf_doc.new_page()
    page.insert_text((50, 72), "Alice Engineer - Full Stack Developer\nSkills: Python, FastAPI, React, SQL, TypeScript\nExperience in developing scalable cloud applications.")
    resume_content = pdf_doc.tobytes()
    pdf_doc.close()

    class MockUploadFile:
        filename = "alice_resume.pdf"
        file = io.BytesIO(resume_content)
        content_type = "application/pdf"

        async def read(self):
            return resume_content

    mock_file = MockUploadFile()
    storage_path, unique_filename, text = await extractor.process_uploaded_file(mock_file, UID_ALICE)

    # 1. Storage path format verification
    assert f"users/{UID_ALICE}/resumes/" in storage_path
    assert unique_filename.endswith(".pdf")
    assert "Alice Engineer" in text
    assert "FastAPI" in text

    # 2. Verify file exists in Firebase Storage
    storage_bytes = await FirestoreClient.download_file(storage_path)
    assert storage_bytes == resume_content

    # 3. Verify no permanent files on local disk
    local_upload_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "uploads", "resumes")
    )
    if os.path.exists(local_upload_dir):
        remaining_files = [f for f in os.listdir(local_upload_dir) if not f.startswith(".")]
        assert len(remaining_files) == 0, f"Found unexpected permanent files: {remaining_files}"

    # 4. Save metadata to Firestore ResumeRepository
    resume_id = "resume-alice-001"
    resume_doc = {
        "filename": unique_filename,
        "storage_path": storage_path,
        "overall_ats_score": 88,
        "target_career_name": "Full Stack Developer",
        "target_match_percentage": 90,
        "ats_breakdown_json": {"keyword_score": 90, "formatting_score": 85},
        "parsed_skills": [{"name": "Python"}, {"name": "FastAPI"}, {"name": "React"}]
    }
    await ResumeRepository.save_resume(UID_ALICE, resume_id, resume_doc)

    latest_resume = await ResumeRepository.get_latest_resume(UID_ALICE)
    assert latest_resume is not None
    assert latest_resume["overall_ats_score"] == 88
    assert latest_resume["storage_path"] == storage_path


@pytest.mark.asyncio
async def test_skills_and_evidence_persistence():
    """Verify user skills and verified evidence persistence."""
    skill_data = {
        "skill_name": "FastAPI",
        "category": "Backend",
        "proficiency_percent": 90,
        "confidence_status": "Verified",
        "evidence_sources": ["Resume Extraction", "Practice Quiz"]
    }
    saved_sk = await SkillsRepository.upsert_skill_by_name(UID_ALICE, "FastAPI", skill_data)
    assert saved_sk["skill_name"] == "FastAPI"

    evidence = {
        "source": "Mock Interview Evaluation",
        "description": "Demonstrated deep knowledge of async concurrency",
        "confidence_weight": 0.95
    }
    await SkillsRepository.add_evidence(UID_ALICE, saved_sk["id"], evidence)

    fetched_sk = await SkillsRepository.get_skill(UID_ALICE, saved_sk["id"])
    assert fetched_sk is not None
    assert len(fetched_sk.get("evidences", [])) == 1
    assert fetched_sk["evidences"][0]["source"] == "Mock Interview Evaluation"


@pytest.mark.asyncio
async def test_roadmap_persistence():
    """Verify Roadmap persistence, phase tracking, and task toggle."""
    roadmap_id = "roadmap-alice-001"
    roadmap_payload = {
        "target_role": "Full Stack Developer",
        "overall_progress_percent": 25,
        "is_active": True,
        "completed_task_ids": ["task-1"],
        "phases": [
            {
                "id": "phase-1",
                "title": "Phase 1: Backend Architecture",
                "progress_percent": 50,
                "tasks": [
                    {"id": "task-1", "title": "Setup FastAPI Server", "is_completed": True},
                    {"id": "task-2", "title": "Async Database Sessions", "is_completed": False}
                ]
            }
        ]
    }
    await RoadmapRepository.save_roadmap(UID_ALICE, roadmap_id, roadmap_payload)

    active_rm = await RoadmapRepository.get_active_roadmap(UID_ALICE)
    assert active_rm is not None
    assert active_rm["id"] == roadmap_id
    assert active_rm["target_role"] == "Full Stack Developer"

    # Toggle task-2
    updated = await RoadmapRepository.toggle_task(UID_ALICE, roadmap_id, "task-2")
    assert "task-2" in updated.get("completed_task_ids", [])


@pytest.mark.asyncio
async def test_interview_persistence():
    """Verify adaptive interview session persistence in Firestore."""
    session_id = "interview-alice-001"
    interview_payload = {
        "target_role": "Full Stack Developer",
        "mode": "Technical",
        "difficulty": "Intermediate",
        "is_completed": True,
        "overall_score": 82,
        "category_scores": {"technical": 85, "communication": 80},
        "readiness_status": "READY",
        "readiness_explanation": "Solid performance across all questions."
    }
    await InterviewRepository.save_session(UID_ALICE, session_id, interview_payload)

    fetched_session = await InterviewRepository.get_session(UID_ALICE, session_id)
    assert fetched_session is not None
    assert fetched_session["overall_score"] == 82
    assert fetched_session["readiness_status"] == "READY"


@pytest.mark.asyncio
async def test_digital_twin_and_readiness_persistence():
    """Verify Career Digital Twin, readiness snapshot, achievements, and weekly report persistence."""
    # 1. Twin Profile
    twin_data = {
        "readiness_score": 84,
        "target_role": "Full Stack Developer",
        "sub_scores": {"skill": 85, "resume": 88, "interview": 82}
    }
    await DigitalTwinRepository.save_digital_twin(UID_ALICE, twin_data)
    fetched_twin = await DigitalTwinRepository.get_digital_twin(UID_ALICE)
    assert fetched_twin is not None
    assert fetched_twin["readiness_score"] == 84

    # 2. Historical Snapshot
    snapshot_payload = {
        "snapshot_date": "2026-09-28",
        "overall_readiness_score": 84,
        "skill_readiness": 85,
        "resume_readiness": 88
    }
    await DigitalTwinRepository.save_snapshot(UID_ALICE, "2026-09-28", snapshot_payload)
    snapshots = await DigitalTwinRepository.list_snapshots(UID_ALICE)
    assert len(snapshots) >= 1
    assert snapshots[0]["overall_readiness_score"] == 84

    # 3. Achievements
    achievement_payload = {"title": "First Assessment Completed", "icon": "trophy"}
    await DigitalTwinRepository.save_achievement(UID_ALICE, "ach-assessment-1", achievement_payload)
    fetched_ach = await DigitalTwinRepository.list_achievements(UID_ALICE)
    assert len(fetched_ach) >= 1
    assert fetched_ach[0]["title"] == "First Assessment Completed"

    # 4. Weekly Report
    report = {"week_number": 39, "summary": "Great progress on backend tasks"}
    await DigitalTwinRepository.save_weekly_report(UID_ALICE, "week-39", report)
    fetched_rep = await DigitalTwinRepository.get_latest_weekly_report(UID_ALICE)
    assert fetched_rep is not None
    assert fetched_rep["week_number"] == 39


@pytest.mark.asyncio
async def test_jobs_and_applications_persistence():
    """Verify saved jobs and job applications in Firestore."""
    # 1. Saved Job
    job_id = "job-backend-engineer-01"
    await JobsRepository.save_job(UID_ALICE, job_id, {"notes": "Top tier company"})
    saved_jobs = await JobsRepository.get_saved_jobs(UID_ALICE)
    assert len(saved_jobs) >= 1
    assert saved_jobs[0]["job_id"] == job_id

    # 2. Job Application
    app_id = "app-001"
    app_payload = {
        "job_id": job_id,
        "job_title": "Senior Backend Engineer",
        "company": "Tech Corp",
        "status": "Applied",
        "applied_date": "2026-09-28"
    }
    await JobsRepository.save_application(UID_ALICE, app_id, app_payload)
    apps = await JobsRepository.get_applications(UID_ALICE)
    assert len(apps) >= 1
    assert apps[0]["id"] == app_id
    assert apps[0]["status"] == "Applied"


@pytest.mark.asyncio
async def test_user_isolation_and_idor_prevention():
    """
    CRITICAL SECURITY TEST:
    Verify that User B cannot read or access User A's Firestore records or resumes.
    """
    # 1. User B should have NO profile
    bob_user = await UserRepository.get_user(UID_BOB)
    assert bob_user is None

    # 2. User B should have NO assessments
    bob_assessments = await AssessmentRepository.list_assessments(UID_BOB)
    assert len(bob_assessments) == 0
    bob_comp = await AssessmentRepository.get_latest_completed_assessment(UID_BOB)
    assert bob_comp is None

    # 3. User B should NOT see Alice's assessment
    alice_assessment = await AssessmentRepository.get_assessment(UID_BOB, "assessment-sess-001")
    assert alice_assessment is None

    # 4. User B should have NO resumes
    bob_resumes = await ResumeRepository.list_resumes(UID_BOB)
    assert len(bob_resumes) == 0
    alice_resume_from_bob = await ResumeRepository.get_resume(UID_BOB, "resume-alice-001")
    assert alice_resume_from_bob is None

    # 5. User B should NOT be able to access Alice's resume file path in storage
    alice_latest = await ResumeRepository.get_latest_resume(UID_ALICE)
    assert alice_latest is not None
    # User B storage root is users/firebase-user-bob-222/
    assert not alice_latest["storage_path"].startswith(f"users/{UID_BOB}/")

    # 6. User B should have NO skills
    bob_skills = await SkillsRepository.list_skills(UID_BOB)
    assert len(bob_skills) == 0

    # 7. User B should have NO active roadmap
    bob_roadmap = await RoadmapRepository.get_active_roadmap(UID_BOB)
    assert bob_roadmap is None

    # 8. User B should have NO interview sessions
    bob_sessions = await InterviewRepository.list_sessions(UID_BOB)
    assert len(bob_sessions) == 0

    # 9. User B should have NO saved jobs or applications
    bob_saved_jobs = await JobsRepository.get_saved_jobs(UID_BOB)
    assert len(bob_saved_jobs) == 0
    bob_apps = await JobsRepository.get_applications(UID_BOB)
    assert len(bob_apps) == 0


def test_api_routes_with_firebase_token():
    """Verify existing protected API routes function seamlessly with Firebase Bearer tokens."""
    mock_uid = "firebase-auth-test-user-333"

    with patch("app.core.firebase.verify_firebase_id_token") as mock_verify:
        mock_verify.return_value = {
            "uid": mock_uid,
            "email": "testuser333@firebase.test",
            "name": "Auth Test User",
            "auth_time": 1700000000,
        }

        # 1. /api/v1/auth/me
        res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer valid-firebase-token"}
        )
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["success"] is True
        assert json_data["data"]["id"] == mock_uid

        # 2. /api/v1/assessment/status
        res_assess = client.get(
            "/api/v1/assessment/status",
            headers={"Authorization": "Bearer valid-firebase-token"}
        )
        assert res_assess.status_code == 200
        assert res_assess.json()["success"] is True

        # 3. /api/v1/skills
        res_skills = client.get(
            "/api/v1/skills",
            headers={"Authorization": "Bearer valid-firebase-token"}
        )
        assert res_skills.status_code == 200
        assert res_skills.json()["success"] is True

        # 4. /api/v1/roadmap/current
        res_rm = client.get(
            "/api/v1/roadmap/current",
            headers={"Authorization": "Bearer valid-firebase-token"}
        )
        assert res_rm.status_code == 200
        assert res_rm.json()["success"] is True

        # 5. /api/v1/jobs/saved
        res_jobs = client.get(
            "/api/v1/jobs/saved",
            headers={"Authorization": "Bearer valid-firebase-token"}
        )
        assert res_jobs.status_code == 200
        assert res_jobs.json()["success"] is True
