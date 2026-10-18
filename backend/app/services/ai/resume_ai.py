import re
import logging
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.client import AIService
from app.services.ai.prompts import (
    RESUME_ANALYSIS_SYSTEM_PROMPT, 
    RESUME_FORMAT_AND_CONVERT_PROMPT,
    RESUME_VERIFICATION_AND_EXTRACTION_PROMPT
)
from app.services.resume.extractor import DocumentExtractor
from app.services.resume.parser import ResumeParser
from app.services.resume.ats_engine import ATSEngine
from app.services.resume.target_matcher import TargetCareerMatcher
from app.services.resume.improver import ResumeImprover
from app.schemas.resume import (
    ParsedContactInfo,
    ExtractedSkillSchema,
    ATSBreakdownSchema,
    TargetCareerMatchSchema,
    BulletImprovementSchema,
    ResumeAnalysisResponse,
    ResumeVerificationAndProfileExtraction,
    ResumeExperienceItem,
    ResumeProjectItem,
    ResumeEducationItem,
    ResumeCertificationItem,
    ResumeSkillItem
)

logger = logging.getLogger(__name__)


class ResumeAIService:
    def __init__(self, provider=None):
        self.provider = provider or AIService.get_provider()
        self.extractor = DocumentExtractor()
        self.parser = ResumeParser()
        self.ats_engine = ATSEngine()
        self.target_matcher = TargetCareerMatcher()
        self.improver = ResumeImprover()

    async def verify_and_extract_profile(self, raw_text: str) -> ResumeVerificationAndProfileExtraction:
        """
        Uses Groq AI to check if the uploaded document is a genuine resume/CV.
        If true, extracts all profile parts (about_user, skills, experience, projects, education, certifications).
        If false, provides rejection reason.
        """
        prompt = (
            f"AUDIT AND EXTRACT CANDIDATE RESUME PROFILE:\n"
            f"```text\n{raw_text[:7500]}\n```\n\n"
            f"1. Is this document genuinely a candidate's personal resume or CV? If not (e.g. invoice, receipt, assignment, random text), set is_resume: false.\n"
            f"2. If valid resume, extract all structured sections in detail."
        )

        try:
            extraction = await self.provider.generate_structured(
                prompt=prompt,
                output_schema=ResumeVerificationAndProfileExtraction,
                system_instruction=RESUME_VERIFICATION_AND_EXTRACTION_PROMPT
            )
            return extraction
        except Exception as e:
            logger.warning(f"Groq structured resume verification exception ({e}), falling back to heuristic validator...")
            return self._heuristic_verify_and_extract(raw_text)

    def _heuristic_verify_and_extract(self, raw_text: str) -> ResumeVerificationAndProfileExtraction:
        """Rule-based safety fallback if AI provider is momentarily unreachable."""
        text_lower = raw_text.lower()

        # Reject obvious non-resumes
        invoice_keywords = ["invoice", "tax invoice", "bill to:", "total amount", "gstin", "subtotal", "terms and conditions", "due date"]
        if any(kw in text_lower for kw in invoice_keywords) and not any(kw in text_lower for kw in ["education", "experience", "curriculum vitae", "work experience"]):
            return ResumeVerificationAndProfileExtraction(
                is_resume=False,
                confidence_score=10,
                rejection_reason="The document appears to be an invoice, bill, or financial document, not a personal resume/CV.",
                about_user=ParsedContactInfo(),
                skills=[],
                experience=[],
                projects=[],
                education=[],
                certifications=[]
            )

        resume_signals = [
            "experience", "education", "skills", "projects", "summary", 
            "objective", "curriculum vitae", "resume", "b.tech", "b.e", "bachelor", 
            "master", "university", "college", "work history", "employment"
        ]
        matches = sum(1 for s in resume_signals if s in text_lower)
        has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text))

        if matches < 2 and not has_email:
            return ResumeVerificationAndProfileExtraction(
                is_resume=False,
                confidence_score=25,
                rejection_reason="The document lacks standard resume sections such as Education, Experience, Skills, or Contact details.",
                about_user=ParsedContactInfo(),
                skills=[],
                experience=[],
                projects=[],
                education=[],
                certifications=[]
            )

        # Parse with local parser
        parsed = self.parser.parse(raw_text)
        contact = parsed.get("contact_info", {})
        contact_obj = ParsedContactInfo(
            name=contact.get("name") or "Candidate",
            email=contact.get("email") or "",
            phone=contact.get("phone") or "",
            linkedin=contact.get("linkedin") or "",
            github=contact.get("github") or "",
            portfolio=contact.get("portfolio") or "",
            summary=parsed.get("summary") or ""
        )

        skills = [
            ResumeSkillItem(name=s, category="Technical", proficiency_estimated=None)
            for s in parsed.get("skills", [])
        ]

        exp_items = []
        for exp in parsed.get("experience", []):
            if isinstance(exp, dict):
                role = exp.get("role") or exp.get("title") or "Software Engineer"
                company = exp.get("company", "")
                exp_items.append(ResumeExperienceItem(
                    role=role,
                    company=company,
                    location=exp.get("location", ""),
                    start_date=exp.get("start_date", ""),
                    end_date=exp.get("end_date", ""),
                    is_current=exp.get("is_current", False),
                    description=exp.get("description", ""),
                    key_achievements=exp.get("key_achievements", [])
                ))

        proj_items = []
        for p in parsed.get("projects", []):
            if isinstance(p, dict):
                p_title = p.get("title") or p.get("name") or "Project"
                if p_title.strip():
                    proj_items.append(ResumeProjectItem(
                        title=p_title.strip(),
                        role=p.get("role") or "Developer",
                        technologies=p.get("technologies") or [],
                        description=p.get("description", ""),
                        link=p.get("link", "")
                    ))

        edu_items = []
        for ed in parsed.get("education", []):
            if isinstance(ed, dict):
                degree = ed.get("degree") or ed.get("title") or "Degree"
                if degree.strip():
                    edu_items.append(ResumeEducationItem(
                        degree=degree.strip(),
                        institution=ed.get("institution", ""),
                        field_of_study=ed.get("field_of_study", ""),
                        start_year=ed.get("start_year", ""),
                        end_year=ed.get("end_year", ""),
                        grade=ed.get("grade", "")
                    ))

        return ResumeVerificationAndProfileExtraction(
            is_resume=True,
            confidence_score=75,
            rejection_reason=None,
            about_user=contact_obj,
            skills=skills,
            experience=exp_items,
            projects=proj_items,
            education=edu_items,
            certifications=[]
        )

    async def format_resume_text_with_groq(self, raw_text: str) -> str:
        """Uses Groq AI to format messy raw extracted text into clean, structured Markdown resume text."""
        try:
            prompt = (
                f"Candidate Raw Extracted Resume Text:\n"
                f"```text\n{raw_text[:6000]}\n```\n\n"
                f"Please reconstruct and output the clean, well-formatted resume in standard Markdown text."
            )
            formatted = await self.provider.generate_text(
                prompt=prompt,
                system_instruction=RESUME_FORMAT_AND_CONVERT_PROMPT
            )
            cleaned = formatted.strip()
            if cleaned.startswith("```markdown") and cleaned.endswith("```"):
                cleaned = cleaned[11:-3].strip()
            elif cleaned.startswith("```") and cleaned.endswith("```"):
                cleaned = cleaned[3:-3].strip()
            return cleaned if len(cleaned) > 30 else raw_text
        except Exception as e:
            logger.warning(f"Groq AI resume text formatting notice (fallback to raw text): {e}")
            return raw_text

    async def analyze_resume_text(
        self,
        db: AsyncSession,
        user_id: str,
        resume_id: str,
        filename: str,
        raw_text: str,
        job_description: Optional[str] = None,
        override_role: Optional[str] = None
    ) -> ResumeAnalysisResponse:
        # 1. STRICT RESUME VALIDATION & STRUCTURED PROFILE EXTRACTION VIA GROQ AI
        logger.info(f"🔎 [RESUME AUDIT] Validating whether '{filename}' is a genuine candidate resume...")
        extraction: ResumeVerificationAndProfileExtraction = await self.verify_and_extract_profile(raw_text)

        if not extraction.is_resume or extraction.confidence_score < 40:
            rejection_msg = extraction.rejection_reason or "Document does not match candidate CV or resume structure."
            logger.warning(f"🚫 [RESUME DISCARDED] File '{filename}' was rejected: {rejection_msg}")
            raise HTTPException(
                status_code=400,
                detail="Sorry hum aapke baare me nahi jaan payen hai toh please assesment dijiye."
            )

        if not extraction.skills and not extraction.experience and not extraction.education:
            logger.warning(f"🚫 [INSUFFICIENT RESUME DATA] No skills or profile details found in '{filename}'.")
            raise HTTPException(
                status_code=400,
                detail="Sorry hum aapke baare me nahi jaan payen hai toh please assesment dijiye."
            )

        logger.info(
            f"✅ [RESUME VERIFIED] '{filename}' confirmed as genuine resume "
            f"(Confidence: {extraction.confidence_score}% | Candidate: {extraction.about_user.name})"
        )

        # 2. Parse structured section content for deterministic ATS calculations
        parsed = self.parser.parse(raw_text)

        # Determine Target Role or Vacancy Mode
        target_role = override_role
        if not target_role:
            from app.models.profile import UserProfile
            from app.models.career_catalog import CareerRole
            from sqlalchemy import select

            p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
            p_res = await db.execute(p_stmt)
            user_profile = p_res.scalars().first()
            if user_profile and user_profile.target_career and user_profile.target_career.strip():
                if user_profile.target_career.strip().lower() not in ["none", "null", "undefined"]:
                    target_role = user_profile.target_career.strip()

        # If job description is explicitly provided with sufficient length
        has_jd = bool(job_description and len(job_description.strip()) >= 20)

        catalog_skills = None
        if target_role and not has_jd:
            from app.models.career_catalog import CareerRole
            from sqlalchemy import select

            c_stmt = select(CareerRole).where(CareerRole.title == target_role)
            c_res = await db.execute(c_stmt)
            catalog_role = c_res.scalars().first()
            if not catalog_role:
                c_stmt = select(CareerRole).where(CareerRole.slug.ilike(f"%{target_role.lower().replace(' ', '-')}%"))
                c_res = await db.execute(c_stmt)
                catalog_role = c_res.scalars().first()
            if catalog_role and catalog_role.required_skills:
                catalog_skills = catalog_role.required_skills

        # 3. Algorithmic ATS Evaluation & Risk Identification
        ats_breakdown, risk_flags = self.ats_engine.evaluate_resume(
            parsed_resume=parsed,
            raw_text=raw_text,
            target_role=target_role,
            job_description=job_description if has_jd else None,
            catalog_skills=catalog_skills
        )

        # 4. Build consolidated skills list (prioritizing exact resume skills verbatim)
        all_skills_dict = {}
        # First: exact skills parsed directly from candidate's resume skills section
        exact_from_section = [s for s in parsed.get("skills", []) if s and not self.parser._is_invalid_skill(s)]
        for s in exact_from_section:
            clean_s = s.strip()
            all_skills_dict[clean_s] = {
                "category": "Technical",
                "proficiency": None
            }

        # Second: If candidate explicitly listed skills in their resume's skills section,
        # we strictly use those skills and do NOT pollute them with random summary words.
        # Only if the skills section was empty do we fall back to AI extraction.
        if not all_skills_dict:
            for s in extraction.skills:
                if s.name and s.name.strip():
                    raw_name = s.name.strip()
                    if not self.parser._is_invalid_skill(raw_name):
                        matched_key = next((k for k in all_skills_dict if k.lower() == raw_name.lower()), None)
                        if not matched_key:
                            all_skills_dict[raw_name] = {
                                "category": s.category or "Technical",
                                "proficiency": s.proficiency_estimated
                            }

        skill_names_list = list(all_skills_dict.keys())

        # 5. Target Career Overlap Match against user's selected Target Role or Job Description
        target_match = await self.target_matcher.match_resume_to_target(
            db=db,
            user_id=user_id,
            resume_skills=skill_names_list,
            job_description=job_description if has_jd else None,
            override_role_title=target_role
        )

        # 6. Generate Bullet Point Improvements
        improvements = self.improver.generate_improvements(
            parsed, target_match.missing_skills
        )

        # 7. Build Extracted Skills list with confidence signals (without fabricated percentages)
        extracted_skills = [
            ExtractedSkillSchema(
                name=sk_name,
                category=all_skills_dict[sk_name]["category"],
                proficiency_estimated=all_skills_dict[sk_name]["proficiency"],
                source="Resume Extraction",
                confidence_level="High" if any(sk_name.lower() in m.lower() or m.lower() in sk_name.lower() for m in target_match.matching_skills) else "Medium"
            )
            for sk_name in skill_names_list
        ]

        # 8. Assemble comprehensive candidate profile
        contact = extraction.about_user
        if not contact.name or contact.name == "Candidate":
            parsed_contact = parsed.get("contact_info", {})
            if parsed_contact.get("name") and parsed_contact["name"] != "Candidate":
                contact.name = parsed_contact["name"]
        if not contact.email:
            contact.email = parsed.get("contact_info", {}).get("email", "")
        if not contact.phone:
            contact.phone = parsed.get("contact_info", {}).get("phone", "")
        if not contact.linkedin:
            contact.linkedin = parsed.get("contact_info", {}).get("linkedin", "")
        if not contact.github:
            contact.github = parsed.get("contact_info", {}).get("github", "")
        if not contact.portfolio:
            contact.portfolio = parsed.get("contact_info", {}).get("portfolio", "")

        # Clean summary to ensure no redundant name, role, email, phone, or links repeat
        if contact.summary:
            contact.summary = self._clean_summary(contact.summary, contact)

        return ResumeAnalysisResponse(
            id=resume_id,
            filename=filename,
            ats_score=ats_breakdown.overall_ats_score,
            ats_breakdown=ats_breakdown,
            target_match=target_match,
            contact_info=contact,
            extracted_skills=extracted_skills,
            formatting_risk_flags=risk_flags,
            improvement_suggestions=improvements,
            formatted_text=None,
            raw_text=None,
            about_user=contact,
            experience=extraction.experience,
            projects=extraction.projects,
            education=extraction.education,
            certifications=extraction.certifications
        )

    @staticmethod
    def _clean_summary(raw_summary: str, contact: Any) -> str:
        if not raw_summary or not raw_summary.strip():
            return ""
        name = getattr(contact, "name", "").lower().strip()
        headline = getattr(contact, "headline", "").lower().strip()
        email = getattr(contact, "email", "").lower().strip()
        phone_digits = "".join(filter(str.isdigit, getattr(contact, "phone", "")))

        cleaned_lines = []
        for line in raw_summary.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            lower = line_str.lower()
            if name and (lower == name or lower.startswith(f"{name} -") or lower.startswith(f"{name} |")):
                continue
            if headline and (lower == headline or lower.startswith(f"{headline} |") or lower.startswith(f"{headline} -")):
                continue
            # Filter standalone role/designation titles (e.g. Software Engineer, Full Stack Developer, etc.)
            role_pattern = r"^(aspiring|junior|senior|lead|entry[-\s]?level|associate)?\s*(software|web|full[-\s]?stack|frontend|backend|mobile|android|ios|devops|cloud|data|ai|ml|machine[-\s]?learning|deep[-\s]?learning|python|java|react|node|c\+\+|system|systems|qa|test|testing|cyber|security|network|database|computer[-\s]?science)?\s*(engineer|developer|programmer|architect|specialist|analyst|scientist|student|intern|fresher|consultant|professional|coder)s?$"
            if re.match(role_pattern, line_str, re.IGNORECASE):
                continue
            if len(line_str.split()) <= 4 and re.search(r"\b(engineer|developer|programmer|architect|specialist|analyst|scientist|student|intern|fresher)\b", line_str, re.IGNORECASE) and not re.search(r"[.,;!?]", line_str):
                continue
            if ("http://" in lower or "https://" in lower or "github.com" in lower or "linkedin.com" in lower or (email and email in lower)):
                if "|" in lower or "github" in lower or "linkedin" in lower or len(line_str.split()) < 15:
                    continue
            digits = "".join(filter(str.isdigit, line_str))
            if phone_digits and len(phone_digits) >= 7 and phone_digits in digits:
                continue
            if ("|" in lower or "•" in lower) and ("phone" in lower or "mail" in lower or "@" in lower or len(digits) >= 10):
                continue
            if line_str in ("|", "-", "•", "/", ","):
                continue
            cleaned_lines.append(line_str)
        return "\n\n".join(cleaned_lines).strip() or raw_summary.strip()


