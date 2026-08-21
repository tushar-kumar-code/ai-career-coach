from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.interview import InterviewSession
from app.models.profile import UserProfile
from app.schemas.health import APIResponse
from app.schemas.interview import (
    InterviewStartRequest,
    InterviewAnswerRequest,
    InterviewEvaluationResponse,
    InterviewSessionResponse,
    InterviewQuestionSchema,
    InterviewFinalReportResponse,
    InterviewReadinessResponse,
    STARAnalysis
)
from app.services.interview.question_generator import InterviewQuestionGenerator
from app.services.interview.evaluator import InterviewEvaluator
from app.services.interview.adaptive_engine import AdaptiveInterviewEngine
from app.services.interview.feedback_loop import InterviewFeedbackLoop

import copy

router = APIRouter()
question_generator = InterviewQuestionGenerator()
evaluator = InterviewEvaluator()
adaptive_engine = AdaptiveInterviewEngine()
feedback_loop = InterviewFeedbackLoop()


@router.post(
    "/start",
    response_model=APIResponse[InterviewSessionResponse],
    summary="Start a personalized, adaptive mock interview session"
)
async def start_interview_session(
    req: InterviewStartRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # Fetch target role from profile if omitted
    target_role = req.target_role
    if not target_role:
        stmt_prof = select(UserProfile).where(UserProfile.user_id == user_id)
        res_prof = await db.execute(stmt_prof)
        prof = res_prof.scalar_one_or_none()
        target_role = prof.target_career if prof and prof.target_career else "Software Developer"

    # Generate first question (Index 0)
    q0_data = await question_generator.generate_question(
        db=db,
        user_id=user_id,
        mode=req.mode,
        difficulty=req.difficulty,
        question_index=0,
        previous_evaluations=[],
        job_id=req.job_id,
        target_role_override=target_role,
        topic_focus=req.topic_focus
    )

    questions_list = [q0_data]

    session = InterviewSession(
        user_id=user_id,
        job_id=req.job_id,
        target_role=target_role,
        mode=req.mode,
        difficulty=req.difficulty,
        question_count=max(1, req.question_count),
        current_question_index=0,
        is_completed=False,
        questions_data=questions_list,
        question_text=q0_data["question_text"]
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    curr_q_schema = InterviewQuestionSchema(
        question_index=0,
        category=q0_data["category"],
        difficulty=q0_data["difficulty"],
        question_text=q0_data["question_text"],
        context_tip=q0_data.get("context_tip")
    )

    resp = InterviewSessionResponse(
        id=session.id,
        user_id=session.user_id,
        job_id=session.job_id,
        target_role=session.target_role,
        mode=session.mode,
        difficulty=session.difficulty,
        question_count=session.question_count,
        current_question_index=session.current_question_index,
        is_completed=session.is_completed,
        current_question=curr_q_schema,
        overall_score=session.overall_score,
        category_scores=session.category_scores or {},
        readiness_status=session.readiness_status,
        readiness_explanation=session.readiness_explanation,
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else ""
    )

    return APIResponse(
        success=True,
        message="Interview session started successfully",
        data=resp
    )


@router.get(
    "/session/{session_id}",
    response_model=APIResponse[InterviewSessionResponse],
    summary="Get session details and current question"
)
async def get_interview_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(InterviewSession).where(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
    res = await db.execute(stmt)
    session = res.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail=f"Interview session '{session_id}' not found")

    q_data_list = session.questions_data or []
    curr_idx = session.current_question_index

    curr_q_schema = None
    if curr_idx < len(q_data_list):
        raw_q = q_data_list[curr_idx]
        eval_raw = raw_q.get("evaluation")
        eval_schema = None
        if eval_raw:
            eval_schema = InterviewEvaluationResponse(**eval_raw)

        curr_q_schema = InterviewQuestionSchema(
            question_index=raw_q.get("question_index", curr_idx),
            category=raw_q.get("category", "Technical"),
            difficulty=raw_q.get("difficulty", session.difficulty),
            question_text=raw_q.get("question_text", ""),
            context_tip=raw_q.get("context_tip"),
            user_answer=raw_q.get("user_answer"),
            score=raw_q.get("score"),
            evaluation=eval_schema
        )

    resp = InterviewSessionResponse(
        id=session.id,
        user_id=session.user_id,
        job_id=session.job_id,
        target_role=session.target_role,
        mode=session.mode,
        difficulty=session.difficulty,
        question_count=session.question_count,
        current_question_index=session.current_question_index,
        is_completed=session.is_completed,
        current_question=curr_q_schema,
        overall_score=session.overall_score,
        category_scores=session.category_scores or {},
        readiness_status=session.readiness_status,
        readiness_explanation=session.readiness_explanation,
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else ""
    )

    return APIResponse(
        success=True,
        message="Session details retrieved",
        data=resp
    )


@router.post(
    "/session/{session_id}/answer",
    response_model=APIResponse[InterviewEvaluationResponse],
    summary="Submit user answer and get AI evaluation"
)
async def submit_interview_answer(
    session_id: str,
    req: InterviewAnswerRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(InterviewSession).where(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
    res = await db.execute(stmt)
    session = res.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail=f"Interview session '{session_id}' not found")

    if session.is_completed:
        raise HTTPException(status_code=400, detail="Interview session is already completed")

    q_data_list = copy.deepcopy(session.questions_data or [])
    curr_idx = session.current_question_index

    if curr_idx >= len(q_data_list):
        raise HTTPException(status_code=400, detail="No active question available for answer submission")

    curr_q = q_data_list[curr_idx]

    # Evaluate answer using multi-category evaluator
    eval_dict = await evaluator.evaluate_answer(
        question_text=curr_q["question_text"],
        category=curr_q["category"],
        difficulty=curr_q["difficulty"],
        user_answer=req.answer_text,
        target_role=session.target_role
    )

    curr_q["user_answer"] = req.answer_text
    curr_q["score"] = eval_dict["score"]
    curr_q["evaluation"] = eval_dict

    q_data_list[curr_idx] = curr_q
    session.questions_data = q_data_list
    flag_modified(session, "questions_data")

    # Store backward compatibility values
    session.user_answer_text = req.answer_text
    session.star_score = eval_dict["score"]
    session.feedback_breakdown = eval_dict

    await db.commit()
    await db.refresh(session)

    star_analysis = None
    if eval_dict.get("situation_feedback") or eval_dict.get("star_complete"):
        star_analysis = STARAnalysis(
            situation_feedback=eval_dict.get("situation_feedback"),
            task_feedback=eval_dict.get("task_feedback"),
            action_feedback=eval_dict.get("action_feedback"),
            result_feedback=eval_dict.get("result_feedback"),
            star_complete=eval_dict.get("star_complete", False)
        )

    resp = InterviewEvaluationResponse(
        score=eval_dict["score"],
        technical_score=eval_dict.get("technical_score", eval_dict["score"]),
        communication_score=eval_dict.get("communication_score", eval_dict["score"]),
        problem_solving_score=eval_dict.get("problem_solving_score", eval_dict["score"]),
        behavioral_score=eval_dict.get("behavioral_score", eval_dict["score"]),
        resume_knowledge_score=eval_dict.get("resume_knowledge_score", eval_dict["score"]),
        strengths=eval_dict.get("strengths", []),
        weaknesses=eval_dict.get("weaknesses", []),
        missing_points=eval_dict.get("missing_points", []),
        suggested_improvement=eval_dict.get("suggested_improvement", ""),
        ideal_answer_outline=eval_dict.get("ideal_answer_outline", []),
        star_analysis=star_analysis,
        detected_weak_topic=eval_dict.get("detected_weak_topic")
    )

    return APIResponse(
        success=True,
        message="Answer evaluated successfully",
        data=resp
    )


@router.post(
    "/session/{session_id}/next",
    response_model=APIResponse[InterviewSessionResponse],
    summary="Adaptively generate next question based on answer performance"
)
async def next_interview_question(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(InterviewSession).where(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
    res = await db.execute(stmt)
    session = res.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail=f"Interview session '{session_id}' not found")

    q_data_list = copy.deepcopy(session.questions_data or [])
    curr_idx = session.current_question_index
    next_idx = curr_idx + 1

    # Check if session questions reached total question count
    if next_idx >= session.question_count:
        # Auto-complete session
        return await complete_interview_session(session_id=session_id, db=db, user_id=user_id)

    # Compute adaptive difficulty for next question based on previous answer score
    last_q = q_data_list[curr_idx] if curr_idx < len(q_data_list) else {}
    last_score = last_q.get("score", 70) if isinstance(last_q, dict) else 70

    next_diff = adaptive_engine.compute_next_difficulty(session.difficulty, last_score)
    session.difficulty = next_diff

    # Generate next question
    next_q_data = await question_generator.generate_question(
        db=db,
        user_id=user_id,
        mode=session.mode,
        difficulty=next_diff,
        question_index=next_idx,
        previous_evaluations=[q.get("evaluation") for q in q_data_list if q.get("evaluation")],
        job_id=session.job_id,
        target_role_override=session.target_role
    )

    q_data_list.append(next_q_data)
    session.questions_data = q_data_list
    session.current_question_index = next_idx
    flag_modified(session, "questions_data")

    await db.commit()
    await db.refresh(session)

    curr_q_schema = InterviewQuestionSchema(
        question_index=next_idx,
        category=next_q_data["category"],
        difficulty=next_q_data["difficulty"],
        question_text=next_q_data["question_text"],
        context_tip=next_q_data.get("context_tip")
    )

    resp = InterviewSessionResponse(
        id=session.id,
        user_id=session.user_id,
        job_id=session.job_id,
        target_role=session.target_role,
        mode=session.mode,
        difficulty=session.difficulty,
        question_count=session.question_count,
        current_question_index=session.current_question_index,
        is_completed=session.is_completed,
        current_question=curr_q_schema,
        overall_score=session.overall_score,
        category_scores=session.category_scores or {},
        readiness_status=session.readiness_status,
        readiness_explanation=session.readiness_explanation,
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else ""
    )

    return APIResponse(
        success=True,
        message="Next adaptive question generated",
        data=resp
    )


@router.post(
    "/session/{session_id}/complete",
    response_model=APIResponse[InterviewFinalReportResponse],
    summary="Finalize interview session, aggregate sub-scores & trigger Skill/Roadmap feedback loops"
)
async def complete_interview_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(InterviewSession).where(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
    res = await db.execute(stmt)
    session = res.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail=f"Interview session '{session_id}' not found")

    q_data_list = session.questions_data or []

    # Calculate score aggregation
    overall_score, category_scores, readiness_status, readiness_explanation, weak_topics = (
        adaptive_engine.aggregate_session_scores(q_data_list)
    )

    session.is_completed = True
    session.overall_score = overall_score
    session.category_scores = category_scores
    session.readiness_status = readiness_status
    session.readiness_explanation = readiness_explanation
    session.weak_areas = weak_topics

    # Process Skill & Roadmap feedback loops
    recommended_topics = await feedback_loop.process_interview_feedback(
        db=db,
        user_id=user_id,
        target_role=session.target_role,
        overall_score=overall_score,
        category_scores=category_scores,
        weak_areas=weak_topics,
        questions_data=q_data_list
    )

    await db.commit()
    await db.refresh(session)

    # Build Q&A Review List
    review_list = []
    for q in q_data_list:
        eval_raw = q.get("evaluation")
        eval_schema = InterviewEvaluationResponse(**eval_raw) if eval_raw else None
        review_list.append(
            InterviewQuestionSchema(
                question_index=q.get("question_index", 0),
                category=q.get("category", "Technical"),
                difficulty=q.get("difficulty", session.difficulty),
                question_text=q.get("question_text", ""),
                context_tip=q.get("context_tip"),
                user_answer=q.get("user_answer"),
                score=q.get("score"),
                evaluation=eval_schema
            )
        )

    report = InterviewFinalReportResponse(
        session_id=session.id,
        target_role=session.target_role,
        mode=session.mode,
        difficulty=session.difficulty,
        overall_score=overall_score,
        technical_score=category_scores.get("technical", overall_score),
        communication_score=category_scores.get("communication", overall_score),
        problem_solving_score=category_scores.get("problem_solving", overall_score),
        behavioral_score=category_scores.get("behavioral", overall_score),
        resume_knowledge_score=category_scores.get("resume_knowledge", overall_score),
        readiness_status=readiness_status,
        readiness_explanation=readiness_explanation,
        strong_areas=["Demonstrated core technical understanding"] if overall_score >= 70 else ["Attempted questions"],
        weak_areas=weak_topics,
        recommended_roadmap_topics=recommended_topics,
        questions_review=review_list
    )

    return APIResponse(
        success=True,
        message="Interview completed and final report generated",
        data=report
    )


@router.get(
    "/history",
    response_model=APIResponse[List[InterviewSessionResponse]],
    summary="Get user's previous interview sessions history"
)
async def get_interview_history(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(InterviewSession).where(InterviewSession.user_id == user_id).order_by(InterviewSession.created_at.desc())
    res = await db.execute(stmt)
    sessions = res.scalars().all()

    responses = [
        InterviewSessionResponse(
            id=s.id,
            user_id=s.user_id,
            job_id=s.job_id,
            target_role=s.target_role,
            mode=s.mode,
            difficulty=s.difficulty,
            question_count=s.question_count,
            current_question_index=s.current_question_index,
            is_completed=s.is_completed,
            overall_score=s.overall_score,
            category_scores=s.category_scores or {},
            readiness_status=s.readiness_status,
            readiness_explanation=s.readiness_explanation,
            created_at=s.created_at.isoformat() if s.created_at else "",
            updated_at=s.updated_at.isoformat() if s.updated_at else ""
        )
        for s in sessions
    ]

    return APIResponse(
        success=True,
        message="Interview history retrieved",
        data=responses
    )


@router.get(
    "/session/{session_id}/results",
    response_model=APIResponse[InterviewFinalReportResponse],
    summary="Get full final interview report for a completed session"
)
async def get_interview_results(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(InterviewSession).where(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
    res = await db.execute(stmt)
    session = res.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail=f"Interview session '{session_id}' not found")

    q_data_list = session.questions_data or []
    review_list = []
    for q in q_data_list:
        eval_raw = q.get("evaluation")
        eval_schema = InterviewEvaluationResponse(**eval_raw) if eval_raw else None
        review_list.append(
            InterviewQuestionSchema(
                question_index=q.get("question_index", 0),
                category=q.get("category", "Technical"),
                difficulty=q.get("difficulty", session.difficulty),
                question_text=q.get("question_text", ""),
                context_tip=q.get("context_tip"),
                user_answer=q.get("user_answer"),
                score=q.get("score"),
                evaluation=eval_schema
            )
        )

    cat_scores = session.category_scores or {}

    report = InterviewFinalReportResponse(
        session_id=session.id,
        target_role=session.target_role,
        mode=session.mode,
        difficulty=session.difficulty,
        overall_score=session.overall_score,
        technical_score=cat_scores.get("technical", session.overall_score),
        communication_score=cat_scores.get("communication", session.overall_score),
        problem_solving_score=cat_scores.get("problem_solving", session.overall_score),
        behavioral_score=cat_scores.get("behavioral", session.overall_score),
        resume_knowledge_score=cat_scores.get("resume_knowledge", session.overall_score),
        readiness_status=session.readiness_status,
        readiness_explanation=session.readiness_explanation or "Evaluation complete.",
        strong_areas=["Core Technical Concepts"] if session.overall_score >= 70 else ["Basic concepts"],
        weak_areas=session.weak_areas or [],
        recommended_roadmap_topics=[f"Review topics in {session.target_role} roadmap"],
        questions_review=review_list
    )

    return APIResponse(
        success=True,
        message="Interview results retrieved",
        data=report
    )


@router.get(
    "/readiness",
    response_model=APIResponse[InterviewReadinessResponse],
    summary="Get overall aggregate interview readiness across completed sessions"
)
async def get_interview_readiness(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(InterviewSession).where(InterviewSession.user_id == user_id, InterviewSession.is_completed == True)
    res = await db.execute(stmt)
    completed_sessions = res.scalars().all()

    if not completed_sessions:
        return APIResponse(
            success=True,
            message="No completed interviews found",
            data=InterviewReadinessResponse(
                overall_readiness_status="NEEDS PRACTICE",
                average_score=0,
                total_interviews_completed=0,
                strongest_mode="Mixed",
                weakest_topic=None,
                recommendation="Start your first AI mock interview to evaluate your technical and behavioral readiness."
            )
        )

    total_count = len(completed_sessions)
    avg_score = int(round(sum(s.overall_score for s in completed_sessions) / total_count))

    if avg_score >= 85:
        status = "EXCELLENT"
        rec = "You have high interview readiness. Keep practicing difficult scenario questions before live interviews."
    elif avg_score >= 75:
        status = "READY"
        rec = "You are interview ready. Practice company-specific STAR behavioral answers to boost scores."
    elif avg_score >= 60:
        status = "NEARLY READY"
        rec = "You have good foundation. Focus on technical architecture trade-offs and detailed project explanations."
    else:
        status = "NEEDS PRACTICE"
        rec = "Focus on foundational roadmap topics and complete beginner/intermediate mock sessions."

    resp = InterviewReadinessResponse(
        overall_readiness_status=status,
        average_score=avg_score,
        total_interviews_completed=total_count,
        strongest_mode=completed_sessions[0].mode,
        weakest_topic=completed_sessions[0].weak_areas[0] if completed_sessions[0].weak_areas else None,
        recommendation=rec
    )

    return APIResponse(
        success=True,
        message="Interview readiness retrieved",
        data=resp
    )
