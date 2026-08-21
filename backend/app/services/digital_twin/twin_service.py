"""
Digital Twin Service (Orchestrator)
====================================
Assembles the full Career Digital Twin by calling all sub-services.
Handles upsert logic (once-per-day snapshot saving).
"""
import logging
import datetime
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.digital_twin import CareerDigitalTwin, ReadinessSnapshot
from app.models.profile import UserProfile
from app.models.assessment import AssessmentResponse
from app.services.digital_twin.readiness_engine import ReadinessEngine
from app.services.digital_twin.gap_analyzer import GapAnalyzer
from app.services.digital_twin.recommendation_engine import RecommendationEngine
from app.services.digital_twin.achievement_engine import AchievementEngine

logger = logging.getLogger(__name__)

readiness_engine = ReadinessEngine()
gap_analyzer = GapAnalyzer()
recommendation_engine = RecommendationEngine()
achievement_engine = AchievementEngine()


class DigitalTwinService:
    """Orchestrates computation and persistence of the Career Digital Twin."""

    async def get_or_compute(self, db: AsyncSession, user_id: str) -> Dict:
        """
        Returns the full Career Digital Twin.
        If today''s twin already exists and is recent (<1h), returns cached.
        Otherwise recomputes from live data and upserts.
        """
        today = datetime.date.today()
        now = datetime.datetime.utcnow()

        # Check if today''s twin already computed recently
        existing_res = await db.execute(
            select(CareerDigitalTwin).where(CareerDigitalTwin.user_id == user_id)
        )
        existing = existing_res.scalar_one_or_none()

        if existing:
            age_minutes = (now - existing.last_computed_at).total_seconds() / 60
            if age_minutes < 60:
                # Return cached within last hour
                return self._to_dict(existing)

        # --- Compute all sub-components ---

        # 1. Readiness scores
        readiness = await readiness_engine.compute(db, user_id)

        # 2. Gap analysis
        gaps = await gap_analyzer.analyze(db, user_id)

        # 3. Next best action
        next_action = await recommendation_engine.get_next_action(
            db, user_id,
            sub_scores={
                "skill_readiness": readiness["skill_readiness"],
                "resume_readiness": readiness["resume_readiness"],
                "interview_readiness": readiness["interview_readiness"],
                "roadmap_progress": readiness["roadmap_progress"],
                "job_match_readiness": readiness["job_match_readiness"],
                "portfolio_readiness": readiness["portfolio_readiness"],
            },
            priority_gaps=gaps["priority_gaps"],
        )

        # 4. Achievements
        achievements = await achievement_engine.compute_achievements(
            db, user_id,
            overall_readiness_score=readiness["overall_readiness_score"],
        )

        # 5. Target career + archetype from profile / assessment
        target_career = None
        primary_archetype = None
        experience_level = "Beginner"

        profile_res = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = profile_res.scalar_one_or_none()
        if profile:
            target_career = profile.target_career
            primary_archetype = profile.primary_archetype

        if not target_career:
            assess_res = await db.execute(
                select(AssessmentResponse)
                .where(AssessmentResponse.user_id == user_id, AssessmentResponse.status == "COMPLETED")
                .order_by(AssessmentResponse.created_at.desc())
                .limit(1)
            )
            assess = assess_res.scalar_one_or_none()
            if assess:
                target_career = assess.selected_target_career
                primary_archetype = assess.computed_archetype

        # 6. Upsert the twin record
        twin_data = {
            "overall_readiness_score": readiness["overall_readiness_score"],
            "readiness_label": readiness["readiness_label"],
            "skill_readiness": readiness["skill_readiness"],
            "resume_readiness": readiness["resume_readiness"],
            "interview_readiness": readiness["interview_readiness"],
            "roadmap_progress": readiness["roadmap_progress"],
            "job_match_readiness": readiness["job_match_readiness"],
            "portfolio_readiness": readiness["portfolio_readiness"],
            "target_career": target_career,
            "primary_archetype": primary_archetype,
            "experience_level": experience_level,
            "top_strengths": gaps["top_strengths"],
            "priority_gaps": gaps["priority_gaps"],
            "critical_missing_skills": gaps["critical_missing_skills"],
            "next_action": next_action,
            "evidence_summary": readiness["evidence_summary"],
            "last_computed_at": now,
            "snapshot_date": today,
        }

        if existing:
            for k, v in twin_data.items():
                setattr(existing, k, v)
        else:
            import uuid
            existing = CareerDigitalTwin(id=str(uuid.uuid4()), user_id=user_id, **twin_data)
            db.add(existing)

        # 7. Save daily snapshot (once per day)
        snap_res = await db.execute(
            select(ReadinessSnapshot).where(
                ReadinessSnapshot.user_id == user_id,
                ReadinessSnapshot.snapshot_date == today,
            )
        )
        existing_snap = snap_res.scalar_one_or_none()
        if not existing_snap:
            import uuid as _uuid
            snap = ReadinessSnapshot(
                id=str(_uuid.uuid4()),
                user_id=user_id,
                snapshot_date=today,
                overall_readiness_score=readiness["overall_readiness_score"],
                skill_readiness=readiness["skill_readiness"],
                resume_readiness=readiness["resume_readiness"],
                interview_readiness=readiness["interview_readiness"],
                roadmap_progress=readiness["roadmap_progress"],
                job_match_readiness=readiness["job_match_readiness"],
                portfolio_readiness=readiness["portfolio_readiness"],
            )
            db.add(snap)

        await db.commit()

        # Build full response dict
        result = self._to_dict(existing)
        result["achievements"] = achievements
        result["gaps"] = gaps
        return result

    def _to_dict(self, twin: CareerDigitalTwin) -> Dict:
        return {
            "user_id": twin.user_id,
            "overall_readiness_score": twin.overall_readiness_score,
            "readiness_label": twin.readiness_label,
            "sub_scores": {
                "skill_readiness": twin.skill_readiness,
                "resume_readiness": twin.resume_readiness,
                "interview_readiness": twin.interview_readiness,
                "roadmap_progress": twin.roadmap_progress,
                "job_match_readiness": twin.job_match_readiness,
                "portfolio_readiness": twin.portfolio_readiness,
            },
            "target_career": twin.target_career,
            "primary_archetype": twin.primary_archetype,
            "experience_level": twin.experience_level,
            "top_strengths": twin.top_strengths or [],
            "priority_gaps": twin.priority_gaps or [],
            "critical_missing_skills": twin.critical_missing_skills or [],
            "next_action": twin.next_action or {},
            "evidence_summary": twin.evidence_summary or {},
            "last_computed_at": twin.last_computed_at.isoformat() if twin.last_computed_at else None,
            "snapshot_date": str(twin.snapshot_date) if twin.snapshot_date else None,
        }
