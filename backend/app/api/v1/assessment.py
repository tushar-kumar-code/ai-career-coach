from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.init_db import seed_database
from app.core.ai_deps import get_ai_provider_from_headers
from app.services.ai.base import BaseLLMProvider
from app.models.assessment import AssessmentResponse
from app.models.question import Question
from app.models.career_catalog import CareerRole
from app.models.profile import UserProfile
from app.schemas.health import APIResponse
from app.schemas.assessment import (
    AssessmentSessionResponse,
    AssessmentStartRequest,
    QuestionSchema,
    QuestionOptionSchema,
    AnswerSubmitRequest,
    TargetCareerSelectRequest,
    DirectCareerGoalRequest
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
    payload: AssessmentStartRequest = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    ai_provider: BaseLLMProvider = Depends(get_ai_provider_from_headers),
    x_language_preference: str = Header(default="en", alias="X-Language-Preference")
):
    if payload is None:
        payload = AssessmentStartRequest()
    retake = payload.retake
    user_level = payload.user_level or "beginner"
    # Seed DB questions and career roles if empty
    await seed_database(db)

    total_questions = adaptive_engine.MAX_QUESTIONS_PER_SESSION

    if not retake:
        completed_stmt = select(AssessmentResponse).where(
            AssessmentResponse.user_id == user_id,
            AssessmentResponse.status == "COMPLETED"
        ).order_by(AssessmentResponse.updated_at.desc())
        comp_res = await db.execute(completed_stmt)
        completed_session = comp_res.scalars().first()

        if completed_session:
            return APIResponse(
                success=True,
                message="User has already completed the assessment",
                data=AssessmentSessionResponse(
                    session_id=completed_session.id,
                    current_step=total_questions,
                    total_questions=total_questions,
                    is_completed=True,
                    current_question=None,
                    answers_count=total_questions
                )
            )

    # Check for existing IN_PROGRESS assessment for user
    stmt = select(AssessmentResponse).where(
        AssessmentResponse.user_id == user_id,
        AssessmentResponse.status == "IN_PROGRESS"
    ).order_by(AssessmentResponse.created_at.desc())
    res = await db.execute(stmt)
    session = res.scalars().first()

    total_questions = adaptive_engine.MAX_QUESTIONS_PER_SESSION

    if session:
        answered_ids = list(session.dimension_answers.keys())
        next_q = await adaptive_engine.get_next_question(
            db=db,
            answered_question_ids=answered_ids,
            current_answers=session.dimension_answers,
            language=x_language_preference,
            ai_provider=ai_provider,
            user_level=session.user_level or user_level
        )
        if not next_q and len(answered_ids) >= total_questions:
            # Session had all questions answered; start a fresh assessment session
            session = None

    if not session:
        session = AssessmentResponse(
            user_id=user_id,
            status="IN_PROGRESS",
            current_step=1,
            user_level=user_level,
            dimension_answers={}
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        answered_ids = []
        next_q = await adaptive_engine.get_next_question(
            db=db,
            answered_question_ids=answered_ids,
            current_answers=session.dimension_answers,
            language=x_language_preference,
            ai_provider=ai_provider
        )

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
            order_index=next_q.order_index,
            allow_custom=True
        )

    session_resp = AssessmentSessionResponse(
        session_id=session.id,
        current_step=len(answered_ids) + 1,
        total_questions=total_questions,
        is_completed=session.status == "COMPLETED" or next_q is None,
        current_question=q_schema,
        answers_count=len(answered_ids),
        user_level=session.user_level or "beginner"
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
    user_id: str = Depends(get_current_user_id),
    ai_provider: BaseLLMProvider = Depends(get_ai_provider_from_headers),
    x_language_preference: str = Header(default="en", alias="X-Language-Preference")
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

    # Find matching option — or accept custom text answer
    is_custom = payload.selected_option_id == "custom"
    if is_custom:
        if not payload.custom_answer or not payload.custom_answer.strip():
            raise HTTPException(status_code=400, detail="Custom answer text is required when selecting 'custom' option")
        selected_opt = {"id": "custom", "text": payload.custom_answer.strip(), "archetype": None}
    else:
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

    total_questions = adaptive_engine.MAX_QUESTIONS_PER_SESSION

    answered_ids = list(updated_answers.keys())
    next_q = await adaptive_engine.get_next_question(
        db=db,
        answered_question_ids=answered_ids,
        current_answers=updated_answers,
        language=x_language_preference,
        ai_provider=ai_provider,
        user_level=session.user_level or "beginner"
    )

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
            order_index=next_q.order_index,
            allow_custom=True
        )

    session_resp = AssessmentSessionResponse(
        session_id=session.id,
        current_step=len(answered_ids) + 1,
        total_questions=total_questions,
        is_completed=next_q is None,
        current_question=q_schema,
        answers_count=len(answered_ids),
        user_level=session.user_level or "beginner"
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
    user_id: str = Depends(get_current_user_id),
    x_language_preference: str = Header(default="en", alias="X-Language-Preference")
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
    ai_result = await ai_service.analyze_assessment(db, session.dimension_answers, language=x_language_preference)
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
        AssessmentResponse.status == "COMPLETED",
        AssessmentResponse.ai_analysis_json.isnot(None)
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
        "selected_target_career": user_profile.target_career if user_profile and user_profile.target_career else session.selected_target_career,
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
    "/status",
    response_model=APIResponse[dict],
    summary="Get user's career assessment completion status"
)
async def get_assessment_status(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """Returns whether the current user has completed their onboarding career assessment."""
    stmt = select(AssessmentResponse).where(
        AssessmentResponse.user_id == user_id,
        AssessmentResponse.status == "COMPLETED",
        AssessmentResponse.ai_analysis_json.isnot(None)
    ).order_by(AssessmentResponse.updated_at.desc())
    res = await db.execute(stmt)
    session = res.scalars().first()

    has_completed = session is not None

    p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    p_res = await db.execute(p_stmt)
    user_profile = p_res.scalars().first()

    return APIResponse(
        success=True,
        message="Assessment status retrieved",
        data={
            "has_completed_assessment": has_completed,
            "target_career": (user_profile.target_career if user_profile else None) or (session.selected_target_career if session else None),
            "primary_archetype": (user_profile.primary_archetype if user_profile else None) or (session.computed_archetype if session else None),
            "job_readiness_score": user_profile.job_readiness_score if user_profile else 0
        }
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


@router.post(
    "/direct-goal",
    response_model=APIResponse[dict],
    summary="Submit direct career goal with known skills and automatic gap analysis"
)
async def submit_direct_career_goal(
    payload: DirectCareerGoalRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    await seed_database(db)
    target_career = payload.target_career.strip()
    if not target_career:
        raise HTTPException(status_code=400, detail="Target career cannot be empty")

    # 1. Fetch career role metadata from catalog if available
    slug = payload.career_slug or target_career.lower().replace(" ", "-").replace("/", "-")
    stmt = select(CareerRole).where((CareerRole.slug == slug) | (CareerRole.title.ilike(f"%{target_career}%")))
    res = await db.execute(stmt)
    role = res.scalars().first()

    catalog_skills = role.required_skills if role and role.required_skills else [
        "Data Structures", "Problem Solving", "Git & Version Control", "Database Fundamentals"
    ]
    role_title = role.title if role else target_career
    archetype = role.work_style if role and role.work_style else "Strategic Builder"

    # 2. Ingest user's known skills into database
    known_skills = [s.strip() for s in payload.known_skills if s.strip()]
    from app.models.skill import Skill
    for sk_name in known_skills:
        sk_stmt = select(Skill).where(Skill.user_id == user_id, Skill.skill_name.ilike(sk_name))
        sk_res = await db.execute(sk_stmt)
        existing_sk = sk_res.scalars().first()
        if not existing_sk:
            new_sk = Skill(
                user_id=user_id,
                skill_name=sk_name,
                normalized_name=sk_name.lower().strip(),
                category="Technical",
                proficiency_level="Intermediate" if payload.experience_level in ["intermediate", "advanced"] else "Beginner",
                confidence_status="Claimed"
            )
            db.add(new_sk)

    # 3. Compute verified vs missing gaps
    verified_skills = []
    missing_gaps = []
    lower_known = {k.lower() for k in known_skills}
    for req_sk in catalog_skills:
        if req_sk.lower() in lower_known or any(k in req_sk.lower() for k in lower_known):
            verified_skills.append(req_sk)
        else:
            missing_gaps.append(req_sk)

    # If user selected scratch, all catalog skills are missing gaps
    if payload.experience_level == "scratch":
        missing_gaps = list(catalog_skills)
        verified_skills = []
        readiness_score = 0
    else:
        readiness_score = int((len(verified_skills) / max(len(catalog_skills), 1)) * 100) if catalog_skills else 50

    # 4. Save/Update UserProfile
    p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    p_res = await db.execute(p_stmt)
    user_profile = p_res.scalars().first()

    skills_matrix_payload = {
        "known_skills": known_skills,
        "verified_skills": [{"name": s, "level": "Known"} for s in verified_skills],
        "missing_gaps": missing_gaps,
        "experience_level": payload.experience_level
    }

    if not user_profile:
        user_profile = UserProfile(
            user_id=user_id,
            target_career=role_title,
            primary_archetype=archetype,
            job_readiness_score=readiness_score,
            skills_matrix=skills_matrix_payload
        )
        db.add(user_profile)
    else:
        user_profile.target_career = role_title
        user_profile.primary_archetype = archetype
        user_profile.job_readiness_score = readiness_score
        user_profile.skills_matrix = skills_matrix_payload
        db.add(user_profile)

    # 5. Save/Update completed AssessmentResponse
    a_stmt = select(AssessmentResponse).where(
        AssessmentResponse.user_id == user_id
    ).order_by(AssessmentResponse.updated_at.desc())
    a_res = await db.execute(a_stmt)
    session = a_res.scalars().first()

    analysis_data = {
        "primary_archetype": archetype,
        "direct_career_track": True,
        "experience_level": payload.experience_level,
        "target_career": role_title,
        "readiness_score": readiness_score,
        "known_skills": known_skills,
        "missing_gaps": missing_gaps,
        "top_strengths": [{"strength_name": s, "evidence_reason": "Verified user-known skill"} for s in known_skills],
        "recommended_careers": [
            {
                "title": role_title,
                "match_percentage": max(readiness_score, 80),
                "slug": slug,
                "reasoning": f"Directly selected career path with {payload.experience_level.title()} starting proficiency."
            }
        ]
    }

    if not session:
        session = AssessmentResponse(
            user_id=user_id,
            status="COMPLETED",
            user_level=payload.experience_level,
            computed_archetype=archetype,
            selected_target_career=role_title,
            ai_analysis_json=analysis_data
        )
        db.add(session)
    else:
        session.status = "COMPLETED"
        session.user_level = payload.experience_level
        session.computed_archetype = archetype
        session.selected_target_career = role_title
        session.ai_analysis_json = analysis_data
        db.add(session)

    await db.commit()

    # Recalculate skill gaps
    try:
        from app.services.skill.ingestion_engine import SkillIngestionEngine
        from app.services.skill.gap_engine import SkillGapEngine
        u_skills = await SkillIngestionEngine().ingest_user_skills(db, user_id)
        await SkillGapEngine().calculate_skill_gaps(db, user_id, u_skills)
    except Exception as e:
        pass

    return APIResponse(
        success=True,
        message=f"Target career set to {role_title} with personalized skill gap analysis.",
        data={
            "target_career": role_title,
            "experience_level": payload.experience_level,
            "readiness_score": readiness_score,
            "known_skills": known_skills,
            "missing_gaps": missing_gaps,
            "total_required": len(catalog_skills),
            "analysis": analysis_data
        }
    )

