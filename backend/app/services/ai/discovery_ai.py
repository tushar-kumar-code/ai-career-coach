import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.ai.client import AIService
from app.services.ai.prompts import CAREER_DISCOVERY_SYSTEM_PROMPT
from app.schemas.assessment import (
    CareerDiscoveryAIAnalysis,
    CareerMatchSchema,
    SupportedStrengthSchema
)
from app.models.career_catalog import CareerRole
from app.core.config import settings

logger = logging.getLogger(__name__)


class CareerDiscoveryAIService:
    def __init__(self, provider=None):
        self.provider = provider or AIService.get_provider()

    async def analyze_assessment(
        self,
        db: AsyncSession,
        answers_dict: Dict[str, Any]
    ) -> CareerDiscoveryAIAnalysis:
        """
        Analyzes dimension answers against the career catalog using Groq Llama-3.3-70B model.
        Returns validated Pydantic CareerDiscoveryAIAnalysis.
        """
        # Fetch catalog career roles
        stmt = select(CareerRole)
        res = await db.execute(stmt)
        roles = res.scalars().all()
        roles_catalog_str = "\n".join([
            f"- {r.title} (Slug: {r.slug}): {r.description}. Skills: {', '.join(r.required_skills)}. Strengths: {', '.join(r.preferred_strengths)}"
            for r in roles
        ])

        # Format user answers
        user_answers_formatted = []
        archetype_tally: Dict[str, int] = {}
        role_weight_tally: Dict[str, int] = {}

        for q_id, ans in answers_dict.items():
            text = ans.get("option_text", "")
            dim = ans.get("dimension", "")
            arch = ans.get("archetype", "")
            weights = ans.get("weights", {})
            user_answers_formatted.append(f"Dimension [{dim}]: Selected '{text}'")

            if arch:
                archetype_tally[arch] = archetype_tally.get(arch, 0) + 1
            for r_name, score in weights.items():
                if isinstance(score, int):
                    role_weight_tally[r_name] = role_weight_tally.get(r_name, 0) + score

        answers_summary = "\n".join(user_answers_formatted)

        prompt = f"""
Available Target Career Catalog Roles:
{roles_catalog_str}

User Assessment Responses:
{answers_summary}

Task:
Evaluate the user's natural strengths, analytical ability, problem solving, work style preferences, and technology interests.
Match the user against the catalog of roles.
Never tell the user 'You MUST become X'. Instead state 'X appears to be your strongest match based on your responses'.

Return a structured JSON evaluation matching:
- primary_archetype (e.g. Systems Builder, Data Investigator, Creative Visualizer, AI Pioneer, User Strategist)
- top_strengths (array of objects with strength_name and evidence_reason)
- interest_profile (array of strings)
- work_style_summary (string)
- motivation_profile (string)
- recommended_careers (array of objects matching exact slugs from catalog: slug, title, match_percentage, confidence_percentage, why_recommended, supporting_strengths, potential_challenges, learning_gaps)
- alternative_careers (array of strings)
"""

        # If Groq API Key is configured, execute Groq 70B structured generation
        if settings.GROQ_API_KEY:
            try:
                analysis = await self.provider.generate_structured(
                    prompt=prompt,
                    output_schema=CareerDiscoveryAIAnalysis,
                    system_instruction=CAREER_DISCOVERY_SYSTEM_PROMPT
                )
                return analysis
            except Exception as e:
                logger.error(f"Groq API structured call failed: {str(e)}. Falling back to deterministic rule analysis.")

        # Fallback when API key is unconfigured or call fails
        return self._generate_deterministic_analysis(roles, archetype_tally, role_weight_tally, answers_summary)

    def _generate_deterministic_analysis(
        self,
        roles: List[CareerRole],
        archetype_tally: Dict[str, int],
        role_weight_tally: Dict[str, int],
        answers_summary: str
    ) -> CareerDiscoveryAIAnalysis:
        # Determine dominant archetype
        primary_arch = max(archetype_tally, key=archetype_tally.get) if archetype_tally else "Systems Builder"

        # Calculate scores for catalog roles based on role_weight_tally
        ranked_roles = []
        max_possible_score = max(role_weight_tally.values()) if role_weight_tally else 50
        max_possible_score = max(max_possible_score, 1)

        for role in roles:
            raw_score = role_weight_tally.get(role.title, 0)
            normalized_pct = min(96, max(60, int((raw_score / max_possible_score) * 36 + 60)))
            ranked_roles.append((role, normalized_pct))

        ranked_roles.sort(key=lambda x: x[1], reverse=True)

        recommended_matches = []
        for role, pct in ranked_roles[:4]:
            match_obj = CareerMatchSchema(
                slug=role.slug,
                title=role.title,
                match_percentage=pct,
                confidence_percentage=min(92, pct - 5),
                why_recommended=[
                    f"Strong alignment with {role.preferred_strengths[0] if role.preferred_strengths else 'problem solving'}.",
                    f"High interest signals in {role.interest_areas[0] if role.interest_areas else 'technology'}.",
                    f"Preferred work style matches '{role.work_style}'."
                ],
                supporting_strengths=role.preferred_strengths[:2],
                potential_challenges=[
                    f"Requires mastering {role.required_skills[-1] if role.required_skills else 'advanced tools'}.",
                    "Requires ongoing continuous learning as ecosystem evolves."
                ],
                learning_gaps=role.learning_areas[:2]
            )
            recommended_matches.append(match_obj)

        alternatives = [r.title for r, _ in ranked_roles[4:7]]

        return CareerDiscoveryAIAnalysis(
            primary_archetype=primary_arch,
            top_strengths=[
                SupportedStrengthSchema(
                    strength_name="Problem Solving & Logical Reasoning",
                    evidence_reason="Selected structured analytical problem-solving choices in scenario questions."
                ),
                SupportedStrengthSchema(
                    strength_name="Systems Thinking",
                    evidence_reason="Demonstrated clear preference for root-cause investigation and structural logic."
                )
            ],
            interest_profile=["Software Architecture", "Database Systems", "Automation Tools"],
            work_style_summary="Demonstrates high autonomy, strong analytical focus, and effective collaborative communication when defining requirements.",
            motivation_profile="Motivated by building tangible, scalable technical solutions and mastering high-impact skills.",
            recommended_careers=recommended_matches,
            alternative_careers=alternatives
        )
