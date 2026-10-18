import pytest
from tests.conftest import TestAsyncSessionLocal
from app.models.user import User
from app.models.profile import UserProfile
from app.models.skill import Skill
from app.models.roadmap import Roadmap
from app.services.roadmap.progress_sync import ProfileProgressSyncService
from app.services.ai.chat_context import build_candidate_chat_dossier, format_chat_system_instruction


@pytest.mark.asyncio
async def test_roadmap_task_completion_syncs_to_profile_and_ai_chat():
    """Verify that completing a roadmap task automatically updates user profile, skills, and chat dossier."""
    sync_service = ProfileProgressSyncService()

    async with TestAsyncSessionLocal() as session:
        user_id = "test-sync-user-001"

        # 1. Setup clean user and profile
        user = User(id=user_id, email="learningsync@example.com", full_name="Aarav Sharma")
        profile = UserProfile(
            user_id=user_id,
            target_career="Backend Engineer",
            primary_archetype="The Architect",
            job_readiness_score=30,
            skills_matrix={},
            evidence_points=[]
        )
        session.add(user)
        session.add(profile)

        # 2. Setup active roadmap with a phase and task
        task_id = "task_docker_101"
        roadmap = Roadmap(
            id="rm-sync-001",
            user_id=user_id,
            target_role="Backend Engineer",
            overall_progress_percent=25,
            is_active=True,
            completed_task_ids=[task_id],
            phases=[
                {
                    "id": "phase-devops",
                    "title": "Phase 2: Containerization & Cloud Deployment",
                    "skills": ["Docker", "DevOps"],
                    "tasks": [
                        {
                            "id": task_id,
                            "title": "Build Multi-Stage Docker Container for FastAPI",
                            "task_type": "Practice",
                            "topics_to_learn": ["Docker", "Containerization"],
                            "learning_focus": "Production DevOps",
                            "is_completed": True
                        }
                    ]
                }
            ]
        )
        session.add(roadmap)
        await session.commit()

        # 3. Trigger sync_task_completion_to_profile
        sync_result = await sync_service.sync_task_completion_to_profile(
            db=session,
            user_id=user_id,
            roadmap=roadmap,
            task_id=task_id,
            completed=True
        )

        assert sync_result["completed"] == True
        assert len(sync_result["learned_skills"]) > 0
        assert any("Docker" in s for s in sync_result["learned_skills"])

        # 4. Verify UserProfile was updated in DB
        await session.refresh(profile)
        assert profile.job_readiness_score > 0
        assert "recent_learned" in profile.skills_matrix
        assert len(profile.skills_matrix["recent_learned"]) > 0
        assert profile.skills_matrix["recent_learned"][0]["task_id"] == task_id
        assert len(profile.evidence_points) > 0

        # 5. Verify Skill records were created/updated
        from sqlalchemy import select
        skills = (await session.execute(select(Skill).where(Skill.user_id == user_id))).scalars().all()
        assert len(skills) > 0
        skill_names = [s.skill_name for s in skills]
        assert any("Docker" in s for s in skill_names)

        # 6. Verify AI Chat Dossier receives the live updated profile data
        dossier = await build_candidate_chat_dossier(session, user_id=user_id)
        assert dossier["name"] == "Aarav Sharma"
        assert dossier["target_career"] == "Backend Engineer"
        assert len(dossier["recent_learned_skills"]) > 0
        assert dossier["recent_learned_skills"][0]["task_title"] == "Build Multi-Stage Docker Container for FastAPI"

        # 7. Verify Groq AI System Instruction contains the learned skills and updated progress
        system_instruction = format_chat_system_instruction(dossier, language="en")
        assert "Aarav Sharma" in system_instruction
        assert "Backend Engineer" in system_instruction
        assert "Build Multi-Stage Docker Container for FastAPI" in system_instruction
        assert "Docker" in system_instruction


@pytest.mark.asyncio
async def test_level_test_and_drill_sync_to_profile():
    """Verify that level tests, drills, and interviews update user profile & evidence dynamically."""
    sync_service = ProfileProgressSyncService()

    async with TestAsyncSessionLocal() as session:
        user_id = "test-perf-user-002"

        user = User(id=user_id, email="perfuser@example.com", full_name="Priya Patel")
        profile = UserProfile(
            user_id=user_id,
            target_career="Frontend Developer",
            job_readiness_score=20,
            skills_matrix={},
            evidence_points=[]
        )
        session.add(user)
        session.add(profile)

        roadmap = Roadmap(
            id="rm-perf-002",
            user_id=user_id,
            target_role="Frontend Developer",
            overall_progress_percent=40,
            is_active=True,
            phases=[
                {
                    "phase_number": 1,
                    "title": "Phase 1: Modern React & TypeScript",
                    "skills": ["React", "TypeScript"],
                    "tasks": []
                }
            ]
        )
        session.add(roadmap)
        await session.commit()

        # 1. Level Test Sync
        test_sync = await sync_service.sync_level_test_to_profile(
            db=session,
            user_id=user_id,
            roadmap=roadmap,
            phase_number=1,
            test_score=85,
            passed=True,
            stars=3,
            xp_reward=150
        )
        assert test_sync["passed"] is True
        assert test_sync["test_score"] == 85

        await session.refresh(profile)
        assert len(profile.evidence_points) > 0
        assert any("Level Test" in ev for ev in profile.evidence_points)
        assert "recent_level_tests" in profile.skills_matrix
        assert profile.skills_matrix["recent_level_tests"][0]["score"] == 85

        # 2. Practice Drill Sync
        drill_sync = await sync_service.sync_practice_drill_to_profile(
            db=session,
            user_id=user_id,
            topic="React Hooks",
            is_correct=True,
            score=100
        )
        assert drill_sync["is_correct"] is True

        await session.refresh(profile)
        assert any("React Hooks" in ev for ev in profile.evidence_points)
        assert "recent_practice_drills" in profile.skills_matrix
        assert profile.skills_matrix["recent_practice_drills"][0]["score"] == 100

        # 3. Interview Sync
        interview_sync = await sync_service.sync_interview_to_profile(
            db=session,
            user_id=user_id,
            target_role="Frontend Developer",
            overall_score=82,
            category_scores={"technical": 85, "communication": 80}
        )
        assert interview_sync["overall_score"] == 82

        await session.refresh(profile)
        assert any("Interview" in ev for ev in profile.evidence_points)
        assert "recent_interviews" in profile.skills_matrix
        assert profile.skills_matrix["recent_interviews"][0]["overall_score"] == 82

