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
        answers_dict: Dict[str, Any],
        language: str = "en"
    ) -> CareerDiscoveryAIAnalysis:
        """
        Analyzes dimension answers against the career catalog using Groq Llama-3.3-70B / Gemini model.
        Returns validated Pydantic CareerDiscoveryAIAnalysis in requested language.
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

        lang_instruction = ""
        if language == "hi":
            lang_instruction = "\nIMPORTANT LANGUAGE REQUIREMENT: The user language preference is Hindi. Write work_style_summary, motivation_profile, evidence_reason, why_recommended, supporting_strengths, potential_challenges, and learning_gaps in clear, professional Hindi while keeping technical career titles and slugs clean."

        prompt = f"""
Available Target Career Catalog Roles:
{roles_catalog_str}

User Assessment Responses:
{answers_summary}

Task:
Evaluate the user's natural strengths, analytical ability, problem solving, work style preferences, and technology interests.
Match the user against the catalog of roles.
Never tell the user 'You MUST become X'. Instead state 'X appears to be your strongest match based on your responses'.
{lang_instruction}

Return a structured JSON evaluation matching:
- primary_archetype (e.g. Systems Builder, Data Investigator, Creative Visualizer, AI Pioneer, User Strategist)
- top_strengths (array of objects with strength_name and evidence_reason)
- interest_profile (array of strings)
- work_style_summary (string)
- motivation_profile (string)
- recommended_careers (array of objects matching exact slugs from catalog: slug, title, match_percentage, confidence_percentage, why_recommended, supporting_strengths, potential_challenges, learning_gaps)
- alternative_careers (array of strings)
"""

        # If Groq/Gemini API Key is configured, execute structured generation
        if settings.GROQ_API_KEY or settings.GEMINI_API_KEY:
            try:
                analysis = await self.provider.generate_structured(
                    prompt=prompt,
                    output_schema=CareerDiscoveryAIAnalysis,
                    system_instruction=CAREER_DISCOVERY_SYSTEM_PROMPT
                )
                return analysis
            except Exception as e:
                logger.error(f"AI API structured call failed: {str(e)}. Falling back to deterministic rule analysis.")

        # Fallback when API key is unconfigured or call fails
        return self._generate_deterministic_analysis(roles, archetype_tally, role_weight_tally, answers_summary, language=language)

    def _generate_deterministic_analysis(
        self,
        roles: List[CareerRole],
        archetype_tally: Dict[str, int],
        role_weight_tally: Dict[str, int],
        answers_summary: str,
        language: str = "en"
    ) -> CareerDiscoveryAIAnalysis:
        is_hi = language == "hi"
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
            why = [
                f"Strong alignment with {role.preferred_strengths[0] if role.preferred_strengths else 'problem solving'}." if not is_hi else f"{role.preferred_strengths[0] if role.preferred_strengths else 'समस्या समाधान'} के साथ मजबूत तालमेल।",
                f"High interest signals in {role.interest_areas[0] if role.interest_areas else 'technology'}." if not is_hi else f"{role.interest_areas[0] if role.interest_areas else 'प्रौद्योगिकी'} में उच्च रुचि के संकेत।",
                f"Preferred work style matches '{role.work_style}'." if not is_hi else f"पसंदीदा कार्यशैली '{role.work_style}' से मेल खाती है।"
            ]
            challenges = [
                f"Requires mastering {role.required_skills[-1] if role.required_skills else 'advanced tools'}." if not is_hi else f"{role.required_skills[-1] if role.required_skills else 'उन्नत उपकरण'} में महारत हासिल करने की आवश्यकता है।",
                "Requires ongoing continuous learning as ecosystem evolves." if not is_hi else "तकनीकी पारिस्थितिकी तंत्र विकसित होने के साथ निरंतर सीखने की आवश्यकता है।"
            ]
            match_obj = CareerMatchSchema(
                slug=role.slug,
                title=role.title,
                match_percentage=pct,
                confidence_percentage=min(92, pct - 5),
                why_recommended=why,
                supporting_strengths=role.preferred_strengths[:2],
                potential_challenges=challenges,
                learning_gaps=role.learning_areas[:2]
            )
            recommended_matches.append(match_obj)

        alternatives = [r.title for r, _ in ranked_roles[4:7]]

        top_strengths_list = [
            SupportedStrengthSchema(
                strength_name="Problem Solving & Logical Reasoning" if not is_hi else "समस्या समाधान और तार्किक तर्क",
                evidence_reason="Selected structured analytical problem-solving choices in scenario questions." if not is_hi else "परिदृश्य आधारित प्रश्नों में विश्लेषणात्मक समस्या समाधान विकल्पों का चयन किया।"
            ),
            SupportedStrengthSchema(
                strength_name="Systems Thinking" if not is_hi else "सिस्टम थिंकिंग (सिस्टम सोच)",
                evidence_reason="Demonstrated clear preference for root-cause investigation and structural logic." if not is_hi else "मूल-कारण जाँच और संरचनात्मक तर्क के लिए स्पष्ट प्राथमिकता का प्रदर्शन किया।"
            )
        ]

        work_style = "Demonstrates high autonomy, strong analytical focus, and effective collaborative communication when defining requirements." if not is_hi else "आप उच्च स्वायत्तता, मजबूत विश्लेषणात्मक ध्यान और आवश्यकताओं को परिभाषित करते समय प्रभावी सहयोगात्मक संचार का प्रदर्शन करते हैं।"
        motivation = "Motivated by building tangible, scalable technical solutions and mastering high-impact skills." if not is_hi else "ठोस, स्केलेबल तकनीकी समाधान बनाने और उच्च-प्रभाव कौशल हासिल करने से प्रेरित।"

        return CareerDiscoveryAIAnalysis(
            primary_archetype=primary_arch,
            top_strengths=top_strengths_list,
            interest_profile=["Software Architecture", "Database Systems", "Automation Tools"],
            work_style_summary=work_style,
            motivation_profile=motivation,
            recommended_careers=recommended_matches,
            alternative_careers=alternatives
        )
