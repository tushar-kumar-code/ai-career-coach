"""
Achievement Engine
==================
Awards achievements based on REAL DB evidence only.
Never creates an achievement without proof from the database.

Each achievement is checked idempotently -- won''t double-award.
"""
import logging
import datetime
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.skill import Skill
from app.models.resume import Resume
from app.models.roadmap import Roadmap
from app.models.interview import InterviewSession
from app.models.digital_twin import UserAchievement
from app.models.job import JobApplication

logger = logging.getLogger(__name__)

# Achievement definitions: key -> (title, description, icon, category, evidence_check_description)
ACHIEVEMENT_DEFINITIONS = {
    "resume_uploaded": (
        "Resume Uploaded",
        "Successfully uploaded and analyzed your resume.",
        "file-text",
        "Resume",
        "Resume record found in database",
    ),
    "ats_score_70": (
        "ATS Ready",
        "Achieved an ATS score of 70% or higher.",
        "shield-check",
        "Resume",
        "Resume ATS score >= 70",
    ),
    "first_skill_verified": (
        "First Skill Verified",
        "Had your first skill verified through assessment or evidence.",
        "award",
        "Skills",
        "At least one Skill with is_verified=True",
    ),
    "five_skills_verified": (
        "Skill Builder",
        "Verified 5 or more skills in your profile.",
        "zap",
        "Skills",
        "Five or more Skills with is_verified=True",
    ),
    "roadmap_started": (
        "Roadmap Started",
        "Generated your personalized career roadmap.",
        "map",
        "Roadmap",
        "Active Roadmap record exists",
    ),
    "first_task_completed": (
        "First Step Taken",
        "Completed your first roadmap task.",
        "check-circle",
        "Roadmap",
        "completed_task_ids has at least 1 entry",
    ),
    "milestone_reached": (
        "Milestone Reached",
        "Completed a roadmap milestone.",
        "flag",
        "Roadmap",
        "completed_milestone_ids has at least 1 entry",
    ),
    "first_project_completed": (
        "Project Builder",
        "Completed your first portfolio project.",
        "code",
        "Portfolio",
        "completed_project_ids has at least 1 entry",
    ),
    "first_interview_completed": (
        "First Mock Interview",
        "Completed your first AI mock interview session.",
        "mic",
        "Interview",
        "At least one completed InterviewSession",
    ),
    "interview_score_70": (
        "Interview Confident",
        "Achieved an interview score of 70+ in a session.",
        "trending-up",
        "Interview",
        "At least one completed session with overall_score >= 70",
    ),
    "interview_readiness_improved": (
        "Interview Readiness Improved",
        "Average interview score exceeds 60 across multiple sessions.",
        "bar-chart-2",
        "Interview",
        "average interview score > 60 across >= 2 sessions",
    ),
    "first_application": (
        "First Application",
        "Submitted your first job application.",
        "send",
        "Jobs",
        "At least one JobApplication record",
    ),
    "job_ready": (
        "Job Ready",
        "Achieved an overall career readiness score of 75 or above.",
        "star",
        "Career",
        "Overall readiness score >= 75",
    ),
    "assessment_completed": (
        "Career Discovered",
        "Completed the Career Discovery Assessment.",
        "compass",
        "Discovery",
        "AssessmentResponse with status=COMPLETED",
    ),
}


class AchievementEngine:
    """Checks evidence and awards/returns user achievements."""

    async def compute_achievements(
        self,
        db: AsyncSession,
        user_id: str,
        overall_readiness_score: int = 0,
    ) -> List[Dict]:
        """
        Evaluate all possible achievements against real DB evidence.
        Awards any newly earned achievements to DB and returns all earned ones.
        """
        # Get already-earned achievement keys
        earned_result = await db.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        already_earned = {a.achievement_key: a for a in earned_result.scalars().all()}

        # Gather evidence
        earned_keys = set(already_earned.keys())
        new_keys: List[str] = []

        # Resume evidence
        resume_res = await db.execute(
            select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc()).limit(1)
        )
        resume = resume_res.scalar_one_or_none()

        if resume:
            new_keys.append("resume_uploaded")
            if resume.overall_ats_score >= 70:
                new_keys.append("ats_score_70")

        # Skills evidence
        skills_res = await db.execute(select(Skill).where(Skill.user_id == user_id))
        all_skills = skills_res.scalars().all()
        verified_skills = [s for s in all_skills if s.is_verified]

        if len(verified_skills) >= 1:
            new_keys.append("first_skill_verified")
        if len(verified_skills) >= 5:
            new_keys.append("five_skills_verified")

        # Roadmap evidence
        roadmap_res = await db.execute(
            select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True).limit(1)
        )
        roadmap = roadmap_res.scalar_one_or_none()

        if roadmap:
            new_keys.append("roadmap_started")
            if len(roadmap.completed_task_ids or []) >= 1:
                new_keys.append("first_task_completed")
            if len(roadmap.completed_milestone_ids or []) >= 1:
                new_keys.append("milestone_reached")
            if len(roadmap.completed_project_ids or []) >= 1:
                new_keys.append("first_project_completed")

        # Interview evidence
        interview_res = await db.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id, InterviewSession.is_completed == True)
        )
        completed_sessions = interview_res.scalars().all()

        if len(completed_sessions) >= 1:
            new_keys.append("first_interview_completed")
        if any(s.overall_score >= 70 for s in completed_sessions):
            new_keys.append("interview_score_70")
        if len(completed_sessions) >= 2:
            avg_score = sum(s.overall_score for s in completed_sessions) / len(completed_sessions)
            if avg_score > 60:
                new_keys.append("interview_readiness_improved")

        # Job application evidence
        app_res = await db.execute(
            select(JobApplication).where(JobApplication.user_id == user_id).limit(1)
        )
        first_app = app_res.scalar_one_or_none()
        if first_app:
            new_keys.append("first_application")

        # Overall readiness
        if overall_readiness_score >= 75:
            new_keys.append("job_ready")

        # Award newly earned achievements to DB
        now = datetime.datetime.utcnow()
        for key in set(new_keys):
            if key not in earned_keys and key in ACHIEVEMENT_DEFINITIONS:
                defn = ACHIEVEMENT_DEFINITIONS[key]
                achievement = UserAchievement(
                    user_id=user_id,
                    achievement_key=key,
                    title=defn[0],
                    description=defn[1],
                    icon=defn[2],
                    category=defn[3],
                    evidence_description=defn[4],
                    earned_at=now,
                )
                db.add(achievement)
                already_earned[key] = achievement

        await db.commit()

        # Return all earned achievements as dicts
        return [
            {
                "achievement_key": a.achievement_key,
                "title": a.title,
                "description": a.description,
                "icon": a.icon,
                "category": a.category,
                "evidence_description": a.evidence_description,
                "earned_at": a.earned_at.isoformat() if a.earned_at else None,
            }
            for a in already_earned.values()
        ]
