from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.init_db import seed_database
from app.models.assessment import AssessmentResponse
from app.models.question import Question
from app.models.career_catalog import CareerRole
from app.models.profile import UserProfile
from app.schemas.health import APIResponse
from app.schemas.assessment import (
    AssessmentSessionResponse,
    QuestionSchema,
    QuestionOptionSchema,
    AnswerSubmitRequest,
    TargetCareerSelectRequest
)
from app.services.assessment.adaptive_engine import AdaptiveAssessmentEngine
from app.services.ai.discovery_ai import CareerDiscoveryAIService

router = APIRouter()
adaptive_engine = AdaptiveAssessmentEngine()
ai_service = CareerDiscoveryAIService()


@router.post(
    "/start",
    response_model=APIResponse[AssessmentSessionResponse],
    summary="Start or resume career discovery assessment session"
)
async def start_assessment(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # Seed DB questions and career roles if empty
    await seed_database(db)

    # Check for existing IN_PROGRESS assessment for user
    stmt = select(AssessmentResponse).where(
        AssessmentResponse.user_id == user_id,
        AssessmentResponse.status == "IN_PROGRESS"
    ).order_by(AssessmentResponse.created_at.desc())
    res = await db.execute(stmt)
    session = res.scalars().first()

    # Get total questions count
    q_count_res = await db.execute(select(Question))
    total_questions = len(q_count_res.scalars().all())

    if session:
        answered_ids = list(session.dimension_answers.keys())
        next_q = await adaptive_engine.get_next_question(db, answered_ids, session.dimension_answers)
        if not next_q and total_questions > 0:
            # Session had all questions answered; start a fresh assessment session
            session = None

    if not session:
        session = AssessmentResponse(
            user_id=user_id,
            status="IN_PROGRESS",
            current_step=1,
            dimension_answers={}
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        answered_ids = []
        next_q = await adaptive_engine.get_next_question(db, answered_ids, session.dimension_answers)

    q_schema = None
    if next_q:
        options_list = [
            QuestionOptionSchema(id=o["id"], text=o["text"], archetype=o.get("archetype"))
            for o in next_q.options
        ]
        q_schema = QuestionSchema(
            id=next_q.id,
            dimension=next_q.dimension,
            question_type=next_q.question_type,
            question_text=next_q.question_text,
            options=options_list,
            order_index=next_q.order_index
        )

    session_resp = AssessmentSessionResponse(
        session_id=session.id,
        current_step=len(answered_ids) + 1,
        total_questions=total_questions,
        is_completed=session.status == "COMPLETED" or next_q is None,
        current_question=q_schema,
        answers_count=len(answered_ids)
    )

    return APIResponse(
        success=True,
        message="Assessment session ready",
        data=session_resp
    )


@router.post(
    "/answer",
    response_model=APIResponse[AssessmentSessionResponse],
    summary="Submit answer for assessment question"
)
async def submit_answer(
    payload: AnswerSubmitRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(AssessmentResponse).where(
        AssessmentResponse.id == payload.session_id,
        AssessmentResponse.user_id == user_id
    )
    res = await db.execute(stmt)
    session = res.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Assessment session not found for user")

    # Fetch targeted question
    q_stmt = select(Question).where(Question.id == payload.question_id)
    q_res = await db.execute(q_stmt)
    question = q_res.scalars().first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Find matching option
    selected_opt = next((o for o in question.options if o["id"] == payload.selected_option_id), None)
    if not selected_opt:
        raise HTTPException(status_code=400, detail="Invalid option selected")

    # Update session answers
    updated_answers = dict(session.dimension_answers)
    updated_answers[question.id] = {
        "question_id": question.id,
        "option_id": selected_opt["id"],
        "option_text": selected_opt["text"],
        "dimension": question.dimension,
        "archetype": selected_opt.get("archetype"),
        "weights": selected_opt.get("weights", {})
    }

    session.dimension_answers = updated_answers
    session.current_step = len(updated_answers) + 1
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Get total count and next question
    q_count_res = await db.execute(select(Question))
    total_questions = len(q_count_res.scalars().all())

    answered_ids = list(updated_answers.keys())
    next_q = await adaptive_engine.get_next_question(db, answered_ids, updated_answers)

    q_schema = None
    if next_q:
        options_list = [
            QuestionOptionSchema(id=o["id"], text=o["text"], archetype=o.get("archetype"))
            for o in next_q.options
        ]
        q_schema = QuestionSchema(
            id=next_q.id,
            dimension=next_q.dimension,
            question_type=next_q.question_type,
            question_text=next_q.question_text,
            options=options_list,
            order_index=next_q.order_index
        )

    session_resp = AssessmentSessionResponse(
        session_id=session.id,
        current_step=len(answered_ids) + 1,
        total_questions=total_questions,
        is_completed=next_q is None,
        current_question=q_schema,
        answers_count=len(answered_ids)
    )

    return APIResponse(
        success=True,
        message="Answer recorded successfully",
        data=session_resp
    )


@router.post(
    "/complete",
    response_model=APIResponse[dict],
    summary="Complete assessment and trigger Gemini AI analysis"
)
async def complete_assessment(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(AssessmentResponse).where(
        AssessmentResponse.id == session_id,
        AssessmentResponse.user_id == user_id
    )
    res = await db.execute(stmt)
    session = res.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Assessment session not found")

    if not session.dimension_answers:
        raise HTTPException(status_code=400, detail="Cannot complete assessment without answers")

    # Run AI Analysis
    ai_result = await ai_service.analyze_assessment(db, session.dimension_answers)
    ai_dict = ai_result.model_dump()

    # Update session status
    session.status = "COMPLETED"
    session.computed_archetype = ai_result.primary_archetype
    session.role_recommendations = [r.model_dump() for r in ai_result.recommended_careers]
    session.ai_analysis_json = ai_dict
    db.add(session)

    # Create or update UserProfile (Digital Twin)
    top_match = ai_result.recommended_careers[0] if ai_result.recommended_careers else None
    target_role = top_match.title if top_match else "Software Developer"
    top_score = top_match.match_percentage if top_match else 75

    p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    p_res = await db.execute(p_stmt)
    user_profile = p_res.scalars().first()

    if not user_profile:
        user_profile = UserProfile(
            user_id=user_id,
            target_career=target_role,
            primary_archetype=ai_result.primary_archetype,
            job_readiness_score=top_score,
            skills_matrix={
                "verified_skills": [s.model_dump() for s in ai_result.top_strengths],
                "interests": ai_result.interest_profile
            },
            recommended_roles=[r.model_dump() for r in ai_result.recommended_careers]
        )
    else:
        user_profile.primary_archetype = ai_result.primary_archetype
        user_profile.job_readiness_score = top_score
        user_profile.recommended_roles = [r.model_dump() for r in ai_result.recommended_careers]
        user_profile.skills_matrix = {
            "verified_skills": [s.model_dump() for s in ai_result.top_strengths],
            "interests": ai_result.interest_profile
        }

    db.add(user_profile)
    await db.commit()

    return APIResponse(
        success=True,
        message="Career Discovery Assessment completed successfully",
        data={
            "session_id": session.id,
            "status": "COMPLETED",
            "archetype": ai_result.primary_archetype,
            "analysis": ai_dict
        }
    )


@router.get(
    "/result",
    response_model=APIResponse[dict],
    summary="Get user's latest career profile and assessment result"
)
async def get_assessment_result(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(AssessmentResponse).where(
        AssessmentResponse.user_id == user_id,
        AssessmentResponse.status == "COMPLETED"
    ).order_by(AssessmentResponse.updated_at.desc())
    res = await db.execute(stmt)
    session = res.scalars().first()

    if not session or not session.ai_analysis_json:
        return APIResponse(
            success=False,
            message="No completed assessment found for user",
            data=None
        )

    # Fetch UserProfile target career
    p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    p_res = await db.execute(p_stmt)
    user_profile = p_res.scalars().first()

    result_data = {
        "session_id": session.id,
        "selected_target_career": user_profile.target_career if user_profile else session.selected_target_career,
        "archetype": session.computed_archetype,
        "analysis": session.ai_analysis_json,
        "completed_at": session.updated_at.isoformat() if session.updated_at else None
    }

    return APIResponse(
        success=True,
        message="Career Discovery Result retrieved",
        data=result_data
    )


@router.get(
    "/careers",
    response_model=APIResponse[List[dict]],
    summary="Get catalog of all structured career roles"
)
async def get_career_catalog(
    db: AsyncSession = Depends(get_db)
):
    await seed_database(db)
    stmt = select(CareerRole).order_by(CareerRole.title)
    res = await db.execute(stmt)
    roles = res.scalars().all()

    roles_data = [
        {
            "id": r.id,
            "slug": r.slug,
            "title": r.title,
            "description": r.description,
            "difficulty_level": r.difficulty_level,
            "required_skills": r.required_skills,
            "preferred_strengths": r.preferred_strengths,
            "interest_areas": r.interest_areas,
            "work_style": r.work_style,
            "responsibilities": r.responsibilities,
            "learning_areas": r.learning_areas
        }
        for r in roles
    ]

    return APIResponse(
        success=True,
        message="Career catalog retrieved",
        data=roles_data
    )


@router.get(
    "/careers/{career_slug}",
    response_model=APIResponse[dict],
    summary="Get detailed metadata for a specific career role"
)
async def get_career_details(
    career_slug: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CareerRole).where(CareerRole.slug == career_slug)
    res = await db.execute(stmt)
    role = res.scalars().first()

    if not role:
        raise HTTPException(status_code=404, detail="Career role not found")

    role_dict = {
        "id": role.id,
        "slug": role.slug,
        "title": role.title,
        "description": role.description,
        "difficulty_level": role.difficulty_level,
        "required_skills": role.required_skills,
        "preferred_strengths": role.preferred_strengths,
        "interest_areas": role.interest_areas,
        "work_style": role.work_style,
        "responsibilities": role.responsibilities,
        "learning_areas": role.learning_areas
    }

    return APIResponse(
        success=True,
        message="Career details retrieved",
        data=role_dict
    )


@router.post(
    "/target-career",
    response_model=APIResponse[dict],
    summary="Select and persist user's target career role"
)
async def select_target_career(
    payload: TargetCareerSelectRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # Verify slug exists in catalog
    stmt = select(CareerRole).where(CareerRole.slug == payload.career_slug)
    res = await db.execute(stmt)
    role = res.scalars().first()

    if not role:
        raise HTTPException(status_code=404, detail=f"Career slug '{payload.career_slug}' not found in catalog")

    # Update UserProfile
    p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    p_res = await db.execute(p_stmt)
    user_profile = p_res.scalars().first()

    if not user_profile:
        user_profile = UserProfile(
            user_id=user_id,
            target_career=role.title,
            primary_archetype="Systems Builder"
        )
        db.add(user_profile)
    else:
        user_profile.target_career = role.title

    # Also update completed AssessmentResponse
    a_stmt = select(AssessmentResponse).where(
        AssessmentResponse.user_id == user_id,
        AssessmentResponse.status == "COMPLETED"
    ).order_by(AssessmentResponse.updated_at.desc())
    a_res = await db.execute(a_stmt)
    session = a_res.scalars().first()
    if session:
        session.selected_target_career = role.title
        db.add(session)

    await db.commit()

    # Recalculate skill profile & gap priorities for new target career
    try:
        from app.services.skill.ingestion_engine import SkillIngestionEngine
        from app.services.skill.gap_engine import SkillGapEngine
        u_skills = await SkillIngestionEngine().ingest_user_skills(db, user_id)
        await SkillGapEngine().calculate_skill_gaps(db, user_id, u_skills)
    except Exception as e:
        logger.warning(f"Background skill sync warning: {e}")

    return APIResponse(
        success=True,
        message=f"Target career set to '{role.title}'",
        data={"target_career": role.title, "slug": role.slug}
    )

