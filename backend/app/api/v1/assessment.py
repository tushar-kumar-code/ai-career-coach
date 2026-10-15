import uuid
import logging
from typing import List, Optional, Set, Tuple
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
from app.models.resume import Resume
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
from app.services.firestore.assessment_repo import AssessmentRepository
from app.services.firestore.user_repo import UserRepository
from app.services.firestore.skills_repo import SkillsRepository

router = APIRouter()
logger = logging.getLogger(__name__)
adaptive_engine = AdaptiveAssessmentEngine()
ai_service = CareerDiscoveryAIService()


async def get_user_past_questions_context(
    db: AsyncSession,
    user_id: str,
    current_session_id: Optional[str] = None
) -> Tuple[Set[str], List[str], int]:
    """Collects question IDs and past answer summaries across all prior assessment sessions for this user."""
    stmt = select(AssessmentResponse).where(AssessmentResponse.user_id == user_id)
    if current_session_id:
        stmt = stmt.where(AssessmentResponse.id != current_session_id)
    res = await db.execute(stmt)
    prev_sessions = res.scalars().all()

    past_ids: Set[str] = set()
    past_summaries: List[str] = []
    for ps in prev_sessions:
        if ps.dimension_answers and isinstance(ps.dimension_answers, dict):
            for qid, ans in ps.dimension_answers.items():
                past_ids.add(str(qid))
                if isinstance(ans, dict):
                    dim = ans.get("dimension", "")
                    txt = ans.get("option_text", "")
                    if dim or txt:
                        past_summaries.append(f"[{dim}]: {txt}")

    attempt_num = len(prev_sessions) + 1
    return past_ids, past_summaries, attempt_num


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

    total_questions = adaptive_engine.MIN_QUESTIONS

    if not retake:
        # Check Firestore for completed assessment
        try:
            fs_completed = await AssessmentRepository.get_latest_completed_assessment(user_id)
            if fs_completed:
                return APIResponse(
                    success=True,
                    message="User has already completed the assessment",
                    data=AssessmentSessionResponse(
                        session_id=fs_completed.get("id"),
                        current_step=total_questions,
                        total_questions=total_questions,
                        is_completed=True,
                        current_question=None,
                        answers_count=total_questions
                    )
                )
        except Exception as e:
            logger.warning(f"Firestore completed assessment check warning: {e}")

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

    # If retake is explicitly requested, abandon any existing incomplete IN_PROGRESS sessions
    if retake:
        old_in_progress_stmt = select(AssessmentResponse).where(
            AssessmentResponse.user_id == user_id,
            AssessmentResponse.status == "IN_PROGRESS"
        )
        old_in_progress_res = await db.execute(old_in_progress_stmt)
        for old_s in old_in_progress_res.scalars().all():
            old_s.status = "ABANDONED"
            db.add(old_s)
        await db.commit()
        session = None
    else:
        # Check for existing IN_PROGRESS assessment for user
        stmt = select(AssessmentResponse).where(
            AssessmentResponse.user_id == user_id,
            AssessmentResponse.status == "IN_PROGRESS"
        ).order_by(AssessmentResponse.created_at.desc())
        res = await db.execute(stmt)
        session = res.scalars().first()

    # Dynamic adaptive question limits
    min_questions = adaptive_engine.MIN_QUESTIONS
    max_questions = adaptive_engine.MAX_SAFETY_QUESTIONS

    # Gather past question context to ensure new/fresh questions on re-assessment
    past_ids, past_summaries, attempt_num = await get_user_past_questions_context(
        db=db,
        user_id=user_id,
        current_session_id=session.id if session else None
    )

    if session:
        answered_ids = list(session.dimension_answers.keys())
        next_q = await adaptive_engine.get_next_question(
            db=db,
            answered_question_ids=answered_ids,
            current_answers=session.dimension_answers,
            language=x_language_preference,
            ai_provider=ai_provider,
            user_level=session.user_level or user_level,
            excluded_question_ids=past_ids,
            past_questions_summary=past_summaries,
            is_retake=retake or (attempt_num > 1),
            attempt_num=attempt_num
        )
        if not next_q and len(answered_ids) >= min_questions:
            # Session had domain predicted by AI or completed
            pass

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

        try:
            await AssessmentRepository.save_assessment(user_id, session.id, {
                "id": session.id,
                "status": "IN_PROGRESS",
                "current_step": 1,
                "user_level": user_level,
                "dimension_answers": {}
            })
        except Exception as e:
            logger.warning(f"Firestore session save warning: {e}")

        answered_ids = []
        next_q = await adaptive_engine.get_next_question(
            db=db,
            answered_question_ids=answered_ids,
            current_answers=session.dimension_answers,
            language=x_language_preference,
            ai_provider=ai_provider,
            user_level=user_level,
            excluded_question_ids=past_ids,
            past_questions_summary=past_summaries,
            is_retake=retake or (attempt_num > 1),
            attempt_num=attempt_num
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

    is_session_completed = session.status == "COMPLETED" or (next_q is None and len(answered_ids) >= min_questions)
    dynamic_total = len(answered_ids) if is_session_completed else max(len(answered_ids) + 1, min_questions)

    session_resp = AssessmentSessionResponse(
        session_id=session.id,
        current_step=len(answered_ids) + 1,
        total_questions=dynamic_total,
        is_completed=is_session_completed,
        current_question=q_schema,
        answers_count=len(answered_ids),
        user_level=session.user_level or user_level
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

    try:
        await AssessmentRepository.save_assessment(user_id, session.id, {
            "status": session.status,
            "current_step": session.current_step,
            "user_level": session.user_level,
            "dimension_answers": updated_answers
        })
    except Exception as e:
        logger.warning(f"Firestore save answer warning: {e}")

    answered_ids = list(updated_answers.keys())
    past_ids, past_summaries, attempt_num = await get_user_past_questions_context(
        db=db,
        user_id=user_id,
        current_session_id=session.id
    )

    next_q = await adaptive_engine.get_next_question(
        db=db,
        answered_question_ids=answered_ids,
        current_answers=updated_answers,
        language=x_language_preference,
        ai_provider=ai_provider,
        user_level=session.user_level or "beginner",
        excluded_question_ids=past_ids,
        past_questions_summary=past_summaries,
        is_retake=(attempt_num > 1),
        attempt_num=attempt_num
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

    min_questions = adaptive_engine.MIN_QUESTIONS
    is_done = (next_q is None and len(answered_ids) >= min_questions)
    dynamic_total = len(answered_ids) if is_done else max(len(answered_ids) + 1, min_questions)

    session_resp = AssessmentSessionResponse(
        session_id=session.id,
        current_step=len(answered_ids) + 1,
        total_questions=dynamic_total,
        is_completed=is_done,
        current_question=q_schema,
        answers_count=len(answered_ids),
        user_level=session.user_level or "beginner"
    )

    return APIResponse(
        success=True,
        message="Answer recorded successfully",
        data=session_resp
    )


async def get_user_resume_profile(db: AsyncSession, user_id: str) -> Optional[dict]:
    """Retrieves structured candidate profile (skills, projects, experience) from UserProfile, Firestore, or Resume table."""
    # 1. Check UserProfile.skills_matrix["candidate_profile"] in DB
    try:
        p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        p_res = await db.execute(p_stmt)
        u_prof = p_res.scalars().first()
        if u_prof and u_prof.skills_matrix and isinstance(u_prof.skills_matrix, dict):
            cand_prof = u_prof.skills_matrix.get("candidate_profile")
            if cand_prof and isinstance(cand_prof, dict) and cand_prof.get("skills"):
                return cand_prof
    except Exception as e:
        logger.warning(f"Error checking UserProfile for candidate_profile: {e}")

    # 2. Check Firestore UserRepository
    try:
        fs_user = await UserRepository.get_user(user_id)
        if fs_user and fs_user.get("candidate_profile"):
            return fs_user.get("candidate_profile")
    except Exception as e:
        logger.warning(f"Firestore get candidate_profile warning: {e}")

    # 3. Check SQLite Resume table
    try:
        r_stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
        r_res = await db.execute(r_stmt)
        resume = r_res.scalars().first()
        if resume:
            skills = []
            if resume.parsed_skills and isinstance(resume.parsed_skills, list):
                skills = [s.get("name") if isinstance(s, dict) else str(s) for s in resume.parsed_skills]
            return {
                "skills": skills,
                "about_user": f"Candidate targeting {resume.target_career_name or 'Tech Role'}",
                "projects": resume.parsed_projects or [],
                "experience": resume.parsed_experience or [],
                "education": resume.parsed_education or []
            }
    except Exception as e:
        logger.warning(f"SQLite resume fallback warning: {e}")

    # 4. Check Firestore ResumeRepository
    try:
        from app.services.firestore.resume_repo import ResumeRepository
        fs_resume = await ResumeRepository.get_latest_resume(user_id)
        if fs_resume:
            skills = [s.get("name") if isinstance(s, dict) else str(s) for s in fs_resume.get("parsed_skills", [])]
            return {
                "skills": skills,
                "about_user": fs_resume.get("target_career_name", "Tech Professional"),
                "projects": fs_resume.get("parsed_projects", []),
                "experience": fs_resume.get("parsed_experience", []),
                "education": fs_resume.get("parsed_education", [])
            }
    except Exception as e:
        logger.warning(f"Firestore resume repo fallback warning: {e}")

    return None


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
        # Check Firestore for session
        fs_session = await AssessmentRepository.get_assessment(user_id, session_id)
        if not fs_session or not fs_session.get("dimension_answers"):
            raise HTTPException(status_code=404, detail="Assessment session not found")
        # Build mock session object for backward compatibility
        dimension_answers = fs_session.get("dimension_answers")
    else:
        dimension_answers = session.dimension_answers

    if not dimension_answers:
        raise HTTPException(status_code=400, detail="Cannot complete assessment without answers")

    # Fetch user's candidate profile from resume if available (synthesizes Resume + Assessment)
    resume_profile = await get_user_resume_profile(db, user_id)
    if resume_profile:
        logger.info(f"Synthesizing career domain suggestions with Resume ({len(resume_profile.get('skills', []))} skills) and Discovery Assessment")
    else:
        logger.info("Running Career Discovery AI Analysis based on assessment responses")

    # Run AI Analysis with both assessment answers and resume profile!
    ai_result = await ai_service.analyze_assessment(
        db,
        dimension_answers,
        resume_profile=resume_profile,
        language=x_language_preference
    )
    ai_dict = ai_result.model_dump()

    # Update session status
    if session:
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

    existing_skills_mat = dict(user_profile.skills_matrix or {}) if user_profile and user_profile.skills_matrix else {}
    existing_skills_mat["verified_skills"] = [s.model_dump() for s in ai_result.top_strengths]
    existing_skills_mat["interests"] = ai_result.interest_profile
    if resume_profile and "candidate_profile" not in existing_skills_mat:
        existing_skills_mat["candidate_profile"] = resume_profile

    if not user_profile:
        user_profile = UserProfile(
            user_id=user_id,
            target_career=target_role,
            primary_archetype=ai_result.primary_archetype,
            job_readiness_score=top_score,
            skills_matrix=existing_skills_mat,
            recommended_roles=[r.model_dump() for r in ai_result.recommended_careers]
        )
    else:
        user_profile.primary_archetype = ai_result.primary_archetype
        user_profile.job_readiness_score = top_score
        user_profile.recommended_roles = [r.model_dump() for r in ai_result.recommended_careers]
        user_profile.skills_matrix = existing_skills_mat

    db.add(user_profile)
    await db.commit()

    # Persist to Firestore AssessmentRepository & UserRepository
    try:
        await AssessmentRepository.save_assessment(user_id, session_id, {
            "status": "COMPLETED",
            "computed_archetype": ai_result.primary_archetype,
            "role_recommendations": [r.model_dump() for r in ai_result.recommended_careers],
            "ai_analysis_json": ai_dict,
            "selected_target_career": target_role
        })
        await UserRepository.upsert_user(user_id, {
            "target_career": target_role,
            "primary_archetype": ai_result.primary_archetype,
            "job_readiness_score": top_score,
            "has_completed_assessment": True,
            "skills_matrix": existing_skills_mat,
            "recommended_roles": [r.model_dump() for r in ai_result.recommended_careers]
        })
    except Exception as e:
        logger.warning(f"Firestore complete assessment save warning: {e}")

    return APIResponse(
        success=True,
        message="Career Discovery Assessment completed successfully",
        data={
            "session_id": session_id,
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
    # 1. Check Firestore first
    try:
        fs_session = await AssessmentRepository.get_latest_completed_assessment(user_id)
        if fs_session and fs_session.get("ai_analysis_json"):
            fs_user = await UserRepository.get_user(user_id)
            target_career = (fs_user.get("target_career") if fs_user else None) or fs_session.get("selected_target_career")
            return APIResponse(
                success=True,
                message="Career Discovery Result retrieved",
                data={
                    "session_id": fs_session.get("id"),
                    "selected_target_career": target_career,
                    "archetype": fs_session.get("computed_archetype"),
                    "analysis": fs_session.get("ai_analysis_json"),
                    "completed_at": fs_session.get("updated_at")
                }
            )
    except Exception as e:
        logger.warning(f"Firestore get_assessment_result warning: {e}")

    # 2. SQLite fallback
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
    "/suggested-domains",
    response_model=APIResponse[dict],
    summary="Get holistic career domain suggestions based on both Resume and Discovery Assessment"
)
async def get_suggested_domains(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    x_language_preference: str = Header(default="en", alias="X-Language-Preference")
):
    """
    Returns AI-synthesized career domains combining:
    1. Psychological strengths & work preferences from Discovery Assessment
    2. Verified skills, real projects, and work experience from Uploaded Resume
    """
    resume_profile = await get_user_resume_profile(db, user_id)
    
    # 1. Fetch latest assessment session
    stmt = select(AssessmentResponse).where(
        AssessmentResponse.user_id == user_id,
        AssessmentResponse.status == "COMPLETED"
    ).order_by(AssessmentResponse.updated_at.desc())
    res = await db.execute(stmt)
    session = res.scalars().first()

    fs_session = None
    if not session:
        try:
            fs_session = await AssessmentRepository.get_latest_completed_assessment(user_id)
        except Exception as e:
            logger.warning(f"Firestore get_latest_completed_assessment warning: {e}")

    session_analysis = (session.ai_analysis_json if session else None) or (fs_session.get("ai_analysis_json") if fs_session else None)
    dimension_answers = (session.dimension_answers if session else None) or (fs_session.get("dimension_answers") if fs_session else None)

    has_resume = bool(resume_profile and resume_profile.get("skills"))
    has_assessment = bool(session_analysis or dimension_answers)

    if not has_resume and not has_assessment:
        return APIResponse(
            success=False,
            message="No assessment or resume found. Complete the discovery assessment or upload a resume to receive tailored career domains.",
            data={
                "has_resume": False,
                "has_assessment": False,
                "suggested_domains": [],
                "domain_clusters": [],
                "recommended_careers": [],
                "primary_archetype": None,
                "career_domains_summary": "Take our adaptive assessment or upload your resume to discover your tailored career domains."
            }
        )

    recommended_careers = (session_analysis.get("recommended_careers", []) if session_analysis else [])

    # Check if synthesis with resume is needed (e.g. user has resume but recommendations lack resume_match_reasons)
    needs_resynthesis = False
    if has_resume and dimension_answers:
        if not recommended_careers or not recommended_careers[0].get("resume_match_reasons"):
            needs_resynthesis = True

    if needs_resynthesis and dimension_answers:
        try:
            logger.info("Auto-synthesizing career domains with fresh resume profile and assessment answers...")
            dual_ai_result = await ai_service.analyze_assessment(
                db,
                dimension_answers,
                resume_profile=resume_profile,
                language=x_language_preference
            )
            session_analysis = dual_ai_result.model_dump()
            recommended_careers = session_analysis.get("recommended_careers", [])
            if session:
                session.ai_analysis_json = session_analysis
                session.role_recommendations = [r.model_dump() for r in dual_ai_result.recommended_careers]
                db.add(session)
                await db.commit()
        except Exception as e:
            logger.warning(f"Re-synthesis in suggested-domains error: {e}")

    # Group into structured Domain Clusters
    domains_map = {}
    for c in recommended_careers:
        dom_name = c.get("career_domain") or "Core Technology & Software"
        if dom_name not in domains_map:
            domains_map[dom_name] = {
                "domain_name": dom_name,
                "highest_match": c.get("match_percentage", 75),
                "roles": [],
                "key_resume_skills": [],
                "key_assessment_traits": []
            }
        domains_map[dom_name]["roles"].append(c)
        if c.get("match_percentage", 0) > domains_map[dom_name]["highest_match"]:
            domains_map[dom_name]["highest_match"] = c.get("match_percentage")
        for r_reason in c.get("resume_match_reasons", []):
            if r_reason not in domains_map[dom_name]["key_resume_skills"]:
                domains_map[dom_name]["key_resume_skills"].append(r_reason)
        for a_reason in c.get("assessment_match_reasons", []):
            if a_reason not in domains_map[dom_name]["key_assessment_traits"]:
                domains_map[dom_name]["key_assessment_traits"].append(a_reason)

    domain_clusters = sorted(domains_map.values(), key=lambda d: d["highest_match"], reverse=True)

    summary_text = (
        session_analysis.get("career_domains_summary")
        if session_analysis and session_analysis.get("career_domains_summary")
        else "Career domains identified by aligning your problem-solving style with verified resume competencies."
    )

    archetype = (
        (session_analysis.get("primary_archetype") if session_analysis else None)
        or (session.computed_archetype if session else None)
        or "Systems Builder"
    )

    return APIResponse(
        success=True,
        message="Synthesized career domains retrieved successfully",
        data={
            "has_resume": has_resume,
            "has_assessment": has_assessment,
            "primary_archetype": archetype,
            "career_domains_summary": summary_text,
            "domain_clusters": domain_clusters,
            "recommended_careers": recommended_careers,
            "resume_profile_preview": {
                "skills_count": len(resume_profile.get("skills", [])) if resume_profile else 0,
                "top_skills": (resume_profile.get("skills") or [])[:8] if resume_profile else [],
                "projects_count": len(resume_profile.get("projects", [])) if resume_profile else 0,
                "experience_count": len(resume_profile.get("experience", [])) if resume_profile else 0
            } if resume_profile else None
        }
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
    # 1. Check Firestore first
    try:
        has_completed_fs = await AssessmentRepository.has_completed_assessment(user_id)
        fs_user = await UserRepository.get_user(user_id)
        if has_completed_fs or (fs_user and fs_user.get("has_completed_assessment")):
            fs_session = await AssessmentRepository.get_latest_completed_assessment(user_id)
            return APIResponse(
                success=True,
                message="Assessment status retrieved",
                data={
                    "has_completed_assessment": True,
                    "target_career": (fs_user.get("target_career") if fs_user else None) or (fs_session.get("selected_target_career") if fs_session else None),
                    "primary_archetype": (fs_user.get("primary_archetype") if fs_user else None) or (fs_session.get("computed_archetype") if fs_session else None),
                    "job_readiness_score": fs_user.get("job_readiness_score", 0) if fs_user else 0
                }
            )
    except Exception as e:
        logger.warning(f"Firestore get_assessment_status warning: {e}")

    # 2. SQLite fallback
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

    # Persist to Firestore UserRepository & AssessmentRepository
    try:
        await UserRepository.update_target_career(user_id, role.title, role.work_style)
        fs_session = await AssessmentRepository.get_latest_completed_assessment(user_id)
        if fs_session:
            await AssessmentRepository.save_assessment(user_id, fs_session.get("id"), {"selected_target_career": role.title})
    except Exception as e:
        logger.warning(f"Firestore update target career error: {e}")

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

    # 2. Ingest user's known skills into database & Firestore
    known_skills = [s.strip() for s in payload.known_skills if s.strip()]
    from app.models.skill import Skill
    for sk_name in known_skills:
        try:
            await SkillsRepository.upsert_skill_by_name(
                user_id,
                sk_name,
                {
                    "category": "Technical",
                    "proficiency_level": "Intermediate" if payload.experience_level in ["intermediate", "advanced"] else "Beginner",
                    "confidence_status": "Claimed"
                }
            )
        except Exception as e:
            logger.warning(f"Firestore skill upsert error for {sk_name}: {e}")

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

    # Persist to Firestore UserRepository & AssessmentRepository
    try:
        await UserRepository.upsert_user(user_id, {
            "target_career": role_title,
            "primary_archetype": archetype,
            "job_readiness_score": readiness_score,
            "has_completed_assessment": True,
            "skills_matrix": skills_matrix_payload
        })
        session_id = session.id if session else str(uuid.uuid4())
        await AssessmentRepository.save_assessment(user_id, session_id, {
            "id": session_id,
            "status": "COMPLETED",
            "user_level": payload.experience_level,
            "computed_archetype": archetype,
            "selected_target_career": role_title,
            "ai_analysis_json": analysis_data
        })
    except Exception as e:
        logger.warning(f"Firestore direct goal save error: {e}")

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


