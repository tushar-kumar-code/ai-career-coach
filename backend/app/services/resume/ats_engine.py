import re
from typing import Dict, Any, List, Tuple
from app.schemas.resume import ATSBreakdownSchema


class ATSEngine:
    """Algorithmic ATS scoring engine computing real sub-scores and formatting risk flags."""

    def evaluate_resume(self, parsed_data: Dict[str, Any], raw_text: str) -> Tuple[ATSBreakdownSchema, List[str]]:
        contact = parsed_data.get("contact_info", {})
        skills = parsed_data.get("skills", [])
        experience = parsed_data.get("experience", [])
        education = parsed_data.get("education", [])
        projects = parsed_data.get("projects", [])
        summary = parsed_data.get("summary", "")

        risk_flags: List[str] = []

        # 1. Formatting Score (max 100)
        fmt_score = 100
        if not contact.get("email"):
            fmt_score -= 20
            risk_flags.append("Missing contact email address.")
        if not contact.get("phone"):
            fmt_score -= 10
            risk_flags.append("Missing contact phone number.")
        if not contact.get("linkedin"):
            fmt_score -= 10
            risk_flags.append("Missing LinkedIn profile URL.")
        if not education:
            fmt_score -= 20
            risk_flags.append("Missing standard Education section header.")
        if not experience and not projects:
            fmt_score -= 25
            risk_flags.append("Missing Work Experience or Projects section.")

        fmt_score = max(30, fmt_score)

        # 2. Skills Score (max 100)
        skill_count = len(skills)
        if skill_count >= 10:
            skills_score = 95
        elif skill_count >= 6:
            skills_score = 82
        elif skill_count >= 3:
            skills_score = 68
        else:
            skills_score = 45
            risk_flags.append("Low technical skill count detected. Add relevant tools and frameworks.")

        # 3. Experience Score (max 100)
        exp_score = 70
        if len(experience) >= 2 or len(projects) >= 2:
            exp_score = 90
        elif len(experience) >= 1 or len(projects) >= 1:
            exp_score = 78
        else:
            exp_score = 50
            risk_flags.append("Limited experience or project items found.")

        # 4. Keyword Score (max 100)
        # Check for quantitative impact metrics (% numbers, $, x)
        metrics_count = len(re.findall(r'\b\d+(?:%|\+|\s?k|\s?million)?\b', raw_text))
        if metrics_count >= 5:
            keyword_score = 92
        elif metrics_count >= 2:
            keyword_score = 78
        else:
            keyword_score = 62
            risk_flags.append("Few quantifiable metrics (% increase, latency reduction, user scale) found in experience bullets.")

        # 5. Readability Score (max 100)
        word_count = len(raw_text.split())
        if 250 <= word_count <= 1200:
            readability_score = 90
        elif word_count < 250:
            readability_score = 55
            risk_flags.append("Resume length is very brief (under 250 words).")
        else:
            readability_score = 70
            risk_flags.append("Resume is lengthy (over 1200 words). Ensure content is concise.")

        # Weighted Overall Score
        overall = int(
            (fmt_score * 0.25) +
            (skills_score * 0.25) +
            (exp_score * 0.20) +
            (keyword_score * 0.15) +
            (readability_score * 0.15)
        )

        breakdown = ATSBreakdownSchema(
            overall_ats_score=overall,
            formatting_score=fmt_score,
            keyword_score=keyword_score,
            skills_score=skills_score,
            experience_score=exp_score,
            readability_score=readability_score
        )

        return breakdown, risk_flags
