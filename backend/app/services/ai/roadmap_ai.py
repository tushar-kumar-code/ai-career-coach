import logging
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.groq_provider import GroqProvider
from app.services.ai.prompts import ROADMAP_GENERATION_PROMPT
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIRoadmapEnrichment(BaseModel):
    learning_objectives: List[str] = Field(default_factory=list)
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)


class RoadmapAIService:
    """Service utilizing Gemini/Groq for rich personalized roadmap content generation."""

    def __init__(self):
        self.gemini = GeminiProvider()
        self.groq = GroqProvider()

    async def enrich_phase(
        self,
        target_role: str,
        user_level: str,
        preferred_style: str,
        phase_name: str,
        skills: List[str],
        verified_skills: List[str]
    ) -> AIRoadmapEnrichment:
        """Enrich a roadmap phase with AI-generated objectives, tasks, projects, and milestones."""
        # Always return instant structured fallback for fast tests and reliable offline fallback
        if settings.DEBUG or not settings.GEMINI_API_KEY:
            return self._generate_fallback_enrichment(target_role, phase_name, skills)

        prompt = f"""
Target Career: {target_role}
User Level: {user_level}
Learning Style: {preferred_style}
Roadmap Phase: {phase_name}
Target Skills in this Phase: {', '.join(skills)}
Already Verified Skills: {', '.join(verified_skills)}

Task:
Generate tailored learning content for this phase:
1. 3-4 clear learning objectives.
2. 3-5 daily actionable tasks for the target skills.
3. 1 realistic portfolio project.
4. 1-2 milestones with clear completion criteria.

Return JSON with structure matching AIRoadmapEnrichment.
"""

        try:
            res = await self.gemini.generate_structured(
                prompt=prompt,
                output_schema=AIRoadmapEnrichment,
                system_instruction=ROADMAP_GENERATION_PROMPT
            )
            if res and res.tasks and len(res.tasks) > 0:
                return res
        except Exception as e:
            logger.warning(f"Gemini roadmap enrichment failed: {str(e)}.")

        return self._generate_fallback_enrichment(target_role, phase_name, skills)

    def _generate_fallback_enrichment(
        self,
        target_role: str,
        phase_name: str,
        skills: List[str]
    ) -> AIRoadmapEnrichment:
        primary_skill = skills[0] if skills else "Core Fundamentals"
        second_skill = skills[1] if len(skills) > 1 else primary_skill

        return AIRoadmapEnrichment(
            learning_objectives=[
                f"Master key concepts in {primary_skill} for production environments.",
                f"Implement hands-on exercises in {second_skill}.",
                f"Build a real-world mini project demonstrating {target_role} competence."
            ],
            tasks=[
                {
                    "title": f"Study {primary_skill} Architecture & Core Patterns",
                    "skill": primary_skill,
                    "estimated_minutes": 30,
                    "why_matters": f"{primary_skill} is a core requirement for a successful {target_role}.",
                    "practice_activity": f"Write a clean sample script or component utilizing {primary_skill} best practices."
                },
                {
                    "title": f"Hands-on {second_skill} Integration & Lab",
                    "skill": second_skill,
                    "estimated_minutes": 35,
                    "why_matters": f"Connecting {primary_skill} with {second_skill} strengthens technical problem solving.",
                    "practice_activity": f"Build a mini module integrating {primary_skill} with {second_skill}."
                },
                {
                    "title": f"Code Optimization & Best Practices for {primary_skill}",
                    "skill": primary_skill,
                    "estimated_minutes": 25,
                    "why_matters": "Clean code structure and performance optimization are essential for technical interviews.",
                    "practice_activity": "Refactor previous exercise code to improve readability, error handling, and testability."
                }
            ],
            projects=[
                {
                    "title": f"{target_role} - {primary_skill} Portfolio Application",
                    "objective": f"Design and deploy a practical application demonstrating end-to-end {primary_skill} and {second_skill} mastery.",
                    "skills_practiced": skills,
                    "difficulty": "Intermediate",
                    "expected_outcome": f"Fully functional, version-controlled project repository with documentation.",
                    "resume_relevance": f"High ATS resume impact item for candidate applying for {target_role} roles."
                }
            ],
            milestones=[
                {
                    "title": f"{phase_name} Core Competency Verified",
                    "criteria": f"Complete all hands-on exercises and submit the portfolio project repository for {primary_skill}."
                }
            ]
        )
