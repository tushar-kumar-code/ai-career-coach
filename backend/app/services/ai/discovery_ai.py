import logging
from typing import Dict, Any, List, Optional
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
        resume_profile: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> CareerDiscoveryAIAnalysis:
        """
        Analyzes dimension answers AND user's resume profile against the career catalog using Groq AI.
        Synthesizes both psychological discovery assessment signals and empirical resume evidence.
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

        # Format user assessment answers
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

        # Format user resume profile (skills, projects, experience, education)
        resume_summary_lines = []
        user_skills_list = []
        if resume_profile and isinstance(resume_profile, dict):
            about = resume_profile.get("about_user") or {}
            headline = about.get("headline") or about.get("summary") or ""
            if headline:
                resume_summary_lines.append(f"Candidate Headline / Objective: {headline}")

            raw_skills = resume_profile.get("skills") or []
            for s in raw_skills:
                s_name = s.get("name") if isinstance(s, dict) else str(s)
                if s_name:
                    user_skills_list.append(s_name)
            if user_skills_list:
                resume_summary_lines.append(f"Verified Resume Skills: {', '.join(user_skills_list[:25])}")

            experiences = resume_profile.get("experience") or []
            for exp in experiences[:3]:
                if isinstance(exp, dict):
                    role_str = f"{exp.get('role', 'Role')} at {exp.get('company', 'Company')}"
                    ach_str = "; ".join(exp.get("key_achievements", [])[:2])
                    resume_summary_lines.append(f"Work Experience: {role_str} ({ach_str})")

            projects = resume_profile.get("projects") or []
            for pr in projects[:3]:
                if isinstance(pr, dict):
                    tech_str = ", ".join(pr.get("technologies", []))
                    resume_summary_lines.append(f"Project: {pr.get('title', 'Project')} (Tech: {tech_str}) - {pr.get('description', '')[:100]}")

            educations = resume_profile.get("education") or []
            for ed in educations[:2]:
                if isinstance(ed, dict):
                    resume_summary_lines.append(f"Education: {ed.get('degree', 'Degree')} from {ed.get('institution', 'Institution')}")

        resume_summary = "\n".join(resume_summary_lines) if resume_summary_lines else "No resume uploaded yet (Base recommendation on discovery assessment strengths)."

        lang_instruction = ""
        if language == "hi":
            lang_instruction = "\nIMPORTANT LANGUAGE REQUIREMENT: The user language preference is Hindi. Write work_style_summary, motivation_profile, evidence_reason, why_recommended, supporting_strengths, potential_challenges, learning_gaps, resume_match_reasons, and assessment_match_reasons in clear, professional Hindi while keeping technical career titles, domain tags, and slugs clean."

        prompt = f"""
Available Target Career Catalog Roles:
{roles_catalog_str}

User Discovery Assessment Responses:
{answers_summary}

Candidate Resume Background & Practical Evidence:
{resume_summary}

Task:
You are an expert AI Career Coach & Strategic Talent Architect.
Suggest the optimal Career Domains and Target Roles by HOLISTICALLY SYNTHESIZING TWO COMPLEMENTARY SOURCES:
1. Discovery Assessment: Natural psychological strengths, problem solving style, analytical aptitude, work style preferences, and archetype.
2. Resume Profile: Tangible verified technical & soft skills, real projects built, work experience achievements, and formal education.

Instructions for Career Domain Suggestions:
- Match the user against the catalog of roles by balancing Discovery Assessment traits (cognitive fit) and Resume background (practical skill fit).
- For each recommended role:
  * "career_domain": Broad industry/tech domain (e.g. "Full Stack & Cloud Architecture", "Data Science & AI", "DevOps & Infrastructure", "Product Engineering", "Cybersecurity").
  * "why_recommended": Explain clearly how their assessment strengths AND their resume background come together for this role.
  * "resume_match_reasons": List 2-3 specific skills, projects, or experiences from their resume that support this domain. (If no resume was provided, note: "Recommended based on assessment instincts; add projects in this domain").
  * "assessment_match_reasons": List 2-3 psychological strengths, problem-solving habits, or archetype traits from the assessment.
  * "learning_gaps": Missing skills needed to master this role based on the catalog requirements.
- Calculate match_percentage realistically (60-98) reflecting their combined aptitude and skill overlap.
- Provide "career_domains_summary" summarizing their best-fit career domains.
{lang_instruction}

