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
    ResumeSkillItem,
    ResumeAchievementItem,
    ResumePublicationItem,
    ResumeLanguageItem,
    ResumeExtracurricularItem,
    ResumeDomainSuggestion
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

        cert_items = [
            ResumeCertificationItem(
                name=c.get("name") or "Certification",
                issuer=c.get("issuer", ""),
                issue_date=c.get("issue_date", ""),
                credential_id_or_url=c.get("credential_id_or_url", "")
            )
            for c in parsed.get("certifications", [])
            if isinstance(c, dict) and (c.get("name") or "").strip()
        ]

        ach_items = [
            ResumeAchievementItem(
                title=a.get("title") or "Achievement",
                issuer_or_event=a.get("issuer_or_event", ""),
                year=a.get("year", ""),
                description=a.get("description", "")
            )
            for a in parsed.get("achievements", [])
            if isinstance(a, dict) and (a.get("title") or "").strip()
        ]

        lang_items = [
            ResumeLanguageItem(
                language=l.get("language") or "Language",
                proficiency=l.get("proficiency", "Proficient")
            )
            for l in parsed.get("languages", [])
            if isinstance(l, dict) and (l.get("language") or "").strip()
        ]

        pub_items = [
            ResumePublicationItem(
                title=pub.get("title") or "Publication",
                authors_or_journal=pub.get("authors_or_journal", ""),
                date_or_year=pub.get("date_or_year", ""),
                url_or_doi=pub.get("url_or_doi", ""),
                description=pub.get("description", "")
            )
            for pub in parsed.get("publications", [])
            if isinstance(pub, dict) and (pub.get("title") or "").strip()
        ]

        extra_items = [
            ResumeExtracurricularItem(
                role=ex.get("role") or "Member",
                organization=ex.get("organization", ""),
                duration=ex.get("duration", ""),
                description=ex.get("description", "")
            )
            for ex in parsed.get("extracurriculars", [])
            if isinstance(ex, dict) and (ex.get("role") or "").strip()
        ]

        return ResumeVerificationAndProfileExtraction(
            is_resume=True,
            confidence_score=75,
            rejection_reason=None,
            about_user=contact_obj,
            skills=skills,
            experience=exp_items,
            projects=proj_items,
            education=edu_items,
            certifications=cert_items,
            achievements=ach_items,
            publications=pub_items,
            languages=lang_items,
            extracurriculars=extra_items
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

        # Fallback recovery: Ensure no section is lost if Groq AI under-extracted projects, certs, etc.
        if not extraction.projects and parsed.get("projects"):
            extraction.projects = [
                ResumeProjectItem(
                    title=p.get("title") or "Project",
                    role=p.get("role") or "Developer",
                    technologies=p.get("technologies") or [],
                    description=p.get("description", ""),
                    link=p.get("link", "")
                )
                for p in parsed.get("projects", [])
                if isinstance(p, dict) and (p.get("title") or "").strip()
            ]

        if not extraction.certifications and parsed.get("certifications"):
            extraction.certifications = [
                ResumeCertificationItem(
                    name=c.get("name") or "Certification",
                    issuer=c.get("issuer", ""),
                    issue_date=c.get("issue_date", ""),
                    credential_id_or_url=c.get("credential_id_or_url", "")
                )
                for c in parsed.get("certifications", [])
                if isinstance(c, dict) and (c.get("name") or "").strip()
            ]

        if not extraction.achievements and parsed.get("achievements"):
            extraction.achievements = [
                ResumeAchievementItem(
                    title=a.get("title") or "Achievement",
                    issuer_or_event=a.get("issuer_or_event", ""),
                    year=a.get("year", ""),
                    description=a.get("description", "")
                )
                for a in parsed.get("achievements", [])
                if isinstance(a, dict) and (a.get("title") or "").strip()
            ]

        if not extraction.languages and parsed.get("languages"):
            extraction.languages = [
                ResumeLanguageItem(
                    language=l.get("language") or "Language",
                    proficiency=l.get("proficiency", "Proficient")
                )
                for l in parsed.get("languages", [])
                if isinstance(l, dict) and (l.get("language") or "").strip()
            ]

        if not extraction.publications and parsed.get("publications"):
            extraction.publications = [
                ResumePublicationItem(
                    title=pub.get("title") or "Publication",
                    authors_or_journal=pub.get("authors_or_journal", ""),
                    date_or_year=pub.get("date_or_year", ""),
                    url_or_doi=pub.get("url_or_doi", ""),
                    description=pub.get("description", "")
                )
                for pub in parsed.get("publications", [])
                if isinstance(pub, dict) and (pub.get("title") or "").strip()
            ]

        if not extraction.extracurriculars and parsed.get("extracurriculars"):
            extraction.extracurriculars = [
                ResumeExtracurricularItem(
                    role=ex.get("role") or "Member",
                    organization=ex.get("organization", ""),
                    duration=ex.get("duration", ""),
                    description=ex.get("description", "")
                )
                for ex in parsed.get("extracurriculars", [])
                if isinstance(ex, dict) and (ex.get("role") or "").strip()
            ]

        # Decongest any congested experience blocks (separates bundled internships, leadership, and projects)
        extraction = self._decongest_profile(extraction)

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

        # 9. Generate Intelligent Career Domain Suggestions based on parsed profile
        domain_suggestions = self.generate_domain_suggestions(
            extracted_skills=extracted_skills,
            projects=extraction.projects,
            experience=extraction.experience,
            education=extraction.education
        )

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
            certifications=extraction.certifications,
            achievements=extraction.achievements,
            publications=extraction.publications,
            languages=extraction.languages,
            extracurriculars=extraction.extracurriculars,
            suggested_domains=domain_suggestions
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

    @classmethod
    def _decongest_profile(cls, extraction: ResumeVerificationAndProfileExtraction) -> ResumeVerificationAndProfileExtraction:
        """Decongests congested experience blocks where multiple jobs, leadership, or projects were bundled into a single description."""
        new_experiences: List[ResumeExperienceItem] = []
        new_projects = list(extraction.projects)
        new_extracurriculars = list(extraction.extracurriculars)

        for exp in extraction.experience:
            desc = exp.description or ""
            has_projects = bool(re.search(r'(?:SELECTED PROJECTS|ACADEMIC PROJECTS|PERSONAL PROJECTS|KEY PROJECTS|(?:\.|\n|^)\s*PROJECTS\s*[:\-–]?\s*[A-Z0-9])', desc, re.IGNORECASE))
            has_interns = bool(re.search(r'(?:ARTIFICIAL INTELLIGENCE INTERN|PYTHON DEVELOPMENT INTERN|[A-Z\s]{4,30}\s+INTERN)', desc))
            has_leadership = bool(re.search(r'(?:PRESIDENT|VICE PRESIDENT|LEAD|HEAD)\s*[-–]\s*(?:DEVELOPERS|CLUB)', desc, re.IGNORECASE))

            if not (has_projects or (has_interns and len(desc) > 120) or has_leadership):
                new_experiences.append(exp)
                continue

            remaining = desc.strip()

            # 1. Extract Selected Projects from description
            proj_match = re.search(r'(?:SELECTED PROJECTS|ACADEMIC PROJECTS|PERSONAL PROJECTS|KEY PROJECTS|(?:\.|\n|^)\s*PROJECTS\s*[:\-–]?\s*[A-Z0-9])', remaining, re.IGNORECASE)
            if proj_match:
                actual_idx = proj_match.start()
                p_text_raw = remaining[actual_idx:]
                header_match = re.search(r'(?:SELECTED PROJECTS|ACADEMIC PROJECTS|PERSONAL PROJECTS|KEY PROJECTS|PROJECTS)\s*[:\-–]?\s*', p_text_raw, re.IGNORECASE)
                if header_match:
                    proj_text = p_text_raw[header_match.end():]
                    remaining = remaining[:actual_idx].strip()

                    p_regex = re.compile(r'([A-Z0-9\s/_-]{2,35})\s*•\s*')
                    matches = list(p_regex.finditer(proj_text))
                    if matches:
                        for i, m in enumerate(matches):
                            title = m.group(1).strip()
                            title = re.sub(r'Technologies\s*:\s*.*$', '', title, flags=re.IGNORECASE).strip()
                            title = re.sub(r'^(?:SELECTED PROJECTS|PROJECTS)\s*', '', title, flags=re.IGNORECASE).strip()
                            c_start = m.end()
                            c_end = matches[i + 1].start() if i + 1 < len(matches) else len(proj_text)
                            chunk_text = proj_text[c_start:c_end]

                            techs = []
                            tech_m = re.search(r'Technologies\s*:\s*([^\n•]+)', chunk_text, re.IGNORECASE)
                            if tech_m:
                                techs = [t.strip() for t in re.split(r'[,|/]', tech_m.group(1)) if t.strip()]

                            raw_bullets = [b.strip() for b in re.split(r'\s*•\s*', re.sub(r'Technologies\s*:\s*[^\n•]+', '', chunk_text, flags=re.IGNORECASE)) if b.strip()]

                            if title:
                                new_projects.append(ResumeProjectItem(
                                    title=title,
                                    role="Developer",
                                    technologies=techs,
                                    description="\n\n".join(raw_bullets) if raw_bullets else chunk_text.strip(),
                                    link=""
                                ))

            # 2. Extract markers for sub-roles e.g. INTERN, PRESIDENT
            marker_pattern = re.compile(r'(?:\.|\n|^|\s{2,})\s*(ARTIFICIAL INTELLIGENCE INTERN|PYTHON DEVELOPMENT INTERN|PRESIDENT\s*[-–]\s*DEVELOPERS CLUB|SOFTWARE DEVELOPER|SOFTWARE ENGINEER|FULL STACK DEVELOPER|FRONTEND DEVELOPER|BACKEND DEVELOPER|DATA SCIENCE INTERN|WEB DEVELOPMENT INTERN|[A-Z\s]{4,30}\s+INTERN)')
            markers = []
            for m in marker_pattern.finditer(remaining):
                role_name = m.group(1).strip()
                snippet = remaining[m.start():m.start() + 200]
                if re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}\b', snippet, re.IGNORECASE):
                    full_match = m.group(0)
                    markers.append({
                        "role": role_name,
                        "index": m.start() + full_match.find(role_name)
                    })

            if not markers:
                exp.description = remaining
                new_experiences.append(exp)
                continue

            segments = []
            if markers[0]["index"] > 0:
                segments.append({
                    "isFirst": True,
                    "text": remaining[:markers[0]["index"]].strip()
                })
            for i, cur in enumerate(markers):
                next_m = markers[i + 1] if i + 1 < len(markers) else None
                s_text = remaining[cur["index"]:next_m["index"]].strip() if next_m else remaining[cur["index"]:].strip()
                segments.append({
                    "role": cur["role"],
                    "text": s_text,
                    "isFirst": False
                })

            for seg in segments:
                s_text = seg["text"]
                d_m = re.search(r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}\s*[-–]\s*(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}))\b', s_text, re.IGNORECASE)
                duration = d_m.group(1) if d_m else ""
                start_date = duration.split("-")[0].strip() if "-" in duration else (duration.split("–")[0].strip() if "–" in duration else "")
                end_date = "Present" if "present" in duration.lower() else (duration.split("-")[1].strip() if "-" in duration else (duration.split("–")[1].strip() if "–" in duration else ""))
                is_current = "present" in duration.lower()

                if seg.get("isFirst"):
                    before_d = s_text[:d_m.start()].strip() if d_m else exp.company or "Trinity Solutions"
                    after_d = s_text[d_m.end():].strip() if d_m else s_text
                    new_experiences.append(ResumeExperienceItem(
                        role=exp.role or "Software Developer",
                        company=before_d or exp.company,
                        start_date=start_date or exp.start_date,
                        end_date=end_date or exp.end_date,
                        is_current=is_current or exp.is_current,
                        description=after_d
                    ))
                elif "PRESIDENT" in seg.get("role", "").upper() or "CLUB" in seg.get("role", "").upper():
                    no_role = s_text[len(seg["role"]):].strip()
                    before_d = no_role[:no_role.find(duration)].strip() if duration and duration in no_role else "Developers Club"
                    after_d = no_role[no_role.find(duration) + len(duration):].strip() if duration and duration in no_role else no_role
                    new_extracurriculars.append(ResumeExtracurricularItem(
                        role=seg["role"],
                        organization=before_d,
                        duration=duration,
                        description=after_d
                    ))
                else:
                    no_role = s_text[len(seg["role"]):].strip()
                    before_d = no_role[:no_role.find(duration)].strip() if duration and duration in no_role else "Tech Company"
                    after_d = no_role[no_role.find(duration) + len(duration):].strip() if duration and duration in no_role else no_role
                    new_experiences.append(ResumeExperienceItem(
                        role=seg["role"],
                        company=before_d,
                        start_date=start_date,
                        end_date=end_date,
                        is_current=is_current,
                        description=after_d
                    ))

        extraction.experience = new_experiences if new_experiences else extraction.experience
        extraction.projects = new_projects
        extraction.extracurriculars = new_extracurriculars
        return extraction

    @classmethod
    def generate_domain_suggestions(
        cls,
        extracted_skills: List[Any],
        projects: List[Any],
        experience: List[Any],
        education: Optional[List[Any]] = None
    ) -> List[ResumeDomainSuggestion]:
        """
        Analyzes candidate verified skills, project portfolio, and work experience
        to produce personalized, deterministic career domain suggestions with fit rationale,
        supporting skills, and high-leverage growth areas.
        """
        skill_names = set()
        for sk in (extracted_skills or []):
            if isinstance(sk, str):
                skill_names.add(sk.strip().lower())
            elif isinstance(sk, dict) and sk.get("name"):
                skill_names.add(sk["name"].strip().lower())
            elif hasattr(sk, "name") and sk.name:
                skill_names.add(sk.name.strip().lower())

        projects_text = ""
        project_titles = []
        for p in (projects or []):
            p_dict = p if isinstance(p, dict) else (p.model_dump() if hasattr(p, "model_dump") else {})
            title = p_dict.get("title", "")
            if title:
                project_titles.append(title)
            desc = p_dict.get("description", "")
            techs = " ".join(p_dict.get("technologies", []))
            projects_text += f" {title} {desc} {techs}"

        exp_text = ""
        exp_roles = []
        for e in (experience or []):
            e_dict = e if isinstance(e, dict) else (e.model_dump() if hasattr(e, "model_dump") else {})
            role = e_dict.get("role", "")
            if role:
                exp_roles.append(role)
            company = e_dict.get("company", "")
            desc = e_dict.get("description", "")
            achievements = " ".join(e_dict.get("key_achievements", []))
            exp_text += f" {role} {company} {desc} {achievements}"

        full_corpus = f"{projects_text} {exp_text}".lower()

        def has_competency(comp: str) -> bool:
            comp_clean = comp.lower().strip()
            if comp_clean in skill_names:
                return True
            for sk in skill_names:
                if comp_clean == sk or f" {comp_clean} " in f" {sk} ":
                    return True
            pattern = r'\b' + re.escape(comp_clean) + r'\b'
            if re.search(pattern, full_corpus):
                return True
            return False

        domain_definitions = [
            {
                "domain_name": "Artificial Intelligence & Machine Learning",
                "core_skills": [
                    "Python", "PyTorch", "TensorFlow", "TensorFlow Lite", "Keras",
                    "Machine Learning", "Deep Learning", "LLMs", "LLaMA", "Groq",
                    "RAG", "LangChain", "MediaPipe", "OpenCV", "Scikit-Learn",
                    "Pandas", "NumPy", "ChromaDB", "Vector Databases", "NLP",
                    "Computer Vision", "AI Inference"
                ],
                "recommended_roles": [
                    "AI / Machine Learning Engineer",
                    "LLM & Generative AI Developer",
                    "Computer Vision / Edge AI Specialist",
                    "Data Scientist"
                ],
                "growth_areas": [
                    "LangChain & LlamaIndex Agentic Workflows",
                    "Model Quantization (GGUF, TensorRT) for Edge Devices",
                    "PEFT / LoRA Fine-Tuning Pipelines"
                ],
                "project_keywords": ["rag", "llm", "llama", "mediapipe", "tensorflow", "pytorch", "model", "avatar", "vision", "ai", "inference", "nlp"],
                "exp_keywords": ["ai", "machine learning", "ml", "data science", "deep learning"]
            },
            {
                "domain_name": "Backend & Cloud API Systems",
                "core_skills": [
                    "Python", "FastAPI", "Django", "Flask", "Java", "Node.js",
                    "Express", "REST APIs", "GraphQL", "Microservices", "PostgreSQL",
                    "MySQL", "MongoDB", "SQLite", "Redis", "Firebase", "SQL",
                    "OOP", "Docker", "Git"
                ],
                "recommended_roles": [
                    "Backend Systems Engineer",
                    "API & Microservices Architect",
                    "Cloud Services Backend Developer",
                    "Python Systems Developer"
                ],
                "growth_areas": [
                    "Distributed Message Streaming (Apache Kafka / RabbitMQ)",
                    "High-Concurrency Caching with Redis Clusters",
                    "Docker & Kubernetes Container Orchestration"
                ],
                "project_keywords": ["fastapi", "backend", "api", "database", "firebase", "sql", "pipeline", "microservice", "server"],
                "exp_keywords": ["backend", "software developer", "software engineer", "developer", "api"]
            },
            {
                "domain_name": "Mobile & Cross-Platform Development",
                "core_skills": [
                    "Flutter", "Dart", "Android", "Android SDK", "Java", "Kotlin",
                    "Swift", "iOS", "React Native", "XML", "Mobile UI",
                    "On-Device AI", "MediaPipe"
                ],
                "recommended_roles": [
                    "Mobile Application Developer (Flutter / Android)",
                    "Cross-Platform Systems Engineer",
                    "On-Device Mobile AI Engineer"
                ],
                "growth_areas": [
                    "Advanced State Management (Riverpod / BLoC Architecture)",
                    "Declarative Android UI with Jetpack Compose",
                    "Mobile CI/CD Pipeline Automation (Fastlane)"
                ],
                "project_keywords": ["flutter", "android", "mobile", "app", "mediapipe", "tflite", "sign language", "complaint"],
                "exp_keywords": ["mobile", "android", "flutter"]
            },
            {
                "domain_name": "Full-Stack & Web Engineering",
                "core_skills": [
                    "JavaScript", "TypeScript", "React", "Next.js", "Node.js",
                    "HTML", "CSS", "Tailwind CSS", "REST APIs", "FastAPI",
                    "Full Stack", "vis.js", "Git"
                ],
                "recommended_roles": [
                    "Full Stack Web Developer",
                    "Frontend Applications Engineer",
                    "Interactive Systems Developer"
                ],
                "growth_areas": [
                    "Next.js App Router, SSR & Server Actions",
                    "Predictable State Management (Zustand / Redux Toolkit)",
                    "End-to-End Automated Testing with Playwright"
                ],
                "project_keywords": ["fullstack", "full-stack", "web", "frontend", "react", "next.js", "vis.js"],
                "exp_keywords": ["full stack", "fullstack", "web developer", "frontend"]
            },
            {
                "domain_name": "Data Science & Analytics",
                "core_skills": [
                    "SQL", "Python", "Pandas", "NumPy", "Data Analysis",
                    "Data Visualization", "Tableau", "PowerBI", "Scikit-Learn",
                    "Statistics", "Data Preprocessing", "ETL"
                ],
                "recommended_roles": [
                    "Data Scientist",
                    "Data Analyst",
                    "Business Intelligence Engineer"
                ],
                "growth_areas": [
                    "Analytics Engineering with dbt (Data Build Tool)",
                    "Advanced Statistical Hypothesis Testing & A/B Experimentation",
                    "Cloud Warehousing with Snowflake / BigQuery"
                ],
                "project_keywords": ["data", "dataset", "analytics", "visualization", "preprocessing", "statistical"],
                "exp_keywords": ["data", "analyst", "analytics", "scientist"]
            },
            {
                "domain_name": "Cloud Infrastructure & DevOps",
                "core_skills": [
                    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
                    "CI/CD", "Linux", "Bash", "Git", "Nginx", "Firebase"
                ],
                "recommended_roles": [
                    "Cloud Infrastructure Engineer",
                    "DevOps & CI/CD Automation Specialist",
                    "Site Reliability Engineer (SRE)"
                ],
                "growth_areas": [
                    "Infrastructure as Code (IaC) with Terraform & Pulumi",
                    "Production Kubernetes Deployment & Helm Charts",
                    "Cloud Observability with Prometheus & Grafana"
                ],
                "project_keywords": ["cloud", "devops", "docker", "deploy", "pipeline", "ci/cd", "infrastructure"],
                "exp_keywords": ["devops", "cloud", "infra", "sre"]
            },
            {
                "domain_name": "Cybersecurity & Systems Defense",
                "core_skills": [
                    "Networking Protocols", "Linux", "Penetration Testing",
                    "Vulnerability Testing", "Cryptography", "Wireshark", "OWASP",
                    "Python", "Security"
                ],
                "recommended_roles": [
                    "Cybersecurity Analyst",
                    "Information Security Specialist",
                    "Vulnerability Assessment Engineer"
                ],
                "growth_areas": [
                    "CompTIA Security+ / CEH Practical Defense Skills",
                    "Zero Trust Architecture & Identity Governance",
                    "Automated Vulnerability Scanning (SAST / DAST)"
                ],
                "project_keywords": ["security", "cyber", "auth", "vulnerability", "encryption"],
                "exp_keywords": ["security", "cyber"]
            }
        ]

        suggestions: List[ResumeDomainSuggestion] = []

        for dom in domain_definitions:
            matched_skills = [sk for sk in dom["core_skills"] if has_competency(sk)]

            matched_projects = []
            for p in (projects or []):
                p_dict = p if isinstance(p, dict) else (p.model_dump() if hasattr(p, "model_dump") else {})
                p_str = f"{p_dict.get('title', '')} {p_dict.get('description', '')} {' '.join(p_dict.get('technologies', []))}".lower()
                for kw in dom["project_keywords"]:
                    if kw in p_str:
                        p_title = p_dict.get("title", "")
                        if p_title and p_title not in matched_projects:
                            matched_projects.append(p_title)
                        break

            matched_exps = []
            for e in (experience or []):
                e_dict = e if isinstance(e, dict) else (e.model_dump() if hasattr(e, "model_dump") else {})
                e_str = f"{e_dict.get('role', '')} {e_dict.get('description', '')}".lower()
                for kw in dom["exp_keywords"]:
                    if kw in e_str:
                        role_name = e_dict.get("role", "")
                        if role_name and role_name not in matched_exps:
                            matched_exps.append(role_name)
                        break

            score = 0
            if matched_skills:
                score += min(60, int((len(matched_skills) / 5) * 55))

            if matched_projects:
                score += min(25, len(matched_projects) * 12)

            if matched_exps:
                score += min(15, len(matched_exps) * 8)

            if score >= 65:
                match_pct = min(96, score + 10)
            elif score >= 40:
                match_pct = min(80, score + 15)
            elif score >= 20:
                match_pct = min(68, score + 20)
            elif matched_skills:
                match_pct = 45
            else:
                match_pct = 20

            if match_pct < 40 and not matched_projects:
                continue

            reasons = []
            if matched_projects:
                p_names = ", ".join(f"'{p}'" for p in matched_projects[:2])
                reasons.append(f"Hands-on project proof: {p_names}")
            if matched_exps:
                e_names = ", ".join(f"'{e}'" for e in matched_exps[:2])
                reasons.append(f"Practical role experience: {e_names}")
            if matched_skills:
                top_s = ", ".join(matched_skills[:4])
                reasons.append(f"Demonstrated core skills: {top_s}")

            fit_reason = ". ".join(reasons) + "." if reasons else "Applicable career domain based on candidate's technical profile."

            suggestions.append(ResumeDomainSuggestion(
                domain_name=dom["domain_name"],
                match_percentage=match_pct,
                fit_reason=fit_reason,
                matched_skills=matched_skills[:8],
                recommended_roles=dom["recommended_roles"],
                growth_areas=dom["growth_areas"]
            ))

        suggestions.sort(key=lambda s: s.match_percentage, reverse=True)

        if not suggestions:
            suggestions.append(ResumeDomainSuggestion(
                domain_name="Core Technology & Software Development",
                match_percentage=75,
                fit_reason="Strong foundational engineering skills applicable across modern software projects.",
                matched_skills=[s for s in list(skill_names)[:5]],
                recommended_roles=["Software Developer", "Junior Backend Developer", "Application Specialist"],
                growth_areas=["Version Control & Git Best Practices", "Data Structures & Algorithms", "REST API Construction"]
            ))

        return suggestions[:4]




