import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.health import APIResponse
from app.schemas.placement import PlacementChecklistResponse, StudentCareerBriefResponse
from app.services.placement.checklist_engine import PlacementChecklistEngine
from app.services.placement.brief_engine import StudentBriefEngine

logger = logging.getLogger(__name__)
router = APIRouter()

checklist_engine = PlacementChecklistEngine()
brief_engine = StudentBriefEngine()


@router.get(
    "/checklist",
    response_model=APIResponse[PlacementChecklistResponse],
    summary="Get 10-point Placement Readiness checklist evaluated from real DB evidence"
)
async def get_placement_checklist(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Returns the student's 10-point Placement Checklist with completion flags,
    live current values, target goals, and 1-click remediation actions.
    """
    try:
        data = await checklist_engine.evaluate_checklist(db, user_id)
        return APIResponse(
            success=True,
            message="Placement checklist evaluated successfully.",
            data=data
        )
    except Exception as e:
        logger.error(f"Placement checklist error for {user_id}: {e}", exc_info=True)
        return APIResponse(
            success=False,
            message=f"Failed to evaluate placement checklist: {str(e)}",
            data=None
        )


@router.get(
    "/brief",
    response_model=APIResponse[StudentCareerBriefResponse],
    summary="Get 1-Page Student Career Brief aggregating profile, verified skills, and interview readiness"
)
async def get_student_career_brief(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Compiles an executive 1-page Career Brief for student portfolio reviews,
    mentors, faculty, and college placement cells.
    """
    try:
        data = await brief_engine.generate_brief(db, user_id)
        return APIResponse(
            success=True,
            message="Student career brief generated successfully.",
            data=data
        )
    except Exception as e:
        logger.error(f"Student brief error for {user_id}: {e}", exc_info=True)
        return APIResponse(
            success=False,
            message=f"Failed to generate student career brief: {str(e)}",
            data=None
        )
