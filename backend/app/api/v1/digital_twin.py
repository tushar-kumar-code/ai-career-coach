"""
Digital Twin API Router
========================
All endpoints under /api/v1/digital-twin/
Integrates with existing auth pattern (get_current_user_id) and APIResponse wrapper.
"""
import datetime
import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.health import APIResponse
from app.models.digital_twin import ReadinessSnapshot, UserAchievement
from app.models.weekly_report import WeeklyCareerReport
from app.services.digital_twin.twin_service import DigitalTwinService
from app.services.digital_twin.readiness_engine import ReadinessEngine
from app.services.digital_twin.gap_analyzer import GapAnalyzer
from app.services.digital_twin.recommendation_engine import RecommendationEngine
from app.services.digital_twin.achievement_engine import AchievementEngine
from app.services.digital_twin.weekly_report_engine import WeeklyReportEngine

logger = logging.getLogger(__name__)
router = APIRouter()

twin_service = DigitalTwinService()
readiness_engine = ReadinessEngine()
gap_analyzer = GapAnalyzer()
recommendation_engine = RecommendationEngine()
achievement_engine = AchievementEngine()
weekly_report_engine = WeeklyReportEngine()


@router.get(
    "/profile",
    response_model=APIResponse,
    summary="Get full Career Digital Twin profile with all sub-scores, gaps, strengths, and next action",
)
async def get_digital_twin_profile(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Returns the complete Career Digital Twin.
    Auto-computes from live data; caches for 1 hour; saves daily snapshot.
    """
    try:
        result = await twin_service.get_or_compute(db, user_id)
        return APIResponse(
            success=True,
            message="Career Digital Twin computed successfully.",
            data=result,
        )
    except Exception as e:
        logger.error(f"Digital twin profile error for {user_id}: {e}")
        return APIResponse(success=False, message=str(e), data=None)


@router.get(
    "/readiness",
    response_model=APIResponse,
    summary="Get current career readiness score and sub-score breakdown",
)
async def get_readiness_score(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Returns current readiness scores computed from live DB evidence."""
    try:
        scores = await readiness_engine.compute(db, user_id)
        return APIResponse(
            success=True,
            message="Readiness scores computed.",
            data=scores,
        )
    except Exception as e:
        logger.error(f"Readiness score error: {e}")
        return APIResponse(success=False, message=str(e), data=None)


@router.get(
    "/readiness/history",
    response_model=APIResponse,
    summary="Get historical readiness score snapshots for trend charts",
)
async def get_readiness_history(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Returns up to 30 daily readiness snapshots for progress trend visualization."""
    try:
        cutoff = datetime.date.today() - datetime.timedelta(days=30)
        result = await db.execute(
            select(ReadinessSnapshot)
            .where(ReadinessSnapshot.user_id == user_id, ReadinessSnapshot.snapshot_date >= cutoff)
            .order_by(ReadinessSnapshot.snapshot_date.asc())
        )
        snapshots = result.scalars().all()

        history = [
            {
                "date": str(s.snapshot_date),
                "overall": s.overall_readiness_score,
                "skill": s.skill_readiness,
                "resume": s.resume_readiness,
                "interview": s.interview_readiness,
                "roadmap": s.roadmap_progress,
                "job_match": s.job_match_readiness,
                "portfolio": s.portfolio_readiness,
            }
            for s in snapshots
        ]

        return APIResponse(
            success=True,
            message=f"Returned {len(history)} historical snapshots.",
            data=history,
        )
    except Exception as e:
        logger.error(f"Readiness history error: {e}")
        return APIResponse(success=False, message=str(e), data=None)


@router.get(
    "/gaps",
    response_model=APIResponse,
    summary="Get prioritized career gap analysis: skill gaps, resume gaps, interview weaknesses",
)
async def get_gap_analysis(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Returns prioritized gaps sorted by career impact from real DB evidence."""
    try:
        result = await gap_analyzer.analyze(db, user_id)
        return APIResponse(
            success=True,
            message="Gap analysis completed.",
            data=result,
        )
    except Exception as e:
        logger.error(f"Gap analysis error: {e}")
        return APIResponse(success=False, message=str(e), data=None)


@router.get(
    "/next-action",
    response_model=APIResponse,
    summary="Get the single best recommended next action based on actual user data",
)
async def get_next_action(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Deterministically selects the highest-impact next action from real user data."""
    try:
        scores = await readiness_engine.compute(db, user_id)
        gaps = await gap_analyzer.analyze(db, user_id)
        action = await recommendation_engine.get_next_action(
            db=db,
            user_id=user_id,
            sub_scores={
                "skill_readiness": scores["skill_readiness"],
                "resume_readiness": scores["resume_readiness"],
                "interview_readiness": scores["interview_readiness"],
                "roadmap_progress": scores["roadmap_progress"],
                "job_match_readiness": scores["job_match_readiness"],
                "portfolio_readiness": scores["portfolio_readiness"],
            },
            priority_gaps=gaps["priority_gaps"],
        )
        return APIResponse(
            success=True,
            message="Next best action computed.",
            data=action,
        )
    except Exception as e:
        logger.error(f"Next action error: {e}")
        return APIResponse(success=False, message=str(e), data=None)


@router.get(
    "/achievements",
    response_model=APIResponse,
    summary="Get all earned user achievements based on real evidence",
)
async def get_achievements(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Returns achievements earned from verifiable DB facts only. No fabricated badges."""
    try:
        scores = await readiness_engine.compute(db, user_id)
        achievements = await achievement_engine.compute_achievements(
            db, user_id,
            overall_readiness_score=scores["overall_readiness_score"],
        )
        return APIResponse(
            success=True,
            message=f"Found {len(achievements)} earned achievements.",
            data=achievements,
        )
    except Exception as e:
        logger.error(f"Achievements error: {e}")
        return APIResponse(success=False, message=str(e), data=None)


@router.get(
    "/weekly-report",
    response_model=APIResponse,
    summary="Get the latest weekly career progress report",
)
async def get_weekly_report(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Generates (or retrieves) the weekly career report.
    Reports only actual changes -- never fabricates activity.
    """
    try:
        scores = await readiness_engine.compute(db, user_id)
        report = await weekly_report_engine.generate(db, user_id, scores)
        return APIResponse(
            success=True,
            message="Weekly career report generated.",
            data=report,
        )
    except Exception as e:
        logger.error(f"Weekly report error: {e}")
        return APIResponse(success=False, message=str(e), data=None)


@router.post(
    "/snapshot",
    response_model=APIResponse,
    summary="Manually trigger a readiness snapshot save",
)
async def save_snapshot(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Saves today''s readiness scores as a historical snapshot (upsert)."""
    try:
        import uuid
        scores = await readiness_engine.compute(db, user_id)
        today = datetime.date.today()

        # Check for existing today snapshot
        existing_res = await db.execute(
            select(ReadinessSnapshot).where(
                ReadinessSnapshot.user_id == user_id,
                ReadinessSnapshot.snapshot_date == today,
            )
        )
        existing = existing_res.scalar_one_or_none()

        if existing:
            existing.overall_readiness_score = scores["overall_readiness_score"]
            existing.skill_readiness = scores["skill_readiness"]
            existing.resume_readiness = scores["resume_readiness"]
            existing.interview_readiness = scores["interview_readiness"]
            existing.roadmap_progress = scores["roadmap_progress"]
            existing.job_match_readiness = scores["job_match_readiness"]
            existing.portfolio_readiness = scores["portfolio_readiness"]
            snapshot = existing
        else:
            snapshot = ReadinessSnapshot(
                id=str(uuid.uuid4()),
                user_id=user_id,
                snapshot_date=today,
                **{k: scores[k] for k in [
                    "overall_readiness_score", "skill_readiness", "resume_readiness",
                    "interview_readiness", "roadmap_progress", "job_match_readiness", "portfolio_readiness"
                ]},
            )
            db.add(snapshot)

        await db.commit()

        return APIResponse(
            success=True,
            message="Readiness snapshot saved.",
            data={
                "snapshot_date": str(today),
                "overall_readiness_score": scores["overall_readiness_score"],
            },
        )
    except Exception as e:
        logger.error(f"Snapshot save error: {e}")
        return APIResponse(success=False, message=str(e), data=None)
