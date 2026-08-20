import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.services.ai.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


class AIAnswerEvaluationSchema(BaseModel):
    score: int = Field(..., ge=0, le=100)
    technical_score: int = Field(..., ge=0, le=100)
    communication_score: int = Field(..., ge=0, le=100)
    problem_solving_score: int = Field(..., ge=0, le=100)
    behavioral_score: int = Field(..., ge=0, le=100)
    resume_knowledge_score: int = Field(..., ge=0, le=100)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_points: List[str] = Field(default_factory=list)
    suggested_improvement: str
    ideal_answer_outline: List[str] = Field(default_factory=list)
    situation_feedback: Optional[str] = None
    task_feedback: Optional[str] = None
    action_feedback: Optional[str] = None
    result_feedback: Optional[str] = None
    star_complete: bool = False
    detected_weak_topic: Optional[str] = None


class InterviewEvaluator:
    """Service evaluating user interview answers using structured multi-category AI analysis & deterministic fallback."""

    def __init__(self):
        self.ai = GeminiProvider()

    async def evaluate_answer(
        self,
        question_text: str,
        category: str,
        difficulty: str,
        user_answer: str,
        target_role: str
    ) -> Dict[str, Any]:
        """Evaluate answer across technical, communication, problem-solving, behavioral, and resume knowledge dimensions."""
        if not user_answer or len(user_answer.strip()) < 5:
            return self._fallback_evaluation(question_text, category, difficulty, user_answer, is_short=True)

        prompt = f"""
You are a senior hiring manager interviewing a candidate for a {target_role} position.
Question: "{question_text}"
Category: {category} | Difficulty: {difficulty}
Candidate Answer: "{user_answer}"

Evaluate the candidate's answer strictly and constructively across sub-scores (0-100):
- technical_score: technical accuracy, domain correctness
- communication_score: clarity, structure, articulation
- problem_solving_score: logical reasoning, approach, trade-offs
- behavioral_score: ownership, collaboration, STAR method
- resume_knowledge_score: project depth, authenticity

Return structured JSON adhering to the schema.
"""

        try:
            res = await self.ai.generate_structured(
                prompt=prompt,
                output_schema=AIAnswerEvaluationSchema,
                system_instruction="You are a senior hiring manager interviewing a candidate."
            )
            return res.model_dump()
        except Exception as err:
            logger.warning(f"AI evaluation failed or debug mode active: {err}. Using deterministic evaluation fallback.")
            return self._fallback_evaluation(question_text, category, difficulty, user_answer)

    def _fallback_evaluation(
        self,
        question_text: str,
        category: str,
        difficulty: str,
        user_answer: str,
        is_short: bool = False
    ) -> Dict[str, Any]:
        """Deterministic evaluation fallback when AI API is unconfigured or response fails."""
        words = user_answer.strip().split() if user_answer else []
        word_count = len(words)

        if is_short or word_count < 10:
            score = 45
            tech_s = 40
            comm_s = 50
            ps_s = 40
            beh_s = 50
            res_s = 45
            strengths = ["Attempted response"]
            weaknesses = ["Answer was extremely brief and lacked detail", "Did not explain technical rationale"]
            missing_points = ["Specific technical implementation steps", "Concrete metrics or outcomes"]
            improvement = "Elaborate with specific examples, architectural choices, and measurable results."
            detected_weak = "Brief / Unclear Explanations"
        elif word_count > 60:
            score = 88
            tech_s = 85
            comm_s = 90
            ps_s = 88
            beh_s = 85
            res_s = 90
            strengths = [
                "Comprehensive explanation with logical structure",
                "Demonstrates practical experience and problem-solving mindset"
            ]
            weaknesses = ["Could be even more concise on background context"]
            missing_points = ["Explicit error edge cases"]
            improvement = "Great answer! To make it exceptional, explicitly state performance trade-offs or edge case handling."
            detected_weak = None
        else:
            score = 75
            tech_s = 75
            comm_s = 78
            ps_s = 74
            beh_s = 75
            res_s = 76
            strengths = ["Solid core answer addressing the main question"]
            weaknesses = ["Could provide more technical depth on implementation details"]
            missing_points = ["Detailed architectural trade-offs"]
            improvement = "Add specific technical details or code/framework mechanisms you utilized."
            detected_weak = None

        return {
            "score": score,
            "technical_score": tech_s,
            "communication_score": comm_s,
            "problem_solving_score": ps_s,
            "behavioral_score": beh_s,
            "resume_knowledge_score": res_s,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_points": missing_points,
            "suggested_improvement": improvement,
            "ideal_answer_outline": [
                "1. State the core concept or situation clearly",
                "2. Explain technical steps, tools, or frameworks applied",
                "3. Conclude with measurable results and trade-offs considered"
            ],
            "situation_feedback": "Context was clear" if word_count > 30 else "Context needed expansion",
            "task_feedback": "Goal identified",
            "action_feedback": "Action steps described",
            "result_feedback": "Outcomes stated",
            "star_complete": word_count > 40,
            "detected_weak_topic": detected_weak
        }
