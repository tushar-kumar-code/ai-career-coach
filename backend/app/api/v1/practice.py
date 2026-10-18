import logging
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.health import APIResponse
from app.models.profile import UserProfile
from app.models.skill import Skill
from app.models.roadmap import Roadmap
from app.services.ai.client import AIService
from app.services.roadmap.level_test_engine import LevelTestEngine
from app.schemas.roadmap import (
    LevelTestQuestion,
    LevelTestResponse,
    LevelTestSubmitRequest,
    LevelTestSubmitResponse
)
from app.services.firestore.roadmap_repo import RoadmapRepository

router = APIRouter()
logger = logging.getLogger(__name__)
level_test_engine = LevelTestEngine()


# Schemas for Skill Practice Engine
class PracticeContextLevelSummary(BaseModel):
    phase_id: str
    phase_number: int
    level_name: str
    level_theme: str
    level_icon: str
    is_unlocked: bool
    test_passed: bool
    test_score: Optional[int] = None
    stars: int = 0
    xp_reward: int = 100


class PracticeContextResponse(BaseModel):
    target_role: str
    profile_skills: List[str]
    missing_skills: List[str]
    current_level_number: int
    current_level_name: str
    current_level_theme: str
    current_phase_id: str
    current_level_unlocked: bool
    current_test_passed: bool
    current_test_score: Optional[int] = None
    next_level_name: Optional[str] = None
    all_levels: List[PracticeContextLevelSummary]
    recommended_topics: List[Dict[str, str]]


class DrillGenerateRequest(BaseModel):
    topic: str
    difficulty: Optional[str] = "Intermediate"
    question_count: Optional[int] = 3


class InteractiveQuestion(BaseModel):
    id: str
    topic: str
    question: str
    code_snippet: Optional[str] = None
    difficulty: str = "Intermediate"
    question_type: str = "conceptual"
    options: List[str]
    correct_answer: str
    explanation: str


class _AIDrillContainer(BaseModel):
    questions: List[InteractiveQuestion]


class DrillEvaluateRequest(BaseModel):
    question_id: str
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: str
    user_answer: str


class DrillEvaluateResponse(BaseModel):
    question_id: str
    is_correct: bool
    score: int
    user_answer: str
    correct_answer: str
    explanation: str
    feedback: str
    key_takeaway: str


