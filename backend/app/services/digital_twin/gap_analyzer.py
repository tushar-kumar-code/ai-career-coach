"""
Gap Analyzer
============
Reads real DB data from Skill, Resume, InterviewSession, and Roadmap
to produce a prioritized list of gaps. Never invents gaps.
"""
import logging
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.skill import Skill
from app.models.resume import Resume
from app.models.interview import InterviewSession
from app.models.roadmap import Roadmap

logger = logging.getLogger(__name__)

PRIORITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


class GapAnalyzer:
    """Produces prioritized career gap analysis from live DB evidence."""

    async def analyze(self, db: AsyncSession, user_id: str) -> Dict:
        gaps = []
        strengths = []
        critical_missing_skills = []

        # --- Skill gaps ---
        skills_result = await db.execute(
            select(Skill).where(Skill.user_id == user_id)
        )
        all_skills = skills_result.scalars().all()

        for skill in all_skills:
            if skill.is_gap:
                gaps.append({
                    "area": "Skill Gap",
                    "name": skill.skill_name,
                    "category": skill.category,
                    "priority": skill.priority or "Medium",
                    "current_level": skill.proficiency_level,
                    "required_level": skill.target_required_level or "Intermediate",
                    "reason": skill.priority_reason or f"{skill.skill_name} is required for your target career.",
                    "source": "skill_matrix",
                })
                if skill.priority in ("Critical", "High"):
                    critical_missing_skills.append(skill.skill_name)
            elif skill.proficiency_percent >= 70 or skill.is_verified:
                strengths.append({
                    "name": skill.skill_name,
                    "category": skill.category,
                    "proficiency": skill.proficiency_percent,
                    "level": skill.proficiency_level,
                    "verified": skill.is_verified,
                })

        # Sort strengths by proficiency desc
        strengths.sort(key=lambda x: x["proficiency"], reverse=True)

        # --- Resume missing skills ---
        resume_result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
        latest_resume = resume_result.scalar_one_or_none()

        if latest_resume and latest_resume.missing_skills:
            for ms in (latest_resume.missing_skills or [])[:5]:
                skill_name = ms if isinstance(ms, str) else ms.get("skill", str(ms))
                # Only add if not already in gaps
                if not any(g["name"] == skill_name for g in gaps):
                    gaps.append({
                        "area": "Resume Gap",
                        "name": skill_name,
                        "category": "Technical",
                        "priority": "High",
                        "current_level": "Not Mentioned",
                        "required_level": "Mentioned in Resume",
                        "reason": f"{skill_name} is missing from your resume but required for your target role.",
                        "source": "resume_analysis",
                    })
                if skill_name not in critical_missing_skills:
                    critical_missing_skills.append(skill_name)

        if latest_resume and latest_resume.overall_ats_score < 60:
            gaps.append({
                "area": "Resume Quality",
                "name": "ATS Score Below 60",
                "category": "Resume",
                "priority": "High",
                "current_level": f"{latest_resume.overall_ats_score}%",
                "required_level": "70%+",
                "reason": "ATS score below 60 significantly reduces application visibility.",
                "source": "ats_engine",
            })

        # --- Interview weak areas ---
        interview_result = await db.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id, InterviewSession.is_completed == True)
        )
        completed_sessions = interview_result.scalars().all()

        interview_weak_topics: List[str] = []
        for session in completed_sessions:
            for weak in (session.weak_areas or []):
                topic = weak if isinstance(weak, str) else weak.get("topic", str(weak))
                if topic and topic not in interview_weak_topics:
                    interview_weak_topics.append(topic)

        for topic in interview_weak_topics[:3]:
            gaps.append({
                "area": "Interview Weakness",
                "name": topic,
                "category": "Interview",
                "priority": "Medium",
                "current_level": "Weak",
                "required_level": "Proficient",
                "reason": f"You scored low on '{topic}' in mock interviews. Practice this topic.",
                "source": "interview_sessions",
            })

        # --- Roadmap incomplete phases ---
        roadmap_result = await db.execute(
            select(Roadmap)
            .where(Roadmap.user_id == user_id, Roadmap.is_active == True)
            .order_by(Roadmap.created_at.desc())
            .limit(1)
        )
        active_roadmap = roadmap_result.scalar_one_or_none()

        if active_roadmap and active_roadmap.phases:
            completed_task_ids = set(active_roadmap.completed_task_ids or [])
            for phase in (active_roadmap.phases or []):
                phase_tasks = phase.get("tasks", [])
                phase_task_ids = {t.get("id") for t in phase_tasks if t.get("id")}
                incomplete = phase_task_ids - completed_task_ids
                if incomplete and len(incomplete) > len(phase_task_ids) // 2:
                    gaps.append({
                        "area": "Roadmap Phase",
                        "name": phase.get("name", "Unnamed Phase"),
                        "category": "Learning",
                        "priority": "Medium",
                        "current_level": f"{len(phase_task_ids)-len(incomplete)}/{len(phase_task_ids)} tasks done",
                        "required_level": "All tasks complete",
                        "reason": f"Phase '{phase.get('name')}' is mostly incomplete. Completing it will unlock next skills.",
                        "source": "roadmap",
                    })

        # Sort gaps by priority
        gaps.sort(key=lambda x: PRIORITY_ORDER.get(x["priority"], 99))

        return {
            "top_strengths": strengths[:5],
            "priority_gaps": gaps[:10],
            "critical_missing_skills": list(set(critical_missing_skills))[:8],
            "total_gaps_found": len(gaps),
            "total_strengths_found": len(strengths),
        }