Return a structured JSON evaluation matching:
- primary_archetype (e.g. Systems Builder, Data Investigator, Creative Visualizer, AI Pioneer, User Strategist)
- top_strengths (array of objects with strength_name and evidence_reason)
- interest_profile (array of strings)
- work_style_summary (string)
- motivation_profile (string)
- career_domains_summary (string summarizing the candidate's optimal career domains)
- recommended_careers (array of objects matching exact slugs from catalog: slug, title, career_domain, match_percentage, confidence_percentage, why_recommended, supporting_strengths, potential_challenges, learning_gaps, resume_match_reasons, assessment_match_reasons)
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
        return self._generate_deterministic_analysis(
            roles, archetype_tally, role_weight_tally, answers_summary, user_skills_list, language=language
        )

    def _generate_deterministic_analysis(
        self,
        roles: List[CareerRole],
        archetype_tally: Dict[str, int],
        role_weight_tally: Dict[str, int],
        answers_summary: str,
        user_skills_list: List[str],
        language: str = "en"
    ) -> CareerDiscoveryAIAnalysis:
        is_hi = language == "hi"
        primary_arch = max(archetype_tally, key=archetype_tally.get) if archetype_tally else "Systems Builder"

        # Calculate scores for catalog roles based on role_weight_tally and resume skill overlap
        ranked_roles = []
        max_possible_score = max(role_weight_tally.values()) if role_weight_tally else 50
        max_possible_score = max(max_possible_score, 1)

        user_skills_lower = {s.lower() for s in user_skills_list}

        for role in roles:
            raw_score = role_weight_tally.get(role.title, 0)
            base_pct = int((raw_score / max_possible_score) * 30 + 55)

            # Bonus for resume skills matching role's required skills
            matching_skills = [
                s for s in role.required_skills 
                if s.lower() in user_skills_lower or any(us in s.lower() for us in user_skills_lower)
            ]
            resume_bonus = min(15, len(matching_skills) * 4)
            final_pct = min(96, max(60, base_pct + resume_bonus))

            ranked_roles.append((role, final_pct, matching_skills))

        ranked_roles.sort(key=lambda x: x[1], reverse=True)

        recommended_matches = []
        for role, pct, matched_skills in ranked_roles[:4]:
            why = [
                f"Strong alignment with {role.preferred_strengths[0] if role.preferred_strengths else 'problem solving'}." if not is_hi else f"{role.preferred_strengths[0] if role.preferred_strengths else 'समस्या समाधान'} के साथ मजबूत तालमेल।",
                f"Resume verified hands-on skills in {', '.join(matched_skills[:2]) if matched_skills else 'software foundation'}." if not is_hi else f"रिज्यूमे में सत्यापित कौशल: {', '.join(matched_skills[:2]) if matched_skills else 'सॉफ्टवेयर आधार'}।",
                f"Preferred work style matches '{role.work_style}'." if not is_hi else f"पसंदीदा कार्यशैली '{role.work_style}' से मेल खाती है।"
            ]
            challenges = [
                f"Requires mastering {role.required_skills[-1] if role.required_skills else 'advanced tools'}." if not is_hi else f"{role.required_skills[-1] if role.required_skills else 'उन्नत उपकरण'} में महारत हासिल करने की आवश्यकता है।",
                "Requires ongoing continuous learning as ecosystem evolves." if not is_hi else "तकनीकी पारिस्थितिकी तंत्र विकसित होने के साथ निरंतर सीखने की आवश्यकता है।"
            ]
            
            # Domain mapping
            domain_name = "Software Engineering & Architecture"
            if any(k in role.title.lower() for k in ["data", "analyst", "ai", "machine learning"]):
                domain_name = "Data Science & Artificial Intelligence"
            elif any(k in role.title.lower() for k in ["devops", "cloud", "security"]):
                domain_name = "Cloud Architecture & DevOps"
            elif any(k in role.title.lower() for k in ["product", "manager", "ui", "ux"]):
                domain_name = "Product Design & Strategy"

            match_obj = CareerMatchSchema(
                slug=role.slug,
                title=role.title,
                career_domain=domain_name,
                match_percentage=pct,
                confidence_percentage=min(92, pct - 5),
                why_recommended=why,
                supporting_strengths=role.preferred_strengths[:2],
                potential_challenges=challenges,
                learning_gaps=role.learning_areas[:2],
                resume_match_reasons=[f"Demonstrated proficiency in {s}" for s in matched_skills[:3]] if matched_skills else ["Foundation ready for project building"],
                assessment_match_reasons=[f"Matches '{primary_arch}' cognitive archetype", f"Prefers {role.work_style} work style"]
            )
            recommended_matches.append(match_obj)

        alternatives = [r.title for r, _, _ in ranked_roles[4:7]]

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
        domains_summary = f"Optimal career domains centered in {recommended_matches[0].career_domain if recommended_matches else 'Software Engineering'} combining assessment problem solving and resume technical background."

        return CareerDiscoveryAIAnalysis(
            primary_archetype=primary_arch,
            top_strengths=top_strengths_list,
            interest_profile=["Software Architecture", "Database Systems", "Automation Tools"],
            work_style_summary=work_style,
            motivation_profile=motivation,
            career_domains_summary=domains_summary,
            recommended_careers=recommended_matches,
            alternative_careers=alternatives
        )
