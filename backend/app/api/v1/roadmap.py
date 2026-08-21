from sqlalchemy.orm.attributes import flag_modified
import copy, uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.roadmap import Roadmap
from app.models.profile import UserProfile
from app.schemas.health import APIResponse
from app.schemas.roadmap import (
    RoadmapDetailResponse,
    RoadmapGenerateRequest,
    RoadmapPreferencesRequest,
    DailyTasksResponse,
    RoadmapProgressResponse,
    RoadmapPhaseSchema,
    FocusSkillRequest,
    FocusSkillResponse,
    RoadmapTaskSchema
)
from app.services.roadmap.roadmap_engine import RoadmapEngine
from app.services.roadmap.daily_task_engine import DailyTaskEngine

router = APIRouter()
roadmap_engine = RoadmapEngine()
daily_task_engine = DailyTaskEngine()


def _to_detail_response(r: Roadmap) -> RoadmapDetailResponse:
    """Helper converting Roadmap SQLAlchemy model to RoadmapDetailResponse Pydantic schema."""
    phases_raw = r.phases or []
    phases_schemas = [RoadmapPhaseSchema(**p) for p in phases_raw]

    return RoadmapDetailResponse(
        id=r.id,
        user_id=r.user_id,
        target_career_id=r.target_career_id,
        target_role=r.target_role,
        user_level=r.user_level or "Beginner",
        overall_progress_percent=r.overall_progress_percent or 0,
        is_active=r.is_active,
        is_outdated=r.is_outdated,
        hours_per_day=r.hours_per_day,
        days_per_week=r.days_per_week,
        preferred_learning_style=r.preferred_learning_style,
        total_estimated_weeks=r.total_estimated_weeks,
        phases=phases_schemas,
        completed_task_ids=r.completed_task_ids or [],
        completed_milestone_ids=r.completed_milestone_ids or [],
        completed_project_ids=r.completed_project_ids or []
    )


