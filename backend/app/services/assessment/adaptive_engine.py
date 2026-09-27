import logging
import uuid
import random
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.question import Question
from app.services.ai.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GeneratedOption(BaseModel):
    id: str = Field(description="Option ID: A, B, C, or D")
    text: str = Field(description="Clear, easy-to-understand option text in plain simple language")
    archetype: str = Field(description="Archetype: Systems Builder, Data Investigator, Creative Visualizer, Cloud Architect, User Strategist, AI Pioneer")
    target_role: str = Field(description="Target role associated with option, e.g. Frontend Developer, Backend Developer, Data Scientist, Product Manager")


class GeneratedQuestion(BaseModel):
    dimension: str = Field(description="Dimension or topic area for this question")
    question_text: str = Field(description="Very easy, clear, relatable question written in everyday language. No jargon. Any student can read and answer this.")
    options: List[GeneratedOption] = Field(description="Array of 4 options A, B, C, D")


LEVEL_CONTEXT = {
    "beginner": (
        "The candidate is a BEGINNER — they may be a student or someone just starting to explore technology careers. "
        "Use extremely simple, everyday language. No technical jargon. Relate questions to everyday life, hobbies, or curiosity. "
        "Example: Instead of 'REST API design', ask 'Do you enjoy figuring out how apps talk to each other, like how Instagram shows you photos?'"
    ),
    "intermediate": (
        "The candidate has INTERMEDIATE experience — they have some coding knowledge or work in tech. "
        "Use clear but slightly technical language. Ask about preferences in tools, approaches, or project types they may have used."
    ),
    "advanced": (
        "The candidate is ADVANCED — a working professional or experienced developer. "
        "You may use industry terminology. Ask deeper questions about architecture choices, tradeoffs, leadership, or specialization."
    )
}


