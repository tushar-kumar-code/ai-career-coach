from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.question import Question


class AdaptiveAssessmentEngine:
    """
    Extensible adaptive selection service.
    Tracks answers, estimates strength signals, and selects the next question.
    """

    async def get_next_question(
        self,
        db: AsyncSession,
        answered_question_ids: List[str],
        current_answers: Dict[str, Any]
    ) -> Optional[Question]:
        # Fetch all questions ordered by order_index
        stmt = select(Question).order_by(Question.order_index)
        result = await db.execute(stmt)
        all_questions = result.scalars().all()

        # Find questions not yet answered by user
        unanswered = [q for q in all_questions if q.id not in answered_question_ids]
        if not unanswered:
            return None

        # Return the next question in the adaptive queue
        return unanswered[0]

    def calculate_raw_scores(self, answers_dict: Dict[str, Any]) -> Dict[str, int]:
        """Calculates raw role weights accumulated from selected options."""
        role_scores: Dict[str, int] = {}
        for q_id, ans in answers_dict.items():
            weights = ans.get("weights", {})
            for role_key, val in weights.items():
                if isinstance(val, int):
                    role_scores[role_key] = role_scores.get(role_key, 0) + val
        return role_scores
