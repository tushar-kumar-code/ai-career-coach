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
    # STAR fields — always populated for Behavioral/HR; optional for others
    situation_status: Optional[str] = "Good"   # Good | Needs Clarity | Missing
    task_status: Optional[str] = "Good"
    action_status: Optional[str] = "Good"
    result_status: Optional[str] = "Good"
    situation_feedback: Optional[str] = None
    task_feedback: Optional[str] = None
    action_feedback: Optional[str] = None
    result_feedback: Optional[str] = None
    star_complete: bool = False
    star_score: int = 0
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

        # Build STAR instruction block — inject for Behavioral/HR questions
        is_behavioral = category in ("Behavioral", "HR")
        star_instruction = ""
        if is_behavioral:
            star_instruction = """
STAR Method Evaluation (REQUIRED for Behavioral/HR):
Decompose the candidate's answer into STAR components:
- situation_status: Did they explain the CONTEXT (project, team, problem)? Options: "Good" | "Needs Clarity" | "Missing"
- task_status: Did they explain their SPECIFIC RESPONSIBILITY? Options: "Good" | "Needs Clarity" | "Missing"
- action_status: Did they clearly describe what THEY PERSONALLY DID (not the team)? Options: "Good" | "Needs Clarity" | "Missing"
- result_status: Did they explain the OUTCOME with measurable or qualitative result? Options: "Good" | "Needs Clarity" | "Missing"
- situation_feedback: One sentence of specific, honest feedback on the Situation component (or null if not applicable).
- task_feedback: One sentence on Task component.
- action_feedback: One sentence on Action component.
- result_feedback: One sentence on Result component. If the result is missing, say so clearly without inventing one.
- star_complete: true only if all 4 components are present (Good).
- star_score: Integer 0-100 reflecting STAR completeness quality.

CRITICAL: Do NOT invent results for the candidate. If the Result is missing, set result_status to "Missing" and 
result_feedback to a concrete suggestion like "Explain what improved after your action — e.g., reduced response time, 
resolved bug, team outcome."
"""
        else:
            star_instruction = """
For non-behavioral questions, set STAR fields to sensible defaults.
situation_status/task_status/action_status/result_status can be "Good" if the answer is coherent, or "Not Applicable".
star_complete: false; star_score: 0.
"""

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

{star_instruction}

Also identify:
- strengths: 1-3 specific things done well (be concrete, not generic)
- weaknesses: 1-3 specific gaps (be honest)
- missing_points: important concepts that should have been mentioned
- suggested_improvement: one actionable, specific sentence to improve the answer
- ideal_answer_outline: 3 bullet points of what a great answer would cover
- detected_weak_topic: if the answer reveals a weak knowledge area, name it (e.g., "SQL Joins", "STAR Result"); else null.

Return structured JSON adhering to the schema.
"""

        try:
            res = await self.ai.generate_structured(
                prompt=prompt,
                output_schema=AIAnswerEvaluationSchema,
                system_instruction="You are a senior hiring manager evaluating a candidate's interview answer."
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
        is_behavioral = category in ("Behavioral", "HR")
        answer_lower = user_answer.lower() if user_answer else ""

        if is_short or word_count < 10:
            score = 45
            tech_s = 40; comm_s = 50; ps_s = 40; beh_s = 50; res_s = 45
            strengths = ["Attempted response"]
            weaknesses = ["Answer was extremely brief and lacked detail", "Did not explain technical rationale"]
            missing_points = ["Specific technical implementation steps", "Concrete metrics or outcomes"]
            improvement = "Elaborate with specific examples, architectural choices, and measurable results."
            detected_weak = "Brief / Unclear Explanations"
        elif word_count > 60:
            score = 88
            tech_s = 85; comm_s = 90; ps_s = 88; beh_s = 85; res_s = 90
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
            tech_s = 75; comm_s = 78; ps_s = 74; beh_s = 75; res_s = 76
            strengths = ["Solid core answer addressing the main question"]
            weaknesses = ["Could provide more technical depth on implementation details"]
            missing_points = ["Detailed architectural trade-offs"]
            improvement = "Add specific technical details or code/framework mechanisms you utilized."
            detected_weak = None

        # STAR component detection — used for Behavioral/HR
        has_situation = any(w in answer_lower for w in ["when", "during", "in my project", "we had", "there was", "client", "problem", "bug", "project"]) or word_count > 25
        has_task = any(w in answer_lower for w in ["goal", "responsible", "needed", "had to", "task", "objective", "assigned", "my role", "i was"]) or word_count > 35
        has_action = any(w in answer_lower for w in ["i built", "i implemented", "i created", "i optimized", "i debugged", "i refactored", "i used", "checked", "wrote", "i decided", "i fixed"]) or word_count > 20
        has_result = any(w in answer_lower for w in ["result", "outcome", "improved", "reduced", "%", "faster", "resolved", "delivered", "success", "learned", "increased"])

        situation_status = "Good" if has_situation else ("Needs Clarity" if word_count > 10 else "Missing")
        task_status = "Good" if has_task else ("Needs Clarity" if word_count > 20 else "Missing")
        action_status = "Good" if has_action else "Missing"
        result_status = "Good" if has_result else "Missing"

        star_complete = all([has_situation, has_task, has_action, has_result])
        star_score = sum([25 if has_situation else 0, 25 if has_task else 0, 25 if has_action else 0, 25 if has_result else 0])

        # Contextual feedback per STAR component
        situation_feedback = (
            "Good — you clearly set the context." if has_situation
            else "Needs clarity: Briefly describe the project or challenge you faced before jumping into the solution."
        )
        task_feedback = (
            "Good — your specific responsibility was clear." if has_task
            else "Needs clarity: State your exact individual role — what were YOU responsible for, vs. the team?"
        )
        action_feedback = (
            "Good — you described what you personally did." if has_action
            else "Missing: Explain what YOU specifically implemented, investigated, or decided (use 'I' statements)."
        )
        result_feedback = (
            "Good — you mentioned an outcome." if has_result
            else "Missing: Explain what changed after your action — e.g., reduced response time, bug resolved, or measurable improvement."
        )

        # If not behavioral, reset STAR to neutral
        if not is_behavioral:
            situation_status = task_status = action_status = result_status = "Not Applicable"
            situation_feedback = task_feedback = action_feedback = result_feedback = None
            star_complete = False
            star_score = 0

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
            "situation_status": situation_status,
            "task_status": task_status,
            "action_status": action_status,
            "result_status": result_status,
            "situation_feedback": situation_feedback,
            "task_feedback": task_feedback,
            "action_feedback": action_feedback,
            "result_feedback": result_feedback,
            "star_complete": star_complete,
            "star_score": star_score,
            "detected_weak_topic": detected_weak
        }
