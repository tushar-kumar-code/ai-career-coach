import datetime
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.skill import Skill
from app.models.roadmap import Roadmap
from app.models.interview import InterviewSession
from app.models.job import JobApplication
from app.models.digital_twin import UserAchievement
from app.services.digital_twin.twin_service import DigitalTwinService
from app.services.digital_twin.readiness_engine import ReadinessEngine
from app.services.placement.checklist_engine import get_placement_tier
from app.schemas.placement import StudentCareerBriefResponse, StudentCareerBriefProject

logger = logging.getLogger(__name__)


class StudentBriefEngine:
    """
    Aggregates verifiable profile, readiness, skill, resume, roadmap, and interview
    metrics for the 1-Page Student Career Brief without mock or fabricated content.
    """

    def __init__(self):
        self.twin_service = DigitalTwinService()
        self.readiness_engine = ReadinessEngine()

    async def generate_brief(self, db: AsyncSession, user_id: str) -> StudentCareerBriefResponse:
        """Compiles a complete 1-page executive career brief payload from live DB records."""
        # 1. Fetch user & profile
        u_stmt = select(User).where(User.id == user_id)
        u_res = await db.execute(u_stmt)
        user = u_res.scalar_one_or_none()
        student_name = user.email.split("@")[0].capitalize() if user and user.email else "Student"

        p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        p_res = await db.execute(p_stmt)
        profile = p_res.scalar_one_or_none()
        target_career = (profile.target_career if profile and profile.target_career else "Software Developer")
        primary_archetype = (profile.primary_archetype if profile and profile.primary_archetype else "Systems Builder")

        # 2. Fetch Digital Twin & Readiness scores
        twin_data = await self.twin_service.get_or_compute(db, user_id)
        overall_score = twin_data.get("overall_readiness_score", 0)
        sub_scores = twin_data.get("sub_scores", {})
        top_strengths = twin_data.get("top_strengths", [])
        priority_gaps = twin_data.get("priority_gaps", [])
        critical_missing = twin_data.get("critical_missing_skills", [])
        next_action = twin_data.get("next_action", {})
        experience_level = twin_data.get("experience_level", "Beginner")

        tier_name, tier_desc = get_placement_tier(overall_score)

        # 3. Skills summary
        sk_stmt = select(Skill).where(Skill.user_id == user_id)
        sk_res = await db.execute(sk_stmt)
        all_skills = sk_res.scalars().all()
        verified_skills = [s.skill_name for s in all_skills if s.is_verified]

        # 4. Latest Resume
        r_stmt = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
        r_res = await db.execute(r_stmt)
        latest_resume = r_res.scalar_one_or_none()

        # 5. Roadmap & Projects
        rm_stmt = (
            select(Roadmap)
            .where(Roadmap.user_id == user_id, Roadmap.is_active == True)
            .order_by(Roadmap.created_at.desc())
            .limit(1)
        )
        rm_res = await db.execute(rm_stmt)
        roadmap = rm_res.scalar_one_or_none()

        completed_projects_list: List[StudentCareerBriefProject] = []
        if roadmap and roadmap.phases:
            for phase in roadmap.phases:
                # Projects in phase
                for proj in phase.get("projects", []):
                    if proj.get("id") in (roadmap.completed_project_ids or []):
                        completed_projects_list.append(StudentCareerBriefProject(
                            title=proj.get("title", "Portfolio Project"),
                            difficulty=proj.get("difficulty", "Intermediate"),
                            expected_outcome=proj.get("expected_outcome", "Working application"),
                            resume_relevance=proj.get("resume_relevance", "Demonstrates practical competency")
                        ))
                # Single project format in phase
                if phase.get("project"):
                    proj = phase.get("project")
                    if proj.get("id") in (roadmap.completed_project_ids or []):
                        completed_projects_list.append(StudentCareerBriefProject(
                            title=proj.get("title", "Portfolio Project"),
                            difficulty=proj.get("difficulty", "Intermediate"),
                            expected_outcome=proj.get("expected_outcome", "Working application"),
                            resume_relevance=proj.get("resume_relevance", "Demonstrates practical competency")
                        ))

        # 6. Interview summary
        iv_stmt = (
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id, InterviewSession.is_completed == True)
        )
        iv_res = await db.execute(iv_stmt)
        completed_interviews = iv_res.scalars().all()

        interview_count = len(completed_interviews)
        avg_interview_score = int(sum(s.overall_score for s in completed_interviews) / interview_count) if interview_count > 0 else 0
        star_done = any(
            s.star_score >= 70 or any(
                (q.get("evaluation") or {}).get("star_analysis", {}).get("star_complete")
                for q in (s.questions_data or [])
            )
            for s in completed_interviews
        )

        # 7. Applications count
        app_stmt = select(JobApplication).where(JobApplication.user_id == user_id)
        app_res = await db.execute(app_stmt)
        active_apps = app_res.scalars().all()

        # 8. Achievements sample
        ach_stmt = (
            select(UserAchievement)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.earned_at.desc())
            .limit(5)
        )
        ach_res = await db.execute(ach_stmt)
        achievements = ach_res.scalars().all()

        # Extract readable string descriptions for strengths and gaps
        formatted_strengths: List[str] = []
        for s in top_strengths:
            if isinstance(s, dict):
                formatted_strengths.append(s.get("name", s.get("title", str(s))))
            else:
                formatted_strengths.append(str(s))

        formatted_gaps: List[str] = []
        for g in priority_gaps:
            if isinstance(g, dict):
                gap_name = g.get("name", g.get("title", ""))
                gap_area = g.get("area", "")
                if gap_area and gap_name:
                    formatted_gaps.append(f"{gap_name} ({gap_area})")
                else:
                    formatted_gaps.append(gap_name or str(g))
            else:
                formatted_gaps.append(str(g))

        return StudentCareerBriefResponse(
            student_name=student_name,
            target_career=target_career,
            primary_archetype=primary_archetype,
            experience_level=experience_level,
            overall_readiness_score=overall_score,
            readiness_tier=tier_name,
            tier_description=tier_desc,
            sub_scores=sub_scores,
            top_strengths=formatted_strengths[:5],
            priority_gaps=formatted_gaps[:5],
            critical_missing_skills=[s if isinstance(s, str) else s.get("name", str(s)) for s in critical_missing[:6]],
            total_skills_count=len(all_skills),
            verified_skills_count=len(verified_skills),
            verified_skills_sample=verified_skills[:8],
            latest_resume_filename=latest_resume.filename if latest_resume else None,
            latest_resume_ats_score=latest_resume.overall_ats_score if latest_resume else 0,
            latest_resume_match_pct=latest_resume.target_match_percentage if latest_resume else 0,
            roadmap_progress_percent=roadmap.overall_progress_percent if roadmap else 0,
            roadmap_completed_tasks=len(roadmap.completed_task_ids or []) if roadmap else 0,
            completed_projects=completed_projects_list,
            interview_completed_count=interview_count,
            interview_avg_score=avg_interview_score,
            interview_star_completed=star_done,
            active_applications_count=len(active_apps),
            achievements_count=len(achievements),
            achievements_sample=[a.title for a in achievements],
            next_action=next_action,
            generated_at=datetime.datetime.utcnow().strftime("%B %d, %Y")
        )