class AdaptiveAssessmentEngine:
    """
    Intelligent Adaptive Assessment Engine.
    Dynamically generates or adaptively selects the NEXT question based on
    the user's previous answer and experience level.
    Ensures questions are easy, clear, non-repetitive, and persona-tailored.
    """

    MAX_QUESTIONS_PER_SESSION = 8

    async def get_next_question(
        self,
        db: AsyncSession,
        answered_question_ids: List[str],
        current_answers: Dict[str, Any],
        language: str = "en",
        ai_provider: Optional[BaseLLMProvider] = None,
        user_level: str = "beginner"
    ) -> Optional[Question]:
        step_num = len(answered_question_ids) + 1

        # End assessment session after MAX_QUESTIONS_PER_SESSION
        if step_num > self.MAX_QUESTIONS_PER_SESSION:
            return None

        # Try dynamic AI question generation first if AI provider is active
        if ai_provider:
            try:
                ai_q = await self._generate_ai_adaptive_question(
                    db=db,
                    step_num=step_num,
                    answered_question_ids=answered_question_ids,
                    current_answers=current_answers,
                    language=language,
                    ai_provider=ai_provider,
                    user_level=user_level
                )
                if ai_q:
                    return ai_q
            except Exception as e:
                logger.warning(f"Dynamic AI question generation fallback: {str(e)}")

        # Fallback: Smart adaptive selection from seeded database questions
        return await self._select_adaptive_fallback_question(
            db=db,
            answered_ids=answered_question_ids,
            current_answers=current_answers,
            step_num=step_num
        )

    async def _generate_ai_adaptive_question(
        self,
        db: AsyncSession,
        step_num: int,
        answered_question_ids: List[str],
        current_answers: Dict[str, Any],
        language: str,
        ai_provider: BaseLLMProvider,
        user_level: str = "beginner"
    ) -> Optional[Question]:
        # Format user's previous answers history for context
        answers_history = []
        last_answer_summary = "None (First Question)"

        for q_id, ans in current_answers.items():
            dim = ans.get("dimension", "")
            selected_text = ans.get("option_text", "")
            arch = ans.get("archetype", "")
            is_custom = ans.get("option_id") == "custom"
            label = "(own answer)" if is_custom else f"(Archetype: {arch})"
            answers_history.append(f"- Step {len(answers_history)+1} [{dim}]: Selected '{selected_text}' {label}")

        if answers_history:
            last_answer_summary = answers_history[-1]

        history_str = "\n".join(answers_history) if answers_history else "No previous answers yet (Starting new session)."

        level_instruction = LEVEL_CONTEXT.get(user_level, LEVEL_CONTEXT["beginner"])

        is_hi = language == "hi"
        lang_rule = ""
        if is_hi:
            lang_rule = "\nIMPORTANT LANGUAGE REQUIREMENT: Write the question_text, dimension name, and all option texts in clear, friendly, encouraging Hindi!"

        prompt = f"""
You are creating Question #{step_num} of {self.MAX_QUESTIONS_PER_SESSION} for an adaptive career discovery assessment.

CANDIDATE LEVEL CONTEXT:
{level_instruction}

Candidate Previous Answers History:
{history_str}

Last Selected Answer Context:
{last_answer_summary}

TASK & GUIDELINES:
1. **Easy & Clear Language**: Write a simple, engaging, practical multiple-choice question based on the candidate's level above.
   - For BEGINNER: Use relatable everyday analogies. No jargon at all.
   - For INTERMEDIATE: Use simple tech language they would recognize.
   - For ADVANCED: You may use technical terms and ask about tradeoffs.
2. **Adaptive Context**: The question MUST adaptively build upon the user's previous answer:
   - If the user previously chose Backend/Systems/Logs, ask a clear follow-up exploring databases, APIs, or system reliability.
   - If the user previously chose Frontend/UI/Design, ask a clear follow-up exploring visual layouts, user interactions, or web components.
   - If the user previously chose Data/Analytics, ask a clear follow-up exploring data charts, trends, or insights.
   - If the user gave a CUSTOM answer, interpret what they wrote and build a follow-up question from that context.
   - If this is Question #1, create a welcoming, easy question exploring what kind of project or activity excites them most in technology.
3. Provide 4 distinct options (A, B, C, D) each mapping to a different career archetype.
4. Make options short, concrete, and easy to pick between — not vague or overlapping.
{lang_rule}
"""

        system_instruction = "You are an expert AI Career Coach generating adaptive, easy, and engaging career discovery assessment questions tailored to the user's experience level."

        generated: GeneratedQuestion = await ai_provider.generate_structured(
            prompt=prompt,
            output_schema=GeneratedQuestion,
            system_instruction=system_instruction
        )

        if not generated or not generated.options or len(generated.options) < 4:
            return None

        formatted_options = [
            {
                "id": opt.id,
                "text": opt.text,
                "archetype": opt.archetype,
                "weights": {opt.target_role: 9, opt.archetype: 8}
            }
            for opt in generated.options
        ]

        new_q = Question(
            id=str(uuid.uuid4()),
            dimension=generated.dimension,
            question_type="adaptive_ai",
            question_text=generated.question_text,
            options=formatted_options,
            difficulty_level=1,
            order_index=step_num
        )

        db.add(new_q)
        await db.commit()
        await db.refresh(new_q)
        return new_q

    async def _select_adaptive_fallback_question(
        self,
        db: AsyncSession,
        answered_ids: List[str],
        current_answers: Dict[str, Any],
        step_num: int
    ) -> Optional[Question]:
        stmt = select(Question)
        result = await db.execute(stmt)
        all_questions = result.scalars().all()

        unanswered = [q for q in all_questions if q.id not in answered_ids]
        if not unanswered:
            return None

        # Randomize selection among unanswered questions so retakes/refreshes never repeat static sequences
        # Prioritize matching archetype if available
        archetype_tally: Dict[str, int] = {}
        for q_id, ans in current_answers.items():
            arch = ans.get("archetype")
            if arch:
                archetype_tally[arch] = archetype_tally.get(arch, 0) + 1

        if archetype_tally:
            leading_arch = max(archetype_tally, key=archetype_tally.get)
            matching_q = [
                q for q in unanswered 
                if any(opt.get("archetype") == leading_arch for opt in q.options if isinstance(opt, dict))
            ]
            if matching_q:
                return random.choice(matching_q)

        # Default fallback: pick a random unanswered question
        return random.choice(unanswered)

    def calculate_raw_scores(self, answers_dict: Dict[str, Any]) -> Dict[str, int]:
        """Calculates raw role weights accumulated from selected options."""
        role_scores: Dict[str, int] = {}
        for q_id, ans in answers_dict.items():
            weights = ans.get("weights", {})
            for role_key, val in weights.items():
                if isinstance(val, int):
                    role_scores[role_key] = role_scores.get(role_key, 0) + val
        return role_scores
