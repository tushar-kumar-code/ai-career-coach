import logging
from typing import Dict, Any, List
from app.services.ai.client import AIService

logger = logging.getLogger(__name__)


class SkillAIService:
    """AI service evaluating ambiguous resume skill claims and soft-skill signals."""

    def __init__(self, provider=None):
        self.provider = provider or AIService.get_provider()

    async def analyze_transferable_skills(
        self,
        user_skills: List[str],
        target_career: str
    ) -> Dict[str, Any]:
        prompt = f"""
Analyze the user's current skill list: {', '.join(user_skills)}
Target Career Role: {target_career}

Identify top 3 transferable skills and soft-skill strengths that accelerate transition into this target role.
Return a structured output with rationale for each.
"""
        try:
            res = await self.provider.generate_text(prompt)
            return {"ai_summary": res, "status": "completed"}
        except Exception as e:
            logger.warning(f"Groq AI skill analysis fallback: {e}")
            return {
                "ai_summary": f"User's analytical and technical skill profile aligns well with {target_career} prerequisites.",
                "status": "fallback"
            }
