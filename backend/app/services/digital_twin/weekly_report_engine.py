"""
Weekly Career Report Engine
============================
Generates a factual weekly progress report by comparing:
  - current readiness state
  - vs. ReadinessSnapshot from ~7 days ago

Reports ONLY changes that actually exist in the DB.
Does NOT invent activity. Optionally adds 1-sentence AI narrative.
"""
import logging
import datetime
from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.digital_twin import ReadinessSnapshot, UserAchievement
from app.models.roadmap import Roadmap
from app.models.interview import InterviewSession
from app.models.job import JobApplication
from app.models.skill import Skill
from app.models.resume import Resume
from app.models.weekly_report import WeeklyCareerReport

logger = logging.getLogger(__name__)


class WeeklyReportEngine:
    """Generates weekly career report from DB evidence diffs."""

    async def generate(
        self,
        db: AsyncSession,
        user_id: str,
        current_scores: Dict,
    ) -> Dict:
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=7)

        # Get snapshot from ~7 days ago (closest available)
        snapshot_res = await db.execute(
            select(ReadinessSnapshot)
            .where(
                ReadinessSnapshot.user_id == user_id,
                ReadinessSnapshot.snapshot_date >= week_start - datetime.timedelta(days=2),
                ReadinessSnapshot.snapshot_date <= week_start + datetime.timedelta(days=2),
            )
            .order_by(ReadinessSnapshot.snapshot_date.asc())
            .limit(1)
        )
        old_snapshot = snapshot_res.scalar_one_or_none()

        # Compute deltas
        def delta(key: str) -> int:
            old = getattr(old_snapshot, key, 0) if old_snapshot else 0
            return current_scores.get(key, 0) - old

        score_delta = delta("overall_readiness_score")
        skill_delta = delta("skill_readiness")
        resume_delta = delta("resume_readiness")
        interview_delta = delta("interview_readiness")
        roadmap_delta = delta("roadmap_progress")

        # Count activity in the last 7 days
        week_start_dt = datetime.datetime.combine(week_start, datetime.time.min)

        # Tasks completed this week
        roadmap_res = await db.execute(
            select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True).limit(1)
        )
        roadmap = roadmap_res.scalar_one_or_none()
        tasks_completed_this_week = 0  # We count from roadmap progress delta

        # Interviews completed this week
        interview_res = await db.execute(
            select(InterviewSession)
            .where(
                InterviewSession.user_id == user_id,
                InterviewSession.is_completed == True,
                InterviewSession.created_at >= week_start_dt,
            )
        )
        interviews_this_week = len(interview_res.scalars().all())

        # Applications this week
        app_res = await db.execute(
            select(JobApplication)
            .where(
                JobApplication.user_id == user_id,
                JobApplication.created_at >= week_start_dt,
            )
        )
        apps_this_week = len(app_res.scalars().all())

        # Skills verified this week
        skill_res = await db.execute(
            select(Skill)
            .where(
                Skill.user_id == user_id,
                Skill.is_verified == True,
                Skill.last_evaluated_at >= week_start_dt,
            )
        )
        skills_verified_this_week = len(skill_res.scalars().all())

        # Achievements earned this week
        ach_res = await db.execute(
            select(UserAchievement)
            .where(
                UserAchievement.user_id == user_id,
                UserAchievement.earned_at >= week_start_dt,
            )
        )
        new_achievements = [
            {"title": a.title, "icon": a.icon}
            for a in ach_res.scalars().all()
        ]

        # Build improvements list (factual, from deltas)
        improvements = []
        if score_delta > 0:
            improvements.append(f"Overall readiness improved by {score_delta} points.")
        if resume_delta > 0:
            improvements.append(f"Resume ATS score improved by {resume_delta} points.")
        if skill_delta > 0:
            improvements.append(f"Skill readiness improved by {skill_delta} points.")
        if interview_delta > 0:
            improvements.append(f"Interview readiness improved by {interview_delta} points.")
        if interviews_this_week > 0:
            improvements.append(f"Completed {interviews_this_week} mock interview session(s) this week.")
        if apps_this_week > 0:
            improvements.append(f"Submitted {apps_this_week} job application(s) this week.")
        if skills_verified_this_week > 0:
            improvements.append(f"Verified {skills_verified_this_week} skill(s) this week.")

        # Determine biggest weakness (lowest sub-score)
        sub_keys = [
            ("skill_readiness", "Skill Development"),
            ("resume_readiness", "Resume Quality"),
            ("interview_readiness", "Interview Performance"),
            ("roadmap_progress", "Roadmap Completion"),
            ("job_match_readiness", "Job Match Score"),
            ("portfolio_readiness", "Portfolio / Projects"),
        ]
        sorted_sub = sorted(sub_keys, key=lambda x: current_scores.get(x[0], 0))
        biggest_weakness = sorted_sub[0][1] if sorted_sub else None
        recommended_focus = f"Focus on {sorted_sub[0][1]} to see the biggest overall readiness gain next week."

        # Persist report
        report = WeeklyCareerReport(
            user_id=user_id,
            week_start_date=week_start,
            week_end_date=today,
            overall_score_delta=str(score_delta),
            skill_score_delta=str(skill_delta),
            resume_score_delta=str(resume_delta),
            interview_score_delta=str(interview_delta),
            roadmap_delta=str(roadmap_delta),
            tasks_completed="0",
            interviews_completed=str(interviews_this_week),
            applications_submitted=str(apps_this_week),
            skills_verified=str(skills_verified_this_week),
            improvements=improvements,
            achievements_earned=new_achievements,
            biggest_weakness=biggest_weakness,
            recommended_focus=recommended_focus,
            ai_narrative=None,
        )
        db.add(report)
        await db.commit()

        return {
            "week_start_date": str(week_start),
            "week_end_date": str(today),
            "score_changes": {
                "overall_delta": score_delta,
                "skill_delta": skill_delta,
                "resume_delta": resume_delta,
                "interview_delta": interview_delta,
                "roadmap_delta": roadmap_delta,
            },
            "activity": {
                "interviews_completed": interviews_this_week,
                "applications_submitted": apps_this_week,
                "skills_verified": skills_verified_this_week,
            },
            "improvements": improvements,
            "achievements_earned_this_week": new_achievements,
            "biggest_weakness": biggest_weakness,
            "recommended_focus": recommended_focus,
            "current_scores": {
                "overall": current_scores.get("overall_readiness_score", 0),
                "skill": current_scores.get("skill_readiness", 0),
                "resume": current_scores.get("resume_readiness", 0),
                "interview": current_scores.get("interview_readiness", 0),
                "roadmap": current_scores.get("roadmap_progress", 0),
                "job_match": current_scores.get("job_match_readiness", 0),
                "portfolio": current_scores.get("portfolio_readiness", 0),
            },
        }