@router.post(
    "/generate",
    response_model=APIResponse[RoadmapDetailResponse],
    summary="Generate personalized, dependency-ordered career roadmap"
)
async def generate_roadmap(
    req: RoadmapGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    roadmap = await roadmap_engine.generate_user_roadmap(
        db=db,
        user_id=user_id,
        user_level=req.user_level or "Beginner",
        hours_per_day=req.hours_per_day or 1,
        days_per_week=req.days_per_week or 5,
        preferred_learning_style=req.preferred_learning_style or "Hands-on",
        target_career_id=req.target_career_id
    )

    return APIResponse(
        success=True,
        message="Personalized career roadmap generated successfully",
        data=_to_detail_response(roadmap)
    )


@router.get(
    "/current",
    response_model=APIResponse[Optional[RoadmapDetailResponse]],
    summary="Get user's active career roadmap"
)
async def get_current_roadmap(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # Check profile target_career vs active roadmap target_role
    stmt_prof = select(UserProfile).where(UserProfile.user_id == user_id)
    res_prof = await db.execute(stmt_prof)
    profile = res_prof.scalar_one_or_none()

    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        return APIResponse(
            success=True,
            message="No active roadmap found",
            data=None
        )

    # Check if target career was changed on profile
    if profile and profile.target_career and profile.target_career != roadmap.target_role:
        if not roadmap.is_outdated:
            roadmap.is_outdated = True
            await db.commit()
            await db.refresh(roadmap)

    return APIResponse(
        success=True,
        message="Current career roadmap retrieved",
        data=_to_detail_response(roadmap)
    )


@router.get(
    "/phases",
    response_model=APIResponse[List[RoadmapPhaseSchema]],
    summary="Get phase breakdown for active roadmap"
)
async def get_roadmap_phases(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=404, detail="No active roadmap found for user")

    phases = [RoadmapPhaseSchema(**p) for p in (roadmap.phases or [])]
    return APIResponse(
        success=True,
        message="Roadmap phases retrieved successfully",
        data=phases
    )


@router.get(
    "/today",
    response_model=APIResponse[DailyTasksResponse],
    summary="Get 'What should I do today?' daily tasks"
)
async def get_today_tasks(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        # Generate default roadmap if none exists
        roadmap = await roadmap_engine.generate_user_roadmap(db=db, user_id=user_id)

    today_data = daily_task_engine.get_today_tasks(roadmap)
    return APIResponse(
        success=True,
        message="Today's focus tasks retrieved",
        data=today_data
    )


@router.post(
    "/tasks/{task_id}/complete",
    response_model=APIResponse[RoadmapProgressResponse],
    summary="Mark roadmap task complete and update progress"
)
async def complete_roadmap_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=404, detail="No active roadmap found for user")

    completed = set(roadmap.completed_task_ids or [])
    completed.add(task_id)
    roadmap.completed_task_ids = list(completed)

    # Recalculate deterministic progress
    roadmap.overall_progress_percent = roadmap_engine.calculate_progress(roadmap)

    await db.commit()
    await db.refresh(roadmap)

    total_tasks = sum(len(p.get("tasks", [])) for p in (roadmap.phases or []))
    total_projs = sum(len(p.get("projects", [])) for p in (roadmap.phases or []))
    total_mils = sum(len(p.get("milestones", [])) for p in (roadmap.phases or []))

    progress_resp = RoadmapProgressResponse(
        roadmap_id=roadmap.id,
        target_role=roadmap.target_role,
        overall_progress_percent=roadmap.overall_progress_percent,
        completed_tasks_count=len(roadmap.completed_task_ids),
        total_tasks_count=total_tasks,
        completed_projects_count=len(roadmap.completed_project_ids or []),
        total_projects_count=total_projs,
        completed_milestones_count=len(roadmap.completed_milestone_ids or []),
        total_milestones_count=total_mils,
        is_outdated=roadmap.is_outdated
    )

    return APIResponse(
        success=True,
        message=f"Task '{task_id}' marked completed",
        data=progress_resp
    )


@router.post(
    "/tasks/{task_id}/uncomplete",
    response_model=APIResponse[RoadmapProgressResponse],
    summary="Unmark roadmap task completion"
)
async def uncomplete_roadmap_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=404, detail="No active roadmap found for user")

    completed = set(roadmap.completed_task_ids or [])
    completed.discard(task_id)
    roadmap.completed_task_ids = list(completed)

    roadmap.overall_progress_percent = roadmap_engine.calculate_progress(roadmap)

    await db.commit()
    await db.refresh(roadmap)

    total_tasks = sum(len(p.get("tasks", [])) for p in (roadmap.phases or []))
    total_projs = sum(len(p.get("projects", [])) for p in (roadmap.phases or []))
    total_mils = sum(len(p.get("milestones", [])) for p in (roadmap.phases or []))

    progress_resp = RoadmapProgressResponse(
        roadmap_id=roadmap.id,
        target_role=roadmap.target_role,
        overall_progress_percent=roadmap.overall_progress_percent,
        completed_tasks_count=len(roadmap.completed_task_ids),
        total_tasks_count=total_tasks,
        completed_projects_count=len(roadmap.completed_project_ids or []),
        total_projects_count=total_projs,
        completed_milestones_count=len(roadmap.completed_milestone_ids or []),
        total_milestones_count=total_mils,
        is_outdated=roadmap.is_outdated
    )

    return APIResponse(
        success=True,
        message=f"Task '{task_id}' unmarked",
        data=progress_resp
    )


@router.get(
    "/progress",
    response_model=APIResponse[RoadmapProgressResponse],
    summary="Get roadmap progress statistics"
)
async def get_roadmap_progress(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=404, detail="No active roadmap found for user")

    total_tasks = sum(len(p.get("tasks", [])) for p in (roadmap.phases or []))
    total_projs = sum(len(p.get("projects", [])) for p in (roadmap.phases or []))
    total_mils = sum(len(p.get("milestones", [])) for p in (roadmap.phases or []))

    progress_resp = RoadmapProgressResponse(
        roadmap_id=roadmap.id,
        target_role=roadmap.target_role,
        overall_progress_percent=roadmap.overall_progress_percent,
        completed_tasks_count=len(roadmap.completed_task_ids or []),
        total_tasks_count=total_tasks,
        completed_projects_count=len(roadmap.completed_project_ids or []),
        total_projects_count=total_projs,
        completed_milestones_count=len(roadmap.completed_milestone_ids or []),
        total_milestones_count=total_mils,
        is_outdated=roadmap.is_outdated
    )

    return APIResponse(
        success=True,
        message="Roadmap progress metrics retrieved",
        data=progress_resp
    )


@router.post(
    "/recalculate",
    response_model=APIResponse[RoadmapDetailResponse],
    summary="Recalculate roadmap for current target career preserving historical task completion"
)
async def recalculate_roadmap(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    old_roadmap = res.scalars().first()

    prev_level = old_roadmap.user_level if old_roadmap else "Beginner"
    prev_hpd = old_roadmap.hours_per_day if old_roadmap else 1
    prev_dpw = old_roadmap.days_per_week if old_roadmap else 5
    prev_style = old_roadmap.preferred_learning_style if old_roadmap else "Hands-on"
    prev_completed_tasks = list(old_roadmap.completed_task_ids) if old_roadmap and old_roadmap.completed_task_ids else []

    new_roadmap = await roadmap_engine.generate_user_roadmap(
        db=db,
        user_id=user_id,
        user_level=prev_level,
        hours_per_day=prev_hpd,
        days_per_week=prev_dpw,
        preferred_learning_style=prev_style
    )

    # Preserve matching completed task IDs if applicable
    new_roadmap.completed_task_ids = prev_completed_tasks
    new_roadmap.overall_progress_percent = roadmap_engine.calculate_progress(new_roadmap)
    new_roadmap.is_outdated = False

    await db.commit()
    await db.refresh(new_roadmap)

    return APIResponse(
        success=True,
        message="Roadmap recalculated and updated successfully",
        data=_to_detail_response(new_roadmap)
    )


@router.put(
    "/preferences",
    response_model=APIResponse[RoadmapDetailResponse],
    summary="Update learning time & level preferences"
)
async def update_learning_preferences(
    req: RoadmapPreferencesRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        roadmap = await roadmap_engine.generate_user_roadmap(
            db=db,
            user_id=user_id,
            user_level=req.user_level,
            hours_per_day=req.hours_per_day,
            days_per_week=req.days_per_week,
            preferred_learning_style=req.preferred_learning_style
        )
    else:
        roadmap.hours_per_day = req.hours_per_day
        roadmap.days_per_week = req.days_per_week
        roadmap.preferred_learning_style = req.preferred_learning_style
        roadmap.user_level = req.user_level

        weekly_hours = req.hours_per_day * req.days_per_week
        roadmap.total_estimated_weeks = max(2, int(round(24.0 / max(weekly_hours, 1))))

        await db.commit()
        await db.refresh(roadmap)

    return APIResponse(
        success=True,
        message="Learning preferences updated successfully",
        data=_to_detail_response(roadmap)
    )


@router.post(
    "/focus-skill",
    response_model=APIResponse[FocusSkillResponse],
    summary="Map a skill gap to Today's Focus in active roadmap"
)
async def focus_skill(
    req: FocusSkillRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    skill_clean = req.skill_name.strip()
    if not skill_clean:
        raise HTTPException(status_code=400, detail="Skill name is required")

    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        roadmap = await roadmap_engine.generate_user_roadmap(db=db, user_id=user_id)

    phases = copy.deepcopy(roadmap.phases or [])
    completed_ids = set(roadmap.completed_task_ids or [])
    
    # 1. Check if an incomplete task already exists matching this skill
    found_task = None
    target_phase_idx = 0
    for p_idx, phase in enumerate(phases):
        for task in phase.get("tasks", []):
            if (task.get("skill", "").lower() == skill_clean.lower() or 
                skill_clean.lower() in task.get("title", "").lower()):
                found_task = task
                target_phase_idx = p_idx
                break
        if found_task:
            break

    # Check today's current focus
    today_data = daily_task_engine.get_today_tasks(roadmap)
    if today_data.tasks and today_data.tasks[0].skill.lower() == skill_clean.lower():
        return APIResponse(
            success=True,
            message=f"'{skill_clean}' is already in your Today's Focus",
            data=FocusSkillResponse(
                status="already_focus",
                message=f"'{skill_clean}' is already in your Today's Focus",
                skill_name=skill_clean,
                roadmap_id=roadmap.id,
                task=today_data.tasks[0]
            )
        )

    if found_task:
        # Prioritize this task by moving it to the top of its phase's tasks
        phase_tasks = phases[target_phase_idx].get("tasks", [])
        phase_tasks = [t for t in phase_tasks if t.get("id") != found_task.get("id")]
        phase_tasks.insert(0, found_task)
        phases[target_phase_idx]["tasks"] = phase_tasks
        status_msg = "prioritized"
        user_msg = f"Task for '{skill_clean}' prioritized in your active roadmap"
    else:
        # Create a new focused task in the first phase without duplication
        new_task_id = f"task_focus_{uuid.uuid4().hex[:8]}"
        found_task = {
            "id": new_task_id,
            "title": f"Master {skill_clean} Fundamentals & Core Implementation",
            "skill": skill_clean,
            "estimated_minutes": 30,
            "why_matters": f"Essential skill gap for {roadmap.target_role}.",
            "practice_activity": f"Build practical hands-on exercises and implement core concepts in {skill_clean}.",
            "completed": False,
            "completed_at": None
        }
        if phases:
            if "tasks" not in phases[0]:
                phases[0]["tasks"] = []
            phases[0]["tasks"].insert(0, found_task)
        else:
            phases.append({
                "phase_id": "phase_1",
                "name": "Phase 1 ? Core Foundations",
                "description": "Core foundational skills",
                "estimated_weeks": 2,
                "skills": [{"name": skill_clean, "status": "Missing", "priority": "Essential", "level": "Beginner"}],
                "learning_objectives": [f"Learn {skill_clean}"],
                "tasks": [found_task],
                "projects": [],
                "milestones": []
            })
        status_msg = "added"
        user_msg = f"New focus task for '{skill_clean}' added to Today's Focus"

    roadmap.phases = phases
    flag_modified(roadmap, "phases")
    await db.commit()
    await db.refresh(roadmap)

    task_schema = RoadmapTaskSchema(**found_task)
    return APIResponse(
        success=True,
        message=user_msg,
        data=FocusSkillResponse(
            status=status_msg,
            message=user_msg,
            skill_name=skill_clean,
            roadmap_id=roadmap.id,
            task=task_schema
        )
    )