@router.get(
    "/context",
    response_model=APIResponse[PracticeContextResponse],
    summary="Get personalized practice context based on user profile and roadmap levels"
)
async def get_practice_context(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # 1. Fetch user profile
    p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    p_res = await db.execute(p_stmt)
    prof = p_res.scalars().first()
    target_role = prof.target_career if prof and prof.target_career else "Software Developer"

    # 2. Fetch profile skills
    s_stmt = select(Skill).where(Skill.user_id == user_id)
    s_res = await db.execute(s_stmt)
    user_skills = s_res.scalars().all()
    profile_skill_names = [s.skill_name for s in user_skills if s.skill_name]

    # 3. Target role missing skills (Skill Gaps)
    missing_skills = []
    if prof and prof.skills_matrix and isinstance(prof.skills_matrix, dict):
        missing_skills = prof.skills_matrix.get("skill_gaps", [])
    if not missing_skills:
        core_role_reqs = ["OOP", "Data Structures", "Git", "Problem Solving", "Systems Thinking"]
        missing_skills = [s for s in core_role_reqs if s.lower() not in [ps.lower() for ps in profile_skill_names]]

    # 4. Fetch active roadmap and levels
    r_stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
    r_res = await db.execute(r_stmt)
    roadmap = r_res.scalars().first()

    phases = roadmap.phases or [] if roadmap else []
    levels_summary: List[PracticeContextLevelSummary] = []

    current_phase_id = "phase-1"
    current_level_num = 1
    current_level_name = "Spawn Point"
    current_level_theme = "Foundations & Environment Setup"
    current_unlocked = True
    current_passed = False
    current_score = None
    next_level_name = None

    prev_passed = True
    found_active = False

    for idx, p in enumerate(phases):
        p_num = p.get("phase_number", idx + 1)
        pid = p.get("id") or p.get("phase_id") or f"phase-{p_num}"
        lvl_info = level_test_engine.get_level_info(p_num)

        test_passed = bool(p.get("test_passed", False))
        is_unlocked = True if idx == 0 else (prev_passed or bool(p.get("is_unlocked", False)))
        score = p.get("test_score")
        stars = p.get("stars") or (3 if score and score >= 95 else 2 if score and score >= 80 else 1 if score and score >= 70 else 0)

        levels_summary.append(PracticeContextLevelSummary(
            phase_id=pid,
            phase_number=p_num,
            level_name=lvl_info["level_name"],
            level_theme=lvl_info["level_theme"],
            level_icon=lvl_info["level_icon"],
            is_unlocked=is_unlocked,
            test_passed=test_passed,
            test_score=score,
            stars=stars,
            xp_reward=p.get("xp_reward") or 100
        ))

        if is_unlocked and not test_passed and not found_active:
            current_phase_id = pid
            current_level_num = p_num
            current_level_name = lvl_info["level_name"]
            current_level_theme = lvl_info["level_theme"]
            current_unlocked = is_unlocked
            current_passed = test_passed
            current_score = score
            if idx + 1 < len(phases):
                next_lvl_info = level_test_engine.get_level_info(p_num + 1)
                next_level_name = next_lvl_info["level_name"]
            found_active = True

        prev_passed = test_passed

    if not found_active and levels_summary:
        last = levels_summary[-1]
        current_phase_id = last.phase_id
        current_level_num = last.phase_number
        current_level_name = last.level_name
        current_level_theme = last.level_theme
        current_unlocked = last.is_unlocked
        current_passed = last.test_passed
        current_score = last.test_score

    # 5. Build personalized recommended practice topics
    recommended_topics = []
    if missing_skills:
        for ms in missing_skills[:3]:
            recommended_topics.append({
                "topic": ms,
                "reason": f"Core required prerequisite for {target_role} currently missing from your profile evidence.",
                "type": "Skill Gap Drill",
                "priority": "High"
            })
    for ps in profile_skill_names[:3]:
        recommended_topics.append({
            "topic": ps,
            "reason": f"Strengthen and verify your {ps} mastery with interactive code analysis drills.",
            "type": "Profile Skill Drill",
            "priority": "Medium"
        })

    return APIResponse(
        success=True,
        message="Practice context retrieved successfully",
        data=PracticeContextResponse(
            target_role=target_role,
            profile_skills=profile_skill_names,
            missing_skills=missing_skills,
            current_level_number=current_level_num,
            current_level_name=current_level_name,
            current_level_theme=current_level_theme,
            current_phase_id=current_phase_id,
            current_level_unlocked=current_unlocked,
            current_test_passed=current_passed,
            current_test_score=current_score,
            next_level_name=next_level_name,
            all_levels=levels_summary,
            recommended_topics=recommended_topics
        )
    )


@router.post(
    "/drill/generate",
    response_model=APIResponse[List[InteractiveQuestion]],
    summary="Generate interactive Groq AI practice questions tailored to user profile and topic"
)
async def generate_drill_questions(
    req: DrillGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # Fetch target role from profile
    p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
    p_res = await db.execute(p_stmt)
    prof = p_res.scalars().first()
    target_role = prof.target_career if prof and prof.target_career else "Software Developer"

    q_count = max(1, min(req.question_count or 3, 5))
    difficulty = req.difficulty or "Intermediate"

    prompt = f"""
You are an expert Senior Technical Examiner creating an interactive {q_count}-question Skill Drill for '{target_role}'.
Topic: '{req.topic}'
Difficulty: '{difficulty}'

REQUIREMENTS:
1. Generate exactly {q_count} multiple-choice interactive questions.
2. For at least 1 question, provide an explicit, realistic `code_snippet` (Python, JavaScript, SQL, C++, or C snippet) testing code output, edge cases, or debugging.
3. Every question MUST have 4 distinct choices in `options`, each clearly prefixed with 'A) ', 'B) ', 'C) ', 'D) '.
4. `correct_answer` MUST strictly match one of the exact strings from `options`.
5. Provide a clear, educational `explanation` explaining the engineering principle and why this choice is correct.
6. Ensure total accuracy: No false answers or ambiguities.
"""

    questions: List[InteractiveQuestion] = []
    try:
        ai_provider = AIService.get_provider()
        res = await ai_provider.generate_structured(
            prompt=prompt,
            output_schema=_AIDrillContainer,
            system_instruction="You are a Principal Software Engineer and Technical Educator. Generate rigorous, precise multiple-choice questions matching the schema."
        )
        if res and res.questions:
            for q in res.questions:
                options = [opt.strip() for opt in q.options]
                corr = q.correct_answer.strip()
                if corr not in options and len(options) > 0:
                    for opt in options:
                        if corr.startswith(opt[:3]):
                            corr = opt
                            break
                    else:
                        corr = options[0]

                questions.append(InteractiveQuestion(
                    id=q.id or f"drill_{uuid.uuid4().hex[:6]}",
                    topic=req.topic,
                    question=q.question,
                    code_snippet=q.code_snippet,
                    difficulty=difficulty,
                    question_type=q.question_type or "conceptual",
                    options=options,
                    correct_answer=corr,
                    explanation=q.explanation
                ))
    except Exception as e:
        logger.warning(f"Groq AI drill generation warning, creating robust fallback: {e}")

    # Fallback if AI response was empty
    if not questions:
        questions = [
            InteractiveQuestion(
                id=f"drill_{uuid.uuid4().hex[:6]}",
                topic=req.topic,
                question=f"Which of the following is the most effective engineering practice when working with {req.topic} in {target_role}?",
                code_snippet=None,
                difficulty=difficulty,
                question_type="best_practice",
                options=[
                    f"A) Implement modular design with clear boundaries, error handling, and unit test coverage.",
                    f"B) Avoid writing tests to maximize initial velocity and ignore edge conditions.",
                    f"C) Use global state across components to simplify variable passing.",
                    f"D) Suppress runtime exceptions silently to prevent the program from stopping."
                ],
                correct_answer=f"A) Implement modular design with clear boundaries, error handling, and unit test coverage.",
                explanation=f"Clean architecture dictates modularity, explicit error handling, and robust testing when developing production software in {req.topic}."
            ),
            InteractiveQuestion(
                id=f"drill_{uuid.uuid4().hex[:6]}",
                topic=req.topic,
                question=f"What is the time complexity or performance characteristic typically associated with optimal {req.topic} lookup operations?",
                code_snippet=None,
                difficulty=difficulty,
                question_type="conceptual",
                options=[
                    "A) O(1) average-time complexity using hashed indexing or direct key access.",
                    "B) O(N!) factorial complexity in standard operations.",
                    "C) O(2^N) exponential time for basic reads.",
                    "D) O(N^3) cubic overhead per access."
                ],
                correct_answer="A) O(1) average-time complexity using hashed indexing or direct key access.",
                explanation="Standard hash-based lookup patterns achieve O(1) average constant-time complexity for key queries."
            ),
            InteractiveQuestion(
                id=f"drill_{uuid.uuid4().hex[:6]}",
                topic=req.topic,
                question=f"Consider the following code snippet. What is the expected behavior?",
                code_snippet=f"# {req.topic} logic test\ndef evaluate(items):\n    return [x * 2 for x in items if x > 0]\n\nprint(evaluate([-1, 0, 2, 4]))",
                difficulty=difficulty,
                question_type="code_analysis",
                options=[
                    "A) [4, 8]",
                    "B) [-2, 0, 4, 8]",
                    "C) [0, 4, 8]",
                    "D) TypeError: invalid condition"
                ],
                correct_answer="A) [4, 8]",
                explanation="The list comprehension filters only positive elements (x > 0), so -1 and 0 are excluded, yielding [2*2, 4*2] = [4, 8]."
            )
        ]

    return APIResponse(
        success=True,
        message=f"Interactive Groq AI drill questions for '{req.topic}' generated successfully",
        data=questions[:q_count]
    )


@router.post(
    "/drill/evaluate",
    response_model=APIResponse[DrillEvaluateResponse],
    summary="Evaluate an interactive question answer with ground truth precision"
)
async def evaluate_drill_question(
    req: DrillEvaluateRequest
):
    user_ans = (req.user_answer or "").strip()
    correct_ans = (req.correct_answer or "").strip()

    is_correct = False
    if user_ans and correct_ans:
        u_clean = user_ans.strip().lower()
        c_clean = correct_ans.strip().lower()
        if u_clean == c_clean:
            is_correct = True
        elif len(user_ans.strip()) <= 3 and user_ans.strip()[0].upper() == correct_ans.strip()[0].upper():
            is_correct = True
        elif correct_ans.startswith(user_ans.strip()):
            is_correct = True
        elif user_ans.startswith(correct_ans[:3]):
            is_correct = True

    score = 100 if is_correct else 0

    if is_correct:
        feedback = f"Sahi Jawab! 🎉 Excellent work. Your selection '{user_ans}' is completely correct."
        takeaway = f"Key Insight: {req.explanation}"
    else:
        feedback = (
            f"Galat Jawab! ❌ The correct choice is '{correct_ans}'. "
            f"Review the engineering reasoning below to avoid this mistake in actual interviews."
        )
        takeaway = f"Learning Focus: {req.explanation}"

    return APIResponse(
        success=True,
        message="Question evaluated successfully",
        data=DrillEvaluateResponse(
            question_id=req.question_id,
            is_correct=is_correct,
            score=score,
            user_answer=user_ans,
            correct_answer=correct_ans,
            explanation=req.explanation,
            feedback=feedback,
            key_takeaway=takeaway
        )
    )
