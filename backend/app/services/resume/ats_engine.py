import re
from typing import Dict, Any, List, Tuple, Optional
from app.schemas.resume import ATSBreakdownSchema, ScoringFactorItem, EligibilityItem
from app.services.skill.normalizer import SkillNormalizer, SKILL_ALIASES


class ATSEngine:
    """
    Algorithmic ATS scoring engine computing explainable factor contributions
    for both Mode A (Role/JD Specific Match) and Mode B (General Resume Quality).
    """

    def _match_skill(self, target_skill: str, candidate_skills: List[str]) -> bool:
        """Check if candidate skills contain target skill via exact, alias, or token matching."""
        if not target_skill or not candidate_skills:
            return False
        tgt_clean = target_skill.strip().lower()
        tgt_norm = SkillNormalizer.normalize(target_skill).lower()

        for c_skill in candidate_skills:
            if not c_skill:
                continue
            c_clean = c_skill.strip().lower()
            c_norm = SkillNormalizer.normalize(c_skill).lower()

            if tgt_clean == c_clean or tgt_norm == c_norm:
                return True
            # Substring / boundary matching (e.g. "python basic" contains "python")
            if re.search(r'\b' + re.escape(tgt_clean) + r'\b', c_clean):
                return True
            if re.search(r'\b' + re.escape(c_clean) + r'\b', tgt_clean):
                return True
        return False

    def _extract_jd_skills_and_keywords(self, jd_text: str) -> Tuple[List[str], List[str], List[str]]:
        """Extract required skills, preferred skills, and responsibility keywords from a job description."""
        required_skills: List[str] = []
        preferred_skills: List[str] = []
        keywords: List[str] = []

        lines = jd_text.splitlines()
        current_section = "required"  # "required" or "preferred"

        for line in lines:
            line_lower = line.strip().lower()
            if any(h in line_lower for h in ["nice to have", "preferred", "bonus", "plus", "good to have", "desired"]):
                current_section = "preferred"
                continue
            elif any(h in line_lower for h in ["requirement", "must have", "qualifications", "required skills", "what you need", "responsibilities"]):
                current_section = "required"
                continue

            # Look for tech skills from catalog aliases
            for alias, canonical in SKILL_ALIASES.items():
                if re.search(r'\b' + re.escape(alias) + r'\b', line_lower):
                    target_list = preferred_skills if current_section == "preferred" else required_skills
                    if canonical not in required_skills and canonical not in preferred_skills:
                        target_list.append(canonical)

        # Domain responsibility keywords
        domain_vocab = [
            "api", "architecture", "microservices", "database", "sql", "testing",
            "ci/cd", "deployment", "cloud", "agile", "scrum", "performance",
            "optimization", "security", "collaboration", "leadership", "scale",
            "frontend", "backend", "full-stack", "analytics", "pipeline", "docker"
        ]
        jd_lower = jd_text.lower()
        for kw in domain_vocab:
            if re.search(r'\b' + re.escape(kw) + r'\b', jd_lower):
                keywords.append(kw.capitalize())

        # Deduplicate while preserving order
        req_clean = list(dict.fromkeys(required_skills))[:12]
        pref_clean = list(dict.fromkeys(preferred_skills))[:8]
        kw_clean = list(dict.fromkeys(keywords))[:10]

        return req_clean, pref_clean, kw_clean

    def evaluate_resume(
        self,
        parsed_data: Optional[Dict[str, Any]] = None,
        raw_text: str = "",
        target_role: Optional[Any] = None,
        job_description: Optional[str] = None,
        target_role_title: Optional[str] = None,
        catalog_skills: Optional[List[str]] = None,
        parsed_resume: Optional[Dict[str, Any]] = None
    ) -> Tuple[ATSBreakdownSchema, List[str]]:
        if parsed_data is None:
            parsed_data = parsed_resume or {}

        contact = parsed_data.get("contact_info", {})
        skills = parsed_data.get("skills", [])
        experience = parsed_data.get("experience", [])
        education = parsed_data.get("education", [])
        projects = parsed_data.get("projects", [])
        summary = parsed_data.get("summary", "")

        risk_flags: List[str] = []
        missing_data_notes: List[str] = []

        # Determine Fresher / Student status
        is_fresher = len(experience) == 0 and (len(projects) > 0 or len(education) > 0)
        # Check graduation years in education text
        edu_text_combined = " ".join(
            (ed.get("degree", "") + " " + ed.get("institution", "") + " " + ed.get("end_year", "") + " " + ed.get("grade", ""))
            for ed in education if isinstance(ed, dict)
        ).lower()
        if re.search(r'\b202[4-9]\b', edu_text_combined):
            is_fresher = True

        # Determine Active Mode:
        # Mode A: specific job description OR known target career role
        # Mode B: general resume quality (target role is unknown)
        is_jd_mode = bool(job_description and len(job_description.strip()) >= 20)
        
        # Normalize target_role if passed as string
        role_title_str = target_role_title
        if isinstance(target_role, str) and target_role.strip():
            role_title_str = target_role.strip()
            target_role = None

        has_target_role = bool(
            target_role is not None or
            (role_title_str and role_title_str.strip() and role_title_str.lower() not in ["none", "null", "undefined"])
        )

        if is_jd_mode:
            return self._evaluate_mode_a(
                parsed_data=parsed_data,
                raw_text=raw_text,
                is_fresher=is_fresher,
                is_jd=True,
                job_description=job_description,
                target_role=target_role,
                target_role_title=role_title_str or "Target Job Description / Vacancy",
                catalog_skills=catalog_skills
            )
        elif has_target_role:
            role_name = getattr(target_role, "title", None) or role_title_str or "Target Role"
            return self._evaluate_mode_a(
                parsed_data=parsed_data,
                raw_text=raw_text,
                is_fresher=is_fresher,
                is_jd=False,
                job_description=None,
                target_role=target_role,
                target_role_title=role_name,
                catalog_skills=catalog_skills
            )
        else:
            return self._evaluate_mode_b(
                parsed_data=parsed_data,
                raw_text=raw_text,
                is_fresher=is_fresher
            )

    # --------------------------------------------------------------------------
    # MODE A: TARGET JOB ROLE OR SPECIFIC JOB DESCRIPTION
    # --------------------------------------------------------------------------
    def _evaluate_mode_a(
        self,
        parsed_data: Dict[str, Any],
        raw_text: str,
        is_fresher: bool,
        is_jd: bool,
        job_description: Optional[str],
        target_role: Optional[Any],
        target_role_title: str,
        catalog_skills: Optional[List[str]] = None
    ) -> Tuple[ATSBreakdownSchema, List[str]]:
        contact = parsed_data.get("contact_info", {})
        skills = parsed_data.get("skills", [])
        experience = parsed_data.get("experience", [])
        education = parsed_data.get("education", [])
        projects = parsed_data.get("projects", [])
        summary = parsed_data.get("summary", "")

        risk_flags: List[str] = []
        missing_data_notes: List[str] = []
        factors: List[ScoringFactorItem] = []
        eligibility: List[EligibilityItem] = []

        # 1. Determine Target Requirements
        required_skills: List[str] = []
        preferred_skills: List[str] = []
        target_responsibilities: List[str] = []

        if is_jd and job_description:
            req_jd, pref_jd, kw_jd = self._extract_jd_skills_and_keywords(job_description)
            required_skills = req_jd if req_jd else ["Python", "JavaScript", "SQL", "Git"]
            preferred_skills = pref_jd
            target_responsibilities = kw_jd if kw_jd else ["API Development", "Database Management", "System Architecture"]
            mode_label = "Specific Job Description Match"
            target_context = "Matched against provided job description vacancy requirements."
        else:
            if target_role:
                required_skills = getattr(target_role, "required_skills", []) or ["Python", "JavaScript", "SQL", "Git"]
                preferred_skills = getattr(target_role, "important_skills", []) or getattr(target_role, "optional_skills", [])
                target_responsibilities = getattr(target_role, "responsibilities", []) or []
            elif catalog_skills:
                required_skills = catalog_skills
                preferred_skills = ["Docker", "AWS", "CI/CD"]
                target_responsibilities = ["Software Development", "API Design", "Database Querying", "Code Review"]
            else:
                required_skills = ["Python", "JavaScript", "SQL", "Git"]
                preferred_skills = ["Docker", "AWS", "CI/CD"]
                target_responsibilities = ["Software Development", "System Architecture"]
            mode_label = f"Role Match: {target_role_title} (Career Catalog)"
            target_context = f"Matched against standardized {target_role_title} industry expectations from role catalog."

        # Compute skill matches
        matched_required = [req for req in required_skills if self._match_skill(req, skills)]
        missing_required = [req for req in required_skills if req not in matched_required]
        matched_preferred = [pref for pref in preferred_skills if self._match_skill(pref, skills)]
        missing_preferred = [pref for pref in preferred_skills if pref not in matched_preferred]

        # Check project and experience evidence of matching skills
        proj_exp_text = ""
        for p in projects:
            if isinstance(p, dict):
                proj_exp_text += " " + p.get("title", "") + " " + p.get("description", "") + " " + " ".join(p.get("technologies", []))
        for exp in experience:
            if isinstance(exp, dict):
                proj_exp_text += " " + exp.get("role", "") + " " + exp.get("description", "") + " " + " ".join(exp.get("key_achievements", []))
        proj_exp_lower = proj_exp_text.lower()

        # ----------------------------------------------------------------------
        # Factor 1: Required and Preferred Skill Match (Weight: 35%)
        # ----------------------------------------------------------------------
        weight_1 = 35
        f1_strengths = []
        f1_missing = []

        if required_skills:
            req_ratio = len(matched_required) / len(required_skills)
        else:
            req_ratio = 1.0

        if preferred_skills:
            pref_ratio = len(matched_preferred) / len(preferred_skills)
            score_1 = int(round((req_ratio * 80.0) + (pref_ratio * 20.0)))
        else:
            score_1 = int(round(req_ratio * 100.0))

        # Bonus for skills supported by project/experience evidence
        evidence_supported = sum(1 for sk in matched_required if sk.lower() in proj_exp_lower)
        if evidence_supported >= 2 and score_1 > 0:
            score_1 = min(100, score_1 + 5)

        score_1 = max(0, min(100, score_1))
        f1_contrib = round((score_1 * weight_1) / 100.0, 1)

        if matched_required:
            f1_strengths.append(f"Matched {len(matched_required)}/{len(required_skills)} required skills: {', '.join(matched_required[:4])}")
        if matched_preferred:
            f1_strengths.append(f"Matched {len(matched_preferred)} preferred skills: {', '.join(matched_preferred[:3])}")
        if missing_required:
            f1_missing.append(f"Missing core required skills: {', '.join(missing_required[:4])}")
            risk_flags.append(f"Missing essential {target_role_title} skills: {', '.join(missing_required[:3])}")

        factors.append(ScoringFactorItem(
            factor_name="Required and preferred skill match",
            weight=weight_1,
            factor_score=score_1,
            weighted_contribution=f1_contrib,
            description=f"Evaluates exact and normalized alignment with mandatory and preferred technical skills for {target_role_title}.",
            strengths=f1_strengths,
            missing_evidence=f1_missing,
            status="evaluated"
        ))

        # ----------------------------------------------------------------------
        # Factor 2: Relevant Projects and Practical Experience (Weight: 20%)
        # ----------------------------------------------------------------------
        weight_2 = 20
        f2_strengths = []
        f2_missing = []

        domain_evidence_found = any(sk.lower() in proj_exp_lower for sk in required_skills)
        total_practical_items = len(experience) + len(projects)

        if is_fresher:
            if len(projects) >= 2:
                score_2 = 90 if domain_evidence_found else 80
                f2_strengths.append(f"Strong project portfolio: {len(projects)} hands-on projects evaluated for fresher readiness.")
            elif len(projects) == 1:
                score_2 = 75 if domain_evidence_found else 65
                f2_strengths.append("1 hands-on project demonstrated.")
                f2_missing.append("Add a 2nd technical project to demonstrate depth.")
            else:
                score_2 = 30
                f2_missing.append("No technical projects or internship experience found in resume.")
                risk_flags.append("Fresher resume lacks demonstrated practical projects.")
        else:
            if len(experience) >= 2 or total_practical_items >= 3:
                score_2 = 95 if domain_evidence_found else 82
                f2_strengths.append(f"Demonstrated {len(experience)} work roles and {len(projects)} projects.")
            elif len(experience) >= 1 or total_practical_items >= 1:
                score_2 = 80 if domain_evidence_found else 70
                f2_strengths.append(f"Documented {len(experience)} role(s) / {len(projects)} project(s).")
            else:
                score_2 = 25
                f2_missing.append("Limited practical work experience or projects listed.")
                risk_flags.append("Limited work experience or project history found.")

        if domain_evidence_found:
            f2_strengths.append(f"Projects/experience demonstrate direct application of {target_role_title} tools.")
        elif total_practical_items > 0:
            f2_missing.append(f"Experience items do not explicitly mention key {target_role_title} requirements.")

        score_2 = max(0, min(100, score_2))
        f2_contrib = round((score_2 * weight_2) / 100.0, 1)

        factors.append(ScoringFactorItem(
            factor_name="Relevant projects and practical experience",
            weight=weight_2,
            factor_score=score_2,
            weighted_contribution=f2_contrib,
            description="Assesses practical project and work experience relevance without unfairly penalizing students/freshers.",
            strengths=f2_strengths,
            missing_evidence=f2_missing,
            status="evaluated"
        ))

        # ----------------------------------------------------------------------
        # Factor 3: Required Qualifications and Eligibility (Weight: 15%)
        # ----------------------------------------------------------------------
        weight_3 = 15
        f3_strengths = []
        f3_missing = []

        edu_text_combined = " ".join([
            f"{e.get('degree', '')} {e.get('institution', '')} {e.get('field_of_study', '')}"
            for e in education if isinstance(e, dict)
        ]) + " " + raw_text.lower()

        # Criterion 1: Education degree
        has_degree = bool(re.search(r'\b(?:b\.?tech|b\.?e\.?|m\.?tech|m\.?e\.?|bca|mca|b\.?sc|m\.?sc|bachelor|master|degree|diploma)\b', edu_text_combined))
        if has_degree:
            eligibility.append(EligibilityItem(
                criterion="Educational Degree Qualification",
                status="MET",
                details="Relevant degree program detected in education history."
            ))
            f3_strengths.append("Verified relevant degree in technical education.")
            deg_score = 100
        elif education:
            eligibility.append(EligibilityItem(
                criterion="Educational Degree Qualification",
                status="MET",
                details="Education history present with completed institutional coursework."
            ))
            deg_score = 85
        else:
            eligibility.append(EligibilityItem(
                criterion="Educational Degree Qualification",
                status="UNKNOWN",
                details="No Education section detected on resume to verify academic qualifications."
            ))
            f3_missing.append("Education section missing or unverifiable.")
            missing_data_notes.append("Educational qualification status could not be verified from resume.")
            deg_score = 45

        # Criterion 2: Verified contact & location identity
        has_email = bool(contact.get("email"))
        has_phone = bool(contact.get("phone"))
        if has_email and has_phone:
            eligibility.append(EligibilityItem(
                criterion="Candidate Contact & Identity Verification",
                status="MET",
                details=f"Email ({contact.get('email')}) and phone verified for candidate outreach."
            ))
            f3_strengths.append("Complete direct contact credentials.")
            contact_score = 100
        else:
            eligibility.append(EligibilityItem(
                criterion="Candidate Contact & Identity Verification",
                status="NOT_MET",
                details="Missing direct contact information (email or phone)."
            ))
            f3_missing.append("Incomplete contact details.")
            contact_score = 40

        # Criterion 3: Core Competency Threshold (at least 1 required skill)
        if len(matched_required) >= max(1, len(required_skills) // 2):
            eligibility.append(EligibilityItem(
                criterion="Core Role Skill Competency Threshold",
                status="MET",
                details=f"Candidate satisfies majority requirement ({len(matched_required)}/{len(required_skills)} required skills)."
            ))
            core_score = 100
        elif len(matched_required) > 0:
            eligibility.append(EligibilityItem(
                criterion="Core Role Skill Competency Threshold",
                status="MET",
                details=f"Candidate meets partial skill baseline ({len(matched_required)} skills)."
            ))
            core_score = 70
        else:
            eligibility.append(EligibilityItem(
                criterion="Core Role Skill Competency Threshold",
                status="NOT_MET",
                details="Zero required target role skills detected."
            ))
            f3_missing.append("Did not meet minimum skill benchmark.")
            core_score = 20

        score_3 = int(round((deg_score * 0.4) + (contact_score * 0.3) + (core_score * 0.3)))
        score_3 = max(0, min(100, score_3))
        f3_contrib = round((score_3 * weight_3) / 100.0, 1)

        factors.append(ScoringFactorItem(
            factor_name="Required qualifications and eligibility",
            weight=weight_3,
            factor_score=score_3,
            weighted_contribution=f3_contrib,
            description="Validates employer baseline requirements (degree, contactability, core competency) without assumptions.",
            strengths=f3_strengths,
            missing_evidence=f3_missing,
            status="evaluated"
        ))

        # ----------------------------------------------------------------------
        # Factor 4: Job-Related Keyword and Responsibility Match (Weight: 10%)
        # ----------------------------------------------------------------------
        weight_4 = 10
        f4_strengths = []
        f4_missing = []

        resume_full_lower = raw_text.lower()
        matched_responsibilities: List[str] = []

        for resp in target_responsibilities:
            resp_words = [w for w in re.split(r'[\s/,-]+', resp.lower()) if len(w) > 3]
            if any(w in resume_full_lower for w in resp_words):
                matched_responsibilities.append(resp)

        kw_count = len(matched_responsibilities)
        if kw_count >= 4:
            score_4 = 95
            f4_strengths.append(f"Strong responsibility alignment across {kw_count} domain areas.")
        elif kw_count >= 2:
            score_4 = 80
            f4_strengths.append(f"Matched {kw_count} job-related responsibility themes.")
        elif kw_count == 1:
            score_4 = 60
            f4_missing.append("Add action verbs reflecting day-to-day role responsibilities.")
        else:
            score_4 = 25
            f4_missing.append("Resume does not reflect key responsibility keywords for this vacancy.")

        score_4 = max(0, min(100, score_4))
        f4_contrib = round((score_4 * weight_4) / 100.0, 1)

        factors.append(ScoringFactorItem(
            factor_name="Job-related keyword and responsibility match",
            weight=weight_4,
            factor_score=score_4,
            weighted_contribution=f4_contrib,
            description="Replaces artificial metric counting with genuine job-related keyword and responsibility matching.",
            strengths=f4_strengths,
            missing_evidence=f4_missing,
            status="evaluated"
        ))

        # ----------------------------------------------------------------------
        # Factor 5: Evidence of Skills and Accomplishments (Weight: 10%)
        # ----------------------------------------------------------------------
        weight_5 = 10
        f5_strengths = []
        f5_missing = []

        # Check for verifiable evidence: links (GitHub, LinkedIn, Portfolio), concrete metrics in bullets
        has_links = bool(contact.get("github") or contact.get("portfolio") or contact.get("linkedin"))
        metrics_found = len(re.findall(r'\b\d+(?:%|\+|\s?k|\s?million|\s?users|\s?ms)?\b', raw_text))

        if has_links and metrics_found >= 2:
            score_5 = 95
            f5_strengths.append("Verified repository/portfolio links and measurable bullet achievements.")
        elif has_links or metrics_found >= 2:
            score_5 = 80
            if has_links:
                f5_strengths.append("Verifiable code repository or professional profile link present.")
            if metrics_found >= 2:
                f5_strengths.append("Quantifiable accomplishment metrics present in descriptions.")
        elif metrics_found == 1:
            score_5 = 65
            f5_missing.append("Add measurable results (e.g. % performance increase, user scale) to project bullets.")
        else:
            score_5 = 40
            f5_missing.append("Skill claims lack links or measurable accomplishment evidence.")

        score_5 = max(0, min(100, score_5))
        f5_contrib = round((score_5 * weight_5) / 100.0, 1)

        factors.append(ScoringFactorItem(
            factor_name="Evidence of skills and accomplishments",
            weight=weight_5,
            factor_score=score_5,
            weighted_contribution=f5_contrib,
            description="Evaluates tangible proof of work (links, project repositories, quantitative deliverables).",
            strengths=f5_strengths,
            missing_evidence=f5_missing,
            status="evaluated"
        ))

        # ----------------------------------------------------------------------
        # Factor 6: Resume Parsing and Formatting Quality (Weight: 10%)
        # ----------------------------------------------------------------------
        weight_6 = 10
        f6_strengths = []
        f6_missing = []

        fmt_score = 100
        if not contact.get("email"):
            fmt_score -= 20
            f6_missing.append("Missing email address.")
        if not contact.get("phone"):
            fmt_score -= 10
            f6_missing.append("Missing phone number.")
        if not education:
            fmt_score -= 20
            f6_missing.append("Missing standard Education section header.")
        if not experience and not projects:
            fmt_score -= 25
            f6_missing.append("Missing Work Experience or Projects section.")

        score_6 = max(30, min(100, fmt_score))
        f6_contrib = round((score_6 * weight_6) / 100.0, 1)

        if score_6 >= 90:
            f6_strengths.append("Clean ATS-friendly document structure and extractable contact sections.")
        elif score_6 >= 70:
            f6_strengths.append("Standard section formatting detected with minor omissions.")

        factors.append(ScoringFactorItem(
            factor_name="Resume parsing and formatting quality",
            weight=weight_6,
            factor_score=score_6,
            weighted_contribution=f6_contrib,
            description="Ensures ATS parsers can seamlessly extract contact information and core sections.",
            strengths=f6_strengths,
            missing_evidence=f6_missing,
            status="evaluated"
        ))

        # Overall Score: Sum of valid weighted contributions
        overall = int(round(sum(f.weighted_contribution for f in factors)))
        overall = max(0, min(100, overall))

        # Readability metric for backward-compatibility
        word_count = len(raw_text.split())
        readability_score = 90 if 200 <= word_count <= 1200 else (60 if word_count < 200 else 70)

        breakdown = ATSBreakdownSchema(
            overall_ats_score=overall,
            formatting_score=score_6,
            keyword_score=score_4,
            skills_score=score_1,
            experience_score=score_2,
            readability_score=readability_score,
            scoring_mode="job_description" if is_jd else "target_role",
            mode_label=mode_label,
            target_context=target_context,
            factors=factors,
            eligibility_criteria=eligibility,
            preferred_skills_matching=matched_preferred,
            preferred_skills_missing=missing_preferred,
            missing_data_notes=missing_data_notes,
            is_fresher_mode=is_fresher
        )

        return breakdown, risk_flags

    # --------------------------------------------------------------------------
    # MODE B: TARGET JOB ROLE IS UNKNOWN (GENERAL RESUME QUALITY)
    # --------------------------------------------------------------------------
    def _evaluate_mode_b(
        self,
        parsed_data: Dict[str, Any],
        raw_text: str,
        is_fresher: bool
    ) -> Tuple[ATSBreakdownSchema, List[str]]:
        contact = parsed_data.get("contact_info", {})
        skills = parsed_data.get("skills", [])
        experience = parsed_data.get("experience", [])
        education = parsed_data.get("education", [])
        projects = parsed_data.get("projects", [])
        summary = parsed_data.get("summary", "")

        risk_flags: List[str] = []
        missing_data_notes: List[str] = []
        factors: List[ScoringFactorItem] = []

        missing_data_notes.append("No specific target job role selected. Resume evaluated for universal ATS readability, section completeness, and presentation.")

        # ----------------------------------------------------------------------
        # Factor 1: Parsing and Formatting Compatibility (Weight: 20%)
        # ----------------------------------------------------------------------
        w1 = 20
        f1_strengths = []
        f1_missing = []
        fmt_compat = 100

        if not contact.get("email"):
            fmt_compat -= 25
            f1_missing.append("Missing email contact.")
            risk_flags.append("Missing contact email address.")
        if not contact.get("phone"):
            fmt_compat -= 15
            f1_missing.append("Missing phone number.")
            risk_flags.append("Missing contact phone number.")
        if not (contact.get("linkedin") or contact.get("github") or contact.get("portfolio")):
            fmt_compat -= 15
            f1_missing.append("No professional web profile or repository URL provided.")

        score_1 = max(35, min(100, fmt_compat))
        if score_1 >= 85:
            f1_strengths.append("Standard contact header with verified direct outreach details.")
        f1_contrib = round((score_1 * w1) / 100.0, 1)

        factors.append(ScoringFactorItem(
            factor_name="Parsing and formatting compatibility",
            weight=w1,
            factor_score=score_1,
            weighted_contribution=f1_contrib,
            description="Evaluates whether ATS systems can extract clean contact and profile identity tokens.",
            strengths=f1_strengths,
            missing_evidence=f1_missing,
            status="evaluated"
        ))

        # ----------------------------------------------------------------------
        # Factor 2: Resume Section Completeness (Weight: 20%)
        # ----------------------------------------------------------------------
        w2 = 20
        f2_strengths = []
        f2_missing = []
        section_pts = 0

        # Header Contact (25 pts)
        if contact.get("name") and (contact.get("email") or contact.get("phone")):
            section_pts += 25
            f2_strengths.append("Contact/Header section detected.")
        else:
            f2_missing.append("Incomplete header section.")

        # Professional Summary (20 pts)
        if summary and len(summary.strip().split()) >= 15:
            section_pts += 20
            f2_strengths.append("Clear professional summary / career objective.")
        else:
            f2_missing.append("Add a concise professional summary highlighting your career direction.")

        # Skills section (25 pts)
        if skills and len(skills) >= 3:
            section_pts += 25
            f2_strengths.append("Dedicated skills section present.")
        elif skills:
            section_pts += 15
            f2_missing.append("Skills section has few items.")
        else:
            f2_missing.append("Missing dedicated Technical Skills section.")

        # Education section (15 pts)
        if education:
            section_pts += 15
            f2_strengths.append("Standard Education history section found.")
        else:
            f2_missing.append("Missing Education section.")

        # Experience or Projects (15 pts)
        if experience or projects:
            section_pts += 15
            f2_strengths.append("Practical experience or projects section verified.")
        else:
            section_pts += 0
            f2_missing.append("Missing both Experience and Projects sections.")

        score_2 = max(0, min(100, section_pts))
        f2_contrib = round((score_2 * w2) / 100.0, 1)

        factors.append(ScoringFactorItem(
            factor_name="Resume section completeness",
            weight=w2,
            factor_score=score_2,
            weighted_contribution=f2_contrib,
            description="Checks presence and structural clarity of standard resume sections.",
            strengths=f2_strengths,
            missing_evidence=f2_missing,
            status="evaluated"
        ))

        # ----------------------------------------------------------------------
        # Factor 3: Documented Skills and Skill Evidence (Weight: 20%)
        # ----------------------------------------------------------------------
        w3 = 20
        f3_strengths = []
        f3_missing = []
        sk_count = len(skills)

        if sk_count >= 8:
            base_sk = 90
            f3_strengths.append(f"Strong skill profile: {sk_count} technical tools and concepts listed.")
        elif sk_count >= 4:
            base_sk = 80
            f3_strengths.append(f"Balanced skill profile: {sk_count} tools identified.")
        elif sk_count >= 2:
            base_sk = 65
            f3_missing.append("Add more core technical skills and libraries you have worked with.")
        else:
            base_sk = 35
            f3_missing.append("Very few skills documented in the skills section.")

        # Evidence bonus: are skills backed by projects or summary?
        proj_exp_text = ""
        for p in projects:
            if isinstance(p, dict):
                proj_exp_text += " " + p.get("title", "") + " " + p.get("description", "") + " " + " ".join(p.get("technologies", []))
        for exp in experience:
            if isinstance(exp, dict):
                proj_exp_text += " " + exp.get("role", "") + " " + exp.get("description", "")
        proj_exp_lower = proj_exp_text.lower()

        evidence_count = sum(1 for s in skills if s.lower() in proj_exp_lower or s.lower() in summary.lower())
        if evidence_count >= 2 and base_sk >= 65:
            base_sk = min(100, base_sk + 10)
            f3_strengths.append(f"{evidence_count} skills supported by project descriptions or summary context.")

        score_3 = max(0, min(100, base_sk))
        f3_contrib = round((score_3 * w3) / 100.0, 1)

        factors.append(ScoringFactorItem(
            factor_name="Documented skills and skill evidence",
            weight=w3,
            factor_score=score_3,
            weighted_contribution=f3_contrib,
            description="Measures technical skills depth and verifies they are substantiated by context rather than stuffed lists.",
            strengths=f3_strengths,
            missing_evidence=f3_missing,
            status="evaluated"
        ))

        # ----------------------------------------------------------------------
        # Factor 4: Projects and Experience Evidence (Weight: 20%)
        # ----------------------------------------------------------------------
        w4 = 20
        f4_strengths = []
        f4_missing = []

        if is_fresher:
            if len(projects) >= 2:
                score_4 = 90
                f4_strengths.append(f"Fresher profile demonstrates {len(projects)} practical projects with technology implementations.")
            elif len(projects) == 1:
                score_4 = 75
                f4_strengths.append("1 technical project demonstrated.")
                f4_missing.append("Add a 2nd project to demonstrate wider technical versatility.")
            else:
                score_4 = 40
                f4_missing.append("No projects or internships listed. Add academic or personal projects.")
                risk_flags.append("No technical projects found in fresher profile.")
        else:
            if len(experience) >= 2 or (len(experience) >= 1 and len(projects) >= 1):
                score_4 = 92
                f4_strengths.append(f"Documented {len(experience)} work roles and {len(projects)} projects.")
            elif len(experience) >= 1 or len(projects) >= 1:
                score_4 = 78
                f4_strengths.append("Practical experience or project documented.")
            else:
                score_4 = 40
                f4_missing.append("Limited practical experience or project items found.")

        score_4 = max(0, min(100, score_4))
        f4_contrib = round((score_4 * w4) / 100.0, 1)

        factors.append(ScoringFactorItem(
            factor_name="Projects and experience evidence",
            weight=w4,
            factor_score=score_4,
            weighted_contribution=f4_contrib,
            description="Evaluates practical ability through projects or work history with fresher-friendly accommodation.",
            strengths=f4_strengths,
            missing_evidence=f4_missing,
            status="evaluated"
        ))

        # ----------------------------------------------------------------------
        # Factor 5: Education and Relevant Certifications (Weight: 10%)
        # ----------------------------------------------------------------------
        w5 = 10
        f5_strengths = []
        f5_missing = []

        if education:
            score_5 = 90
            f5_strengths.append(f"Verified education record ({len(education)} institutional entry/entries).")
        else:
            score_5 = 45
            f5_missing.append("No formal education or training listed.")

        score_5 = max(0, min(100, score_5))
        f5_contrib = round((score_5 * w5) / 100.0, 1)

        factors.append(ScoringFactorItem(
            factor_name="Education and relevant certifications",
            weight=w5,
            factor_score=score_5,
            weighted_contribution=f5_contrib,
            description="Checks presence of verified academic foundations and professional certifications.",
            strengths=f5_strengths,
            missing_evidence=f5_missing,
            status="evaluated"
        ))

        # ----------------------------------------------------------------------
        # Factor 6: Readability and Content Clarity (Weight: 10%)
        # ----------------------------------------------------------------------
        w6 = 10
        f6_strengths = []
        f6_missing = []

        word_count = len(raw_text.split())
        if 150 <= word_count <= 1200:
            score_6 = 92
            f6_strengths.append(f"Optimal resume density ({word_count} words).")
        elif word_count < 150:
            score_6 = 60
            f6_missing.append("Resume content is concise (< 150 words). Add details about your projects and skills.")
        else:
            score_6 = 75
            f6_missing.append("Resume is lengthy (> 1200 words). Ensure descriptions are concise.")

        score_6 = max(0, min(100, score_6))
        f6_contrib = round((score_6 * w6) / 100.0, 1)

        factors.append(ScoringFactorItem(
            factor_name="Readability and content clarity",
            weight=w6,
            factor_score=score_6,
            weighted_contribution=f6_contrib,
            description="Evaluates overall textual density, bullet structure, and readability for automated ATS parsers.",
            strengths=f6_strengths,
            missing_evidence=f6_missing,
            status="evaluated"
        ))

        # Overall Score
        overall = int(round(sum(f.weighted_contribution for f in factors)))
        overall = max(0, min(100, overall))

        breakdown = ATSBreakdownSchema(
            overall_ats_score=overall,
            formatting_score=score_1,
            keyword_score=score_2,
            skills_score=score_3,
            experience_score=score_4,
            readability_score=score_6,
            scoring_mode="general",
            mode_label="General Resume Quality & ATS Readiness",
            target_context="No target career role or job description selected. General profile analysis active.",
            factors=factors,
            eligibility_criteria=[],
            preferred_skills_matching=[],
            preferred_skills_missing=[],
            missing_data_notes=missing_data_notes,
            is_fresher_mode=is_fresher
        )

        return breakdown, risk_flags
