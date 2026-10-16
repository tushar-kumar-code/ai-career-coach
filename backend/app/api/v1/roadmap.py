import copy
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
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
    CustomPhaseRequest,
    RoadmapResponse,
    RoadmapPhaseSchema,
    TodayFocusResponse,
    RoadmapProgressResponse,
    RoadmapTaskSchema,
    TaskLearningContentResponse,
    PracticeSuggestion,
    FocusSkillRequest,
    FocusSkillResponse,
    LevelTestResponse,
    LevelTestSubmitRequest,
    LevelTestSubmitResponse
)

import logging
from app.schemas.interview import PracticeSuggestionItem
from app.services.skill.ingestion_engine import SkillIngestionEngine
from app.services.skill.gap_engine import SkillGapEngine
from app.services.roadmap.roadmap_engine import RoadmapEngine
from app.services.roadmap.progress_sync import ProfileProgressSyncService
from app.services.firestore.roadmap_repo import RoadmapRepository
from app.services.roadmap.level_test_engine import LevelTestEngine

router = APIRouter()
logger = logging.getLogger(__name__)
ingestion_engine = SkillIngestionEngine()
gap_engine = SkillGapEngine()
roadmap_engine = RoadmapEngine()
progress_sync_service = ProfileProgressSyncService()
level_test_engine = LevelTestEngine()


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
        user_level=payload.user_level or "Beginner",
        hours_per_day=payload.hours_per_day,
        days_per_week=payload.days_per_week,
        learning_style=payload.preferred_learning_style,
        preserve_progress=True,
        track_pace=payload.track_pace,
        target_phases_count=payload.target_phases_count
    )

    resp_data = _serialize_roadmap(roadmap)
    try:
        await RoadmapRepository.save_roadmap(user_id, roadmap.id, resp_data.model_dump())
    except Exception as e:
        logger.warning(f"Firestore save roadmap error: {e}")

    return APIResponse(
        success=True,
        message="Personalized roadmap generated successfully",
        data=resp_data
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
    # 1. Check Firestore first
    try:
        fs_roadmap = await RoadmapRepository.get_active_roadmap(user_id)
        if fs_roadmap and fs_roadmap.get("phases"):
            # Check if target career changed
            user_profile = await UserRepository.get_user(user_id)
            target_career = user_profile.get("target_career") if user_profile else None
            if not target_career:
                p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
                p_res = await db.execute(p_stmt)
                up = p_res.scalars().first()
                if up:
                    target_career = up.target_career

            if target_career and target_career != fs_roadmap.get("target_role"):
                fs_roadmap["is_outdated"] = True
                await RoadmapRepository.save_roadmap(user_id, fs_roadmap.get("id"), {"is_outdated": True})

            return APIResponse(
                success=True,
                message="Current roadmap retrieved",
                data=RoadmapResponse(**fs_roadmap)
            )
    except Exception as e:
        logger.warning(f"Firestore get_active_roadmap warning: {e}")

    # 2. SQLite fallback
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
            topics_to_learn=t.get("topics_to_learn") or [],
            learning_focus=t.get("learning_focus"),
            practice_goal=t.get("practice_goal"),
            recommended_resources=t.get("recommended_resources") or [],
            difficulty_level=t.get("difficulty_level") or "Beginner",
            prerequisites=t.get("prerequisites") or [],
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

    # Automatically synchronize learned skills, update UserProfile & Digital Twin
    try:
        await progress_sync_service.sync_task_completion_to_profile(
            db=db,
            user_id=user_id,
            roadmap=roadmap,
            task_id=task_id,
            completed=True
        )
    except Exception as e:
        logger.warning(f"Error syncing roadmap progress to profile: {e}")

    serialized = _serialize_roadmap(roadmap)
    try:
        await RoadmapRepository.save_roadmap(user_id, roadmap.id, serialized.model_dump())
    except Exception as e:
        logger.warning(f"Firestore update roadmap error: {e}")

    return APIResponse(
        success=True,
        message=f"Task '{task_id}' marked as completed",
        data=serialized
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

    # Synchronize uncompletion to user profile
    try:
        await progress_sync_service.sync_task_completion_to_profile(
            db=db,
            user_id=user_id,
            roadmap=roadmap,
            task_id=task_id,
            completed=False
        )
    except Exception as e:
        logger.warning(f"Error syncing uncompleted task to profile: {e}")

    serialized = _serialize_roadmap(roadmap)
    try:
        await RoadmapRepository.save_roadmap(user_id, roadmap.id, serialized.model_dump())
    except Exception as e:
        logger.warning(f"Firestore update roadmap error: {e}")

    return APIResponse(
        success=True,
        message=f"Task '{task_id}' marked as uncompleted",
        data=serialized
    )


@router.post(
    "/phases/{phase_id}/generate-test",
    response_model=APIResponse[LevelTestResponse],
    summary="Generate AI level advancement test for a roadmap phase"
)
async def generate_level_test(
    phase_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=404, detail="Active roadmap not found")

    phases = roadmap.phases or []
    target_phase = None
    target_idx = -1
    for idx, p in enumerate(phases):
        pid = p.get("id") or p.get("phase_id") or f"phase-{idx + 1}"
        if pid == phase_id or str(p.get("phase_number")) == str(phase_id):
            target_phase = p
            target_idx = idx
            break

    if not target_phase:
        raise HTTPException(status_code=404, detail=f"Phase '{phase_id}' not found in active roadmap")

    test_res = await level_test_engine.generate_test(
        phase=target_phase,
        target_career=roadmap.target_role,
        user_level=roadmap.user_level
    )

    # Cache current test questions inside phase so verification is consistent
    target_phase["current_test_questions"] = [q.model_dump() for q in test_res.questions]
    flag_modified(roadmap, "phases")
    await db.commit()

    return APIResponse(
        success=True,
        message=f"AI Level Test for {test_res.level_name} generated successfully",
        data=test_res
    )


@router.post(
    "/phases/{phase_id}/submit-test",
    response_model=APIResponse[LevelTestSubmitResponse],
    summary="Submit answers for AI level test and unlock next level if passed"
)
async def submit_level_test(
    phase_id: str,
    payload: LevelTestSubmitRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=404, detail="Active roadmap not found")

    phases = roadmap.phases or []
    target_phase = None
    target_idx = -1
    for idx, p in enumerate(phases):
        pid = p.get("id") or p.get("phase_id") or f"phase-{idx + 1}"
        if pid == phase_id or str(p.get("phase_number")) == str(phase_id):
            target_phase = p
            target_idx = idx
            break

    if not target_phase:
        raise HTTPException(status_code=404, detail=f"Phase '{phase_id}' not found in active roadmap")

    next_phase = phases[target_idx + 1] if target_idx + 1 < len(phases) else None

    # Load stored test questions or generate fresh ones if not cached
    stored_questions_data = target_phase.get("current_test_questions") or []
    if stored_questions_data:
        from app.schemas.roadmap import LevelTestQuestion
        questions = [LevelTestQuestion(**q) for q in stored_questions_data]
    else:
        test_gen = await level_test_engine.generate_test(
            phase=target_phase,
            target_career=roadmap.target_role,
            user_level=roadmap.user_level
        )
        questions = test_gen.questions

    eval_res = level_test_engine.evaluate_test(
        phase=target_phase,
        user_answers=payload.answers,
        questions=questions,
        next_phase=next_phase
    )

    # Persist pass/score state
    target_phase["test_score"] = eval_res.score_percent
    target_phase["stars"] = eval_res.stars_awarded
    target_phase["xp_reward"] = eval_res.xp_earned
    if eval_res.passed:
        target_phase["test_passed"] = True
        if next_phase:
            next_phase["is_unlocked"] = True

    flag_modified(roadmap, "phases")
    await db.commit()

    # Firestore sync
    try:
        serialized = _serialize_roadmap(roadmap)
        await RoadmapRepository.save_roadmap(user_id, roadmap.id, serialized.model_dump())
    except Exception as e:
        logger.warning(f"Firestore update roadmap error: {e}")

    return APIResponse(
        success=True,
        message="Level test evaluated",
        data=eval_res
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
        user_level=roadmap.user_level if roadmap else "Beginner",
        hours_per_day=h_day,
        days_per_week=d_week,
        learning_style=style,
        preserve_progress=True
    )

    try:
        await RoadmapRepository.save_roadmap(user_id, updated_roadmap.id, _serialize_roadmap(updated_roadmap).model_dump())
    except Exception as e:
        logger.warning(f"Firestore save_roadmap warning: {e}")

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
        user_level=payload.user_level or (roadmap.user_level if roadmap else "Beginner"),
        hours_per_day=payload.hours_per_day,
        days_per_week=payload.days_per_week,
        learning_style=payload.preferred_learning_style,
        preserve_progress=True,
        track_pace=payload.track_pace,
        target_phases_count=payload.target_phases_count
    )

    try:
        await RoadmapRepository.save_roadmap(user_id, updated_roadmap.id, _serialize_roadmap(updated_roadmap).model_dump())
    except Exception as e:
        logger.warning(f"Firestore save_roadmap warning: {e}")

    return APIResponse(
        success=True,
        message="Learning preferences updated successfully",
        data=_serialize_roadmap(updated_roadmap)
    )


@router.post(
    "/phases/custom",
    response_model=APIResponse[RoadmapResponse],
    summary="Add a custom milestone/level to active roadmap"
)
async def add_custom_phase(
    payload: CustomPhaseRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    res = await db.execute(stmt)
    roadmap = res.scalars().first()

    if not roadmap:
        raise HTTPException(status_code=404, detail="Active roadmap not found")

    phases = list(roadmap.phases or [])
    new_phase_number = len(phases) + 1
    new_phase_id = f"phase-{new_phase_number}-{uuid.uuid4().hex[:6]}"

    tasks = []
    if payload.topics:
        for t_idx, topic in enumerate(payload.topics, start=1):
            tasks.append({
                "id": f"{new_phase_id}-task-{t_idx}",
                "title": f"Master {topic}",
                "description": f"Hands-on deep dive and implementation of {topic}.",
                "estimated_minutes": payload.estimated_minutes or 45,
                "task_type": "Practice",
                "why_it_matters": "Custom career goal requirement",
                "is_completed": False,
                "topics_to_learn": [topic]
            })
    else:
        tasks.append({
            "id": f"{new_phase_id}-task-1",
            "title": f"Complete {payload.title}",
            "description": payload.description or f"Hands-on milestone for {payload.title}.",
            "estimated_minutes": payload.estimated_minutes or 60,
            "task_type": "Milestone",
            "why_it_matters": "Personalized career milestone",
            "is_completed": False,
            "topics_to_learn": [payload.title]
        })

    custom_phase = {
        "id": new_phase_id,
        "phase_id": new_phase_id,
        "phase_number": new_phase_number,
        "name": payload.title,
        "title": payload.title,
        "level_name": payload.title,
        "level_theme": payload.title,
        "description": payload.description or "Custom user milestone tailored to specific learning goals.",
        "is_unlocked": len(phases) == 0,
        "test_passed": False,
        "progress_percent": 0,
        "tasks": tasks
    }

    phases.append(custom_phase)
    roadmap.phases = phases
    flag_modified(roadmap, "phases")
    await db.commit()

    return APIResponse(
        success=True,
        message=f"Custom level '{payload.title}' added to your roadmap",
        data=_serialize_roadmap(roadmap)
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

    # If not found in SQLite, check Firestore first
    if not roadmap:
        try:
            fs_roadmap = await RoadmapRepository.get_active_roadmap(user_id)
            if fs_roadmap and fs_roadmap.get("phases"):
                roadmap = Roadmap(
                    user_id=user_id,
                    target_role=fs_roadmap.get("target_role", "Software Developer"),
                    user_level=fs_roadmap.get("user_level", "Beginner"),
                    overall_progress_percent=fs_roadmap.get("overall_progress_percent", 0),
                    is_active=True,
                    is_outdated=False,
                    hours_per_day=fs_roadmap.get("hours_per_day", 1),
                    days_per_week=fs_roadmap.get("days_per_week", 5),
                    preferred_learning_style=fs_roadmap.get("preferred_learning_style", "Hands-on"),
                    total_estimated_weeks=fs_roadmap.get("total_estimated_weeks", 12),
                    phases=fs_roadmap.get("phases", []),
                    completed_task_ids=fs_roadmap.get("completed_task_ids", []),
                    completed_milestone_ids=fs_roadmap.get("completed_milestone_ids", []),
                    completed_project_ids=fs_roadmap.get("completed_project_ids", [])
                )
                db.add(roadmap)
                await db.commit()
                await db.refresh(roadmap)
        except Exception as e:
            logger.warning(f"Notice while restoring Firestore roadmap in focus_skill: {e}")

    # If still not found, generate a fresh roadmap
    if not roadmap:
        u_skills = await ingestion_engine.ingest_user_skills(db, user_id)
        target_career, _, _, missing_gaps, _ = await gap_engine.calculate_skill_gaps(db, user_id, u_skills)
        roadmap = await roadmap_engine.generate_roadmap(
            db=db,
            user_id=user_id,
            target_career=target_career,
            user_skills=u_skills,
            missing_gaps=missing_gaps
        )

    phases = copy.deepcopy(roadmap.phases or [])
    if not phases:
        phases.append({
            "id": "phase-1",
            "phase_number": 1,
            "title": f"Phase 1: Core {skill_clean} & Foundations",
            "type": "Foundation",
            "skills": [skill_clean],
            "learning_objectives": [f"Master {skill_clean} basics and application"],
            "progress_percent": 0,
            "tasks": []
        })

    # Find first active incomplete phase (so the task is immediately actionable)
    active_phase_idx = 0
    for p_idx, phase in enumerate(phases):
        p_tasks = phase.get("tasks", [])
        if any(not t.get("is_completed") for t in p_tasks):
            active_phase_idx = p_idx
            break

    # Check if this skill is already top of today's focus
    focus_dict = roadmap_engine.get_today_focus_tasks(roadmap)
    today_tasks = focus_dict.get("today_tasks", [])
    if today_tasks:
        first_t = today_tasks[0]
        first_t_skill = first_t.get("skill") or first_t.get("title", "")
        if skill_clean.lower() in first_t_skill.lower() or skill_clean.lower() in first_t.get("title", "").lower():
            return APIResponse(
                success=True,
                message=f"'{skill_clean}' is already in your Today's Focus",
                data=FocusSkillResponse(
                    status="already_focus",
                    message=f"'{skill_clean}' is already in your Today's Focus",
                    skill_name=skill_clean,
                    roadmap_id=roadmap.id,
                    task=RoadmapTaskSchema(**first_t)
                )
            )

    found_task = None
    existing_phase_idx = -1
    for p_idx, phase in enumerate(phases):
        for task in phase.get("tasks", []):
            task_skill = task.get("skill") or task.get("title", "")
            if (skill_clean.lower() in task_skill.lower() or 
                skill_clean.lower() in task.get("title", "").lower()):
                found_task = task
                existing_phase_idx = p_idx
                break
        if found_task:
            break

    if found_task:
        # Remove from old position
        if existing_phase_idx >= 0:
            phases[existing_phase_idx]["tasks"] = [
                t for t in phases[existing_phase_idx].get("tasks", [])
                if t.get("id") != found_task.get("id")
            ]
        # Ensure task is marked uncompleted and prioritized in the active phase
        found_task["is_completed"] = False
        found_task["completed_at"] = None
        found_task["is_priority"] = True
        found_task["priority_reason"] = f"Focused skill gap: {skill_clean}"
        found_task["skill"] = skill_clean
        if not found_task.get("topics_to_learn"):
            found_task["topics_to_learn"] = [
                f"{skill_clean} Core Syntax & Semantics",
                f"{skill_clean} Common Algorithms & Patterns",
                f"{skill_clean} Practice Project Implementation"
            ]
        phases[active_phase_idx].setdefault("tasks", []).insert(0, found_task)
        phase_skills = phases[active_phase_idx].setdefault("skills", [])
        if skill_clean not in phase_skills:
            phase_skills.append(skill_clean)

        status_msg = "prioritized"
        user_msg = f"Task for '{skill_clean}' prioritized in Level {active_phase_idx + 1} and Today's Focus!"
    else:
        # Create a new rich focused task directly in the active phase
        new_task_id = f"task_focus_{uuid.uuid4().hex[:8]}"
        target_role_str = roadmap.target_role or "Software Developer"
        found_task = {
            "id": new_task_id,
            "title": f"Master {skill_clean} Fundamentals & Core Implementation",
            "description": f"Hands-on study and practical implementation of {skill_clean} for {target_role_str}.",
            "estimated_minutes": 35,
            "task_type": "Practice",
            "skill": skill_clean,
            "why_it_matters": f"Identified as a critical skill gap for {target_role_str} placement readiness.",
            "is_completed": False,
            "completed_at": None,
            "topics_to_learn": [
                f"{skill_clean} Core Fundamentals",
                f"{skill_clean} Problem Solving & Best Practices",
                f"{skill_clean} Applied Project Exercise"
            ],
            "learning_focus": f"Prioritize core syntax, idiomatic patterns, and hands-on coding with {skill_clean}.",
            "practice_goal": f"Build a tested module demonstrating {skill_clean} concepts.",
            "difficulty_level": "Intermediate",
            "concept_explanation": f"Core principles, idioms, and industry standards for using {skill_clean} in {target_role_str} roles.",
            "practice_exercise": f"Write a clean, functional implementation utilizing {skill_clean}.",
            "check_quiz_question": f"What is the primary value of {skill_clean} in {target_role_str} workflows?",
            "check_quiz_options": [
                f"A) Core technical competency directly assessed in interviews",
                f"B) Optional hobby concept not tested by recruiters",
                f"C) Replaced by legacy utilities"
            ],
            "check_quiz_answer": f"A) Core technical competency directly assessed in interviews",
            "is_priority": True,
            "priority_reason": f"Added from Missing Target Career Skills: {skill_clean}"
        }

        phases[active_phase_idx].setdefault("tasks", []).insert(0, found_task)
        phase_skills = phases[active_phase_idx].setdefault("skills", [])
        if skill_clean not in phase_skills:
            phase_skills.append(skill_clean)

        status_msg = "added"
        user_msg = f"'{skill_clean}' added to Level {active_phase_idx + 1} and Today's Focus!"

    roadmap.phases = phases
    flag_modified(roadmap, "phases")
    await db.commit()
    await db.refresh(roadmap)

    # Sync to Firestore if configured
    serialized = _serialize_roadmap(roadmap)
    try:
        await RoadmapRepository.save_roadmap(user_id, roadmap.id, serialized.model_dump())
    except Exception as e:
        logger.warning(f"Firestore update roadmap notice: {e}")

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


def _serialize_roadmap(r: Roadmap) -> RoadmapResponse:
    raw_phases = r.phases or []
    enriched_phases = []

    # Level 1 is always unlocked.
    # Level N is unlocked if Level N-1 test was passed (or is_unlocked is explicitly set).
    prev_passed = True
    passed_ids = []

    for idx, p in enumerate(raw_phases):
        p_num = p.get("phase_number", idx + 1)
        lvl_info = level_test_engine.get_level_info(p_num)

        test_passed = bool(p.get("test_passed", False))
        if test_passed:
            passed_ids.append(p.get("id") or p.get("phase_id") or f"phase-{p_num}")

        is_unlocked = True if idx == 0 else (prev_passed or bool(p.get("is_unlocked", False)))

        score = p.get("test_score")
        if p.get("stars") is not None:
            stars = p.get("stars", 0)
        elif score is not None:
            stars = 3 if score >= 95 else 2 if score >= 80 else 1 if score >= 70 else 0
        else:
            stars = 0

        xp_val = p.get("xp_reward") or (100 if test_passed else 100)

        p_copy = dict(p)
        p_copy["level_name"] = p.get("level_name") or lvl_info["level_name"]
        p_copy["level_theme"] = p.get("level_theme") or lvl_info["level_theme"]
        p_copy["level_icon"] = p.get("level_icon") or lvl_info["level_icon"]
        p_copy["is_unlocked"] = is_unlocked
        p_copy["test_passed"] = test_passed
        p_copy["test_score"] = score
        p_copy["stars"] = stars
        p_copy["xp_reward"] = xp_val

        enriched_phases.append(p_copy)
        prev_passed = test_passed

    curr_unlocked = max([p.get("phase_number", 1) for p in enriched_phases if p.get("is_unlocked")] or [1])
    total_xp = sum(p.get("xp_reward", 100) for p in enriched_phases if p.get("test_passed")) + len(r.completed_task_ids or []) * 20
    adventurer_level = max(1, (total_xp // 250) + 1)

    return RoadmapResponse(
        id=r.id,
        user_id=r.user_id,
        target_role=r.target_role,
        user_level=getattr(r, "user_level", "Beginner") or "Beginner",
        overall_progress_percent=r.overall_progress_percent,
        is_active=r.is_active,
        is_outdated=r.is_outdated,
        hours_per_day=r.hours_per_day,
        days_per_week=r.days_per_week,
        preferred_learning_style=r.preferred_learning_style,
        total_estimated_weeks=r.total_estimated_weeks,
        phases=enriched_phases,
        completed_task_ids=r.completed_task_ids or [],
        completed_milestone_ids=r.completed_milestone_ids or [],
        completed_project_ids=r.completed_project_ids or [],
        passed_level_ids=passed_ids,
        current_unlocked_level=curr_unlocked,
        total_xp=total_xp,
        adventurer_level=adventurer_level,
        created_at=r.created_at.isoformat() if r.created_at else None,
        updated_at=r.updated_at.isoformat() if r.updated_at else None
    )
