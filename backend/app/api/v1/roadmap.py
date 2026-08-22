from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.roadmap import Roadmap
from app.models.skill import Skill
from app.models.profile import UserProfile
from app.models.interview import InterviewSession
from app.schemas.health import APIResponse
from app.schemas.roadmap import (
    RoadmapGenerateRequest,
    RoadmapPreferencesRequest,
    RoadmapResponse,
    RoadmapPhaseSchema,
    TodayFocusResponse,
    RoadmapProgressResponse,
    RoadmapTaskSchema,
    TaskLearningContentResponse,
    PracticeSuggestion
)
from app.schemas.interview import PracticeSuggestionItem
from app.services.skill.ingestion_engine import SkillIngestionEngine
from app.services.skill.gap_engine import SkillGapEngine
from app.services.roadmap.roadmap_engine import RoadmapEngine

router = APIRouter()
ingestion_engine = SkillIngestionEngine()
gap_engine = SkillGapEngine()
roadmap_engine = RoadmapEngine()


@router.post(
    "/generate",
    response_model=APIResponse[RoadmapResponse],
    summary="Generate personalized learning roadmap from target career and skill gaps"
)
async def generate_roadmap(
    payload: RoadmapGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # 1. Ingest/get user skills
    u_skills = await ingestion_engine.ingest_user_skills(db, user_id)
    
    # 2. Calculate skill gaps & target career
    target_career, _, _, missing_gaps, _ = await gap_engine.calculate_skill_gaps(db, user_id, u_skills)

    # 3. Generate Roadmap
    roadmap = await roadmap_engine.generate_roadmap(
        db=db,
        user_id=user_id,
        target_career=target_career,
        user_skills=u_skills,
        missing_gaps=missing_gaps,
        hours_per_day=payload.hours_per_day,
        days_per_week=payload.days_per_week,
        learning_style=payload.preferred_learning_style,
        preserve_progress=True
    )

    return APIResponse(
        success=True,
        message="Personalized roadmap generated successfully",
        data=_serialize_roadmap(roadmap)
    )


@router.get(
    "/current",
    response_model=APIResponse[Optional[RoadmapResponse]],
    summary="Get active user roadmap"
)
async def get_current_roadmap(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        return APIResponse(
            success=True,
            message="No active roadmap found",
            data=None
        )

    # Check if target career changed
    p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    p_res = await db.execute(p_stmt)
    user_profile = p_res.scalars().first()

    if user_profile and user_profile.target_career and user_profile.target_career != roadmap.target_role:
        roadmap.is_outdated = True
        db.add(roadmap)
        await db.commit()

    return APIResponse(
        success=True,
        message="Current roadmap retrieved",
        data=_serialize_roadmap(roadmap)
    )


@router.get(
    "/phases",
    response_model=APIResponse[List[RoadmapPhaseSchema]],
    summary="Get list of roadmap phases with progress"
)
async def get_roadmap_phases(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        return APIResponse(
            success=True,
            message="No active roadmap found",
            data=[]
        )

    return APIResponse(
        success=True,
        message="Roadmap phases retrieved",
        data=roadmap.phases or []
    )


@router.get(
    "/today",
    response_model=APIResponse[TodayFocusResponse],
    summary="Get 'What should I do today?' focus tasks"
)
async def get_today_focus(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    focus_dict = roadmap_engine.get_today_focus_tasks(roadmap)

    # Map today tasks into schemas
    today_tasks_schemas = [
        RoadmapTaskSchema(
            id=t["id"],
            title=t["title"],
            description=t["description"],
            estimated_minutes=t.get("estimated_minutes", 30),
            task_type=t.get("task_type", "Learn"),
            why_it_matters=t.get("why_it_matters", "Skill gap requirement"),
            is_completed=t.get("is_completed", False),
            completed_at=t.get("completed_at"),
            concept_explanation=t.get("concept_explanation"),
            practice_exercise=t.get("practice_exercise"),
            check_quiz_question=t.get("check_quiz_question"),
            check_quiz_options=t.get("check_quiz_options"),
            check_quiz_answer=t.get("check_quiz_answer"),
            is_priority=t.get("is_priority", False),
            priority_reason=t.get("priority_reason")
        )
        for t in focus_dict["today_tasks"]
    ]

    return APIResponse(
        success=True,
        message="Today's focus tasks retrieved",
        data=TodayFocusResponse(
            target_career=focus_dict["target_career"],
            today_focus_title=focus_dict["today_focus_title"],
            current_phase_id=focus_dict.get("current_phase_id"),
            current_phase_title=focus_dict.get("current_phase_title"),
            today_tasks=today_tasks_schemas,
            recommended_minutes=focus_dict["recommended_minutes"],
            why_it_matters=focus_dict.get("why_it_matters")
        )
    )


@router.get(
    "/tasks/{task_id}/learn",
    response_model=APIResponse[TaskLearningContentResponse],
    summary="Get learning resources (concept, exercise, quiz) for a specific roadmap task"
)
async def get_task_learning_content(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Returns the learning guidance content (Learn / Practice / Check Yourself) for a task."""
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=404, detail="No active roadmap found")

    # Search for task across all phases
    task_data = None
    for phase in (roadmap.phases or []):
        for task in phase.get("tasks", []):
            if task.get("id") == task_id:
                task_data = task
                break
        if task_data:
            break

    if not task_data:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found in active roadmap")

    # Build default learning content if not populated by AI
    skill_topic = task_data.get("title", "this topic")
    target_role = roadmap.target_role

    return APIResponse(
        success=True,
        message="Task learning content retrieved",
        data=TaskLearningContentResponse(
            task_id=task_id,
            title=task_data.get("title", ""),
            concept_explanation=task_data.get("concept_explanation") or f"{skill_topic} is a key concept for {target_role}. Understanding it helps you build reliable, production-ready systems. Focus on the core principles before moving to advanced patterns.",
            practice_exercise=task_data.get("practice_exercise") or f"Write a small working implementation of {skill_topic}. Start with the simplest possible version, verify it works, then add one small feature.",
            check_quiz_question=task_data.get("check_quiz_question") or f"What is the primary benefit of {skill_topic} in a {target_role} project?",
            check_quiz_options=task_data.get("check_quiz_options") or [
                f"A) It directly enables core {target_role} functionality",
                f"B) It is optional and rarely used in real projects",
                f"C) It is only relevant for senior-level engineers"
            ],
            check_quiz_answer=task_data.get("check_quiz_answer") or f"A) {skill_topic} is a foundational skill that most {target_role} job descriptions require.",
            why_it_matters=task_data.get("why_it_matters", f"Essential for {target_role} readiness."),
            task_type=task_data.get("task_type", "Learn")
        )
    )


@router.get(
    "/practice/suggest",
    response_model=APIResponse[List[PracticeSuggestionItem]],
    summary="Get suggested micro-practice topics based on skill gaps and recent interview weaknesses"
)
async def get_practice_suggestions(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Returns 3-5 focused practice topics derived from skill gaps and recent interview weak areas."""
    suggestions: List[PracticeSuggestionItem] = []
    seen_topics = set()

    # 1. Recent interview weak areas (last 3 completed sessions)
    stmt_iv = (
        select(InterviewSession)
        .where(InterviewSession.user_id == user_id, InterviewSession.is_completed == True)
        .order_by(InterviewSession.created_at.desc())
        .limit(3)
    )
    res_iv = await db.execute(stmt_iv)
    recent_sessions = res_iv.scalars().all()

    for session in recent_sessions:
        for wa in (session.weak_areas or [])[:2]:
            if wa and wa not in seen_topics:
                seen_topics.add(wa)
                suggestions.append(PracticeSuggestionItem(
                    topic=wa,
                    reason=f"Identified as a weak area in your recent {session.mode} interview (score: {session.overall_score}%).",
                    source="interview_weakness",
                    priority="High" if session.overall_score < 60 else "Medium"
                ))

    # 2. High-priority skill gaps
    stmt_sk = select(Skill).where(Skill.user_id == user_id, Skill.priority == "High")
    res_sk = await db.execute(stmt_sk)
    high_priority_skills = res_sk.scalars().all()

    for sk in high_priority_skills[:3]:
        topic = sk.skill_name
        if topic not in seen_topics:
            seen_topics.add(topic)
            suggestions.append(PracticeSuggestionItem(
                topic=topic,
                reason=f"High-priority skill gap for your target career. Current confidence: {sk.confidence_status}.",
                source="skill_gap",
                priority="High"
            ))

    # 3. First incomplete roadmap task from current phase
    stmt_rm = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res_rm = await db.execute(stmt_rm)
    roadmap = res_rm.scalars().first()

    if roadmap and roadmap.phases:
        for phase in roadmap.phases:
            for task in phase.get("tasks", []):
                if not task.get("is_completed"):
                    topic = task.get("title", "")
                    if topic and topic not in seen_topics:
                        seen_topics.add(topic)
                        suggestions.append(PracticeSuggestionItem(
                            topic=topic,
                            reason=f"Next task in your active roadmap: {phase.get('title', 'Current Phase')}.",
                            source="roadmap_task",
                            priority="Medium"
                        ))
                    break
            break  # Only first phase

    # Sort: High priority first, then Medium
    suggestions.sort(key=lambda x: 0 if x.priority == "High" else 1)

    return APIResponse(
        success=True,
        message="Practice suggestions retrieved",
        data=suggestions[:6]  # Max 6 suggestions
    )


@router.post(
    "/tasks/{task_id}/complete",
    response_model=APIResponse[RoadmapResponse],
    summary="Mark roadmap task as completed and update progress"
)
async def complete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=404, detail="Active roadmap not found")

    roadmap = roadmap_engine.update_task_completion(roadmap, task_id, completed=True)
    db.add(roadmap)
    await db.commit()

    return APIResponse(
        success=True,
        message=f"Task '{task_id}' marked as completed",
        data=_serialize_roadmap(roadmap)
    )


@router.post(
    "/tasks/{task_id}/uncomplete",
    response_model=APIResponse[RoadmapResponse],
    summary="Mark roadmap task as uncompleted"
)
async def uncomplete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=404, detail="Active roadmap not found")

    roadmap = roadmap_engine.update_task_completion(roadmap, task_id, completed=False)
    db.add(roadmap)
    await db.commit()

    return APIResponse(
        success=True,
        message=f"Task '{task_id}' marked as uncompleted",
        data=_serialize_roadmap(roadmap)
    )


@router.get(
    "/progress",
    response_model=APIResponse[RoadmapProgressResponse],
    summary="Get overall roadmap progress metrics"
)
async def get_roadmap_progress(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        return APIResponse(
            success=True,
            message="No active roadmap",
            data=RoadmapProgressResponse(
                target_role="None",
                overall_progress_percent=0,
                completed_tasks_count=0,
                total_tasks_count=0,
                completed_phases_count=0,
                total_phases_count=0,
                is_outdated=False
            )
        )

    phases = roadmap.phases or []
    total_tasks = sum(len(p.get("tasks", [])) for p in phases)
    completed_tasks = len(roadmap.completed_task_ids or [])
    completed_phases = sum(1 for p in phases if p.get("progress_percent", 0) == 100)

    return APIResponse(
        success=True,
        message="Roadmap progress retrieved",
        data=RoadmapProgressResponse(
            target_role=roadmap.target_role,
            overall_progress_percent=roadmap.overall_progress_percent,
            completed_tasks_count=completed_tasks,
            total_tasks_count=total_tasks,
            completed_phases_count=completed_phases,
            total_phases_count=len(phases),
            is_outdated=roadmap.is_outdated
        )
    )


@router.post(
    "/recalculate",
    response_model=APIResponse[RoadmapResponse],
    summary="Recalculate roadmap while preserving completed task progress"
)
async def recalculate_roadmap(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    h_day = roadmap.hours_per_day if roadmap else 1
    d_week = roadmap.days_per_week if roadmap else 5
    style = roadmap.preferred_learning_style if roadmap else "Hands-on"

    u_skills = await ingestion_engine.ingest_user_skills(db, user_id)
    target_career, _, _, missing_gaps, _ = await gap_engine.calculate_skill_gaps(db, user_id, u_skills)

    updated_roadmap = await roadmap_engine.generate_roadmap(
        db=db,
        user_id=user_id,
        target_career=target_career,
        user_skills=u_skills,
        missing_gaps=missing_gaps,
        hours_per_day=h_day,
        days_per_week=d_week,
        learning_style=style,
        preserve_progress=True
    )

    return APIResponse(
        success=True,
        message="Roadmap recalculated and progress preserved",
        data=_serialize_roadmap(updated_roadmap)
    )


@router.put(
    "/preferences",
    response_model=APIResponse[RoadmapResponse],
    summary="Update learning preferences and study schedule"
)
async def update_preferences(
    payload: RoadmapPreferencesRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    u_skills = await ingestion_engine.ingest_user_skills(db, user_id)
    target_career, _, _, missing_gaps, _ = await gap_engine.calculate_skill_gaps(db, user_id, u_skills)

    updated_roadmap = await roadmap_engine.generate_roadmap(
        db=db,
        user_id=user_id,
        target_career=target_career,
        user_skills=u_skills,
        missing_gaps=missing_gaps,
        hours_per_day=payload.hours_per_day,
        days_per_week=payload.days_per_week,
        learning_style=payload.preferred_learning_style,
        preserve_progress=True
    )

    return APIResponse(
        success=True,
        message="Learning preferences updated successfully",
        data=_serialize_roadmap(updated_roadmap)
    )


def _serialize_roadmap(r: Roadmap) -> RoadmapResponse:
    return RoadmapResponse(
        id=r.id,
        user_id=r.user_id,
        target_role=r.target_role,
        overall_progress_percent=r.overall_progress_percent,
        is_active=r.is_active,
        is_outdated=r.is_outdated,
        hours_per_day=r.hours_per_day,
        days_per_week=r.days_per_week,
        preferred_learning_style=r.preferred_learning_style,
        total_estimated_weeks=r.total_estimated_weeks,
        phases=r.phases or [],
        completed_task_ids=r.completed_task_ids or [],
        completed_milestone_ids=r.completed_milestone_ids or [],
        completed_project_ids=r.completed_project_ids or [],
        created_at=r.created_at.isoformat() if r.created_at else None,
        updated_at=r.updated_at.isoformat() if r.updated_at else None
    )
