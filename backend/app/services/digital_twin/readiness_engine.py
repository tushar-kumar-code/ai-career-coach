"""
Career Readiness Engine
=======================
Deterministic 0-100 score computed entirely from real DB evidence.

SCORING FORMULA (weights must sum to 1.0):
  skill_readiness        * 0.30
  resume_readiness       * 0.20
  interview_readiness    * 0.20
  roadmap_progress       * 0.15
  job_match_readiness    * 0.10
  portfolio_readiness    * 0.05

Each sub-score is 0-100. If the user has not used a module yet, that
sub-score is 0 (no penalty escalation -- it just hasn't contributed yet).
"""
import logging
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.skill import Skill
from app.models.resume import Resume
from app.models.roadmap import Roadmap
from app.models.interview import InterviewSession
from app.models.profile import UserProfile

logger = logging.getLogger(__name__)

WEIGHTS = {
    "skill_readiness": 0.30,
    "resume_readiness": 0.20,
    "interview_readiness": 0.20,
    "roadmap_progress": 0.15,
    "job_match_readiness": 0.10,
    "portfolio_readiness": 0.05,
}

READINESS_LABELS = [
    (85, "Job Ready"),
    (70, "Nearly Ready"),
    (50, "In Progress"),
    (25, "Early Stage"),
    (0,  "Not Started"),
]


def _label(score: int) -> str:
    for threshold, label in READINESS_LABELS:
        if score >= threshold:
            return label
    return "Not Started"


class ReadinessEngine:
    """Computes per-user career readiness scores from live DB evidence."""

    async def compute(self, db: AsyncSession, user_id: str) -> Dict:
        """
        Returns a dict with overall score, all sub-scores, label,
        and evidence_summary showing what data was found.
        """
        sub_scores = {}
        evidence = {}

        # --- 1. Skill Readiness (30%) ---
        # Formula: (verified_skills / total_skills) * proficiency_avg
        # If no skills exist: 0
        skills_result = await db.execute(
            select(Skill).where(Skill.user_id == user_id)
        )
        all_skills = skills_result.scalars().all()

        total_skills = len(all_skills)
        if total_skills > 0:
            verified = [s for s in all_skills if s.is_verified]
            non_gap = [s for s in all_skills if not s.is_gap]
            avg_proficiency = sum(s.proficiency_percent for s in all_skills) / total_skills
            # Skill readiness = 50% weight on verified ratio + 50% on proficiency
            verified_ratio = len(verified) / total_skills
            skill_score = int((verified_ratio * 50) + (avg_proficiency * 0.5))
            skill_score = min(skill_score, 100)
            evidence["skills"] = {
                "total": total_skills,
                "verified": len(verified),
                "avg_proficiency": round(avg_proficiency, 1),
            }
        else:
            skill_score = 0
            evidence["skills"] = {"total": 0, "verified": 0, "avg_proficiency": 0}

        sub_scores["skill_readiness"] = skill_score

        # --- 2. Resume Readiness (20%) ---
        # Formula: latest resume overall_ats_score
        resume_result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
        latest_resume = resume_result.scalar_one_or_none()

        if latest_resume:
            resume_score = min(latest_resume.overall_ats_score, 100)
            evidence["resume"] = {
                "filename": latest_resume.filename,
                "ats_score": latest_resume.overall_ats_score,
                "target_match": latest_resume.target_match_percentage,
            }
        else:
            resume_score = 0
            evidence["resume"] = {"filename": None, "ats_score": 0}

        sub_scores["resume_readiness"] = resume_score

        # --- 3. Interview Readiness (20%) ---
        # Formula: average overall_score across all completed sessions
        interview_result = await db.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id, InterviewSession.is_completed == True)
        )
        completed_sessions = interview_result.scalars().all()

        if completed_sessions:
            avg_interview = sum(s.overall_score for s in completed_sessions) / len(completed_sessions)
            interview_score = int(avg_interview)
            evidence["interviews"] = {
                "completed_count": len(completed_sessions),
                "avg_score": round(avg_interview, 1),
            }
        else:
            interview_score = 0
            evidence["interviews"] = {"completed_count": 0, "avg_score": 0}

        sub_scores["interview_readiness"] = interview_score

        # --- 4. Roadmap Progress (15%) ---
        # Formula: roadmap.overall_progress_percent from active roadmap
        roadmap_result = await db.execute(
            select(Roadmap)
            .where(Roadmap.user_id == user_id, Roadmap.is_active == True)
            .order_by(Roadmap.created_at.desc())
            .limit(1)
        )
        active_roadmap = roadmap_result.scalar_one_or_none()

        if active_roadmap:
            roadmap_score = min(active_roadmap.overall_progress_percent, 100)
            completed_tasks = len(active_roadmap.completed_task_ids or [])
            completed_projects = len(active_roadmap.completed_project_ids or [])
            completed_milestones = len(active_roadmap.completed_milestone_ids or [])
            evidence["roadmap"] = {
                "target_role": active_roadmap.target_role,
                "progress_percent": active_roadmap.overall_progress_percent,
                "completed_tasks": completed_tasks,
                "completed_projects": completed_projects,
                "completed_milestones": completed_milestones,
            }
        else:
            roadmap_score = 0
            completed_tasks = 0
            completed_projects = 0
            evidence["roadmap"] = {"target_role": None, "progress_percent": 0}

        sub_scores["roadmap_progress"] = roadmap_score

        # --- 5. Job Match Readiness (10%) ---
        # Formula: profile.job_readiness_score (already computed by job matching engine)
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()

        if profile and profile.job_readiness_score:
            job_match_score = min(profile.job_readiness_score, 100)
            evidence["job_match"] = {
                "job_readiness_score": profile.job_readiness_score,
                "target_career": profile.target_career,
            }
        else:
            job_match_score = 0
            evidence["job_match"] = {"job_readiness_score": 0}

        sub_scores["job_match_readiness"] = job_match_score

        # --- 6. Portfolio Readiness (5%) ---
        # Formula: completed_project_ids count (capped at 3 projects = 100%)
        if active_roadmap:
            project_count = len(active_roadmap.completed_project_ids or [])
            portfolio_score = min(int((project_count / 3) * 100), 100)
            evidence["portfolio"] = {"completed_projects": project_count}
        else:
            portfolio_score = 0
            evidence["portfolio"] = {"completed_projects": 0}

        sub_scores["portfolio_readiness"] = portfolio_score

        # --- Compute weighted overall score ---
        overall = sum(
            sub_scores[key] * weight
            for key, weight in WEIGHTS.items()
        )
        overall_score = int(round(overall))

        return {
            "overall_readiness_score": overall_score,
            "readiness_label": _label(overall_score),
            **sub_scores,
            "evidence_summary": evidence,
            "weights": WEIGHTS,
        }
