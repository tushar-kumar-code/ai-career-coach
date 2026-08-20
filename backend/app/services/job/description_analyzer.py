import re
import logging
from typing import List, Dict, Any
from app.services.skill.normalizer import SkillNormalizer

logger = logging.getLogger(__name__)


class JobDescriptionAnalyzer:
    """Service parsing raw job descriptions into structured skill requirements and metadata."""

    def __init__(self):
        self.normalizer = SkillNormalizer()

    def analyze_description(self, description_text: str) -> Dict[str, Any]:
        """Extract required skills, preferred skills, experience level, and education from text."""
        if not description_text:
            return {
                "required_skills": [],
                "preferred_skills": [],
                "experience_level": "Mid Level",
                "education_requirements": "Bachelor's degree or equivalent experience"
            }

        # 1. Normalize skill terms present in description
        extracted_required: List[str] = []
        extracted_preferred: List[str] = []

        # Check catalog skills against text
        for raw_term, canonical in self.normalizer.synonyms.items():
            pattern = r'\b' + re.escape(raw_term) + r'\b'
            if re.search(pattern, description_text, re.IGNORECASE):
                if canonical not in extracted_required:
                    extracted_required.append(canonical)

        # 2. Extract experience level
        exp_level = "Mid Level"
        if re.search(r'\bsenior\b|\blead\b|\bprincipal\b|\b5\+\s*years?\b', description_text, re.IGNORECASE):
            exp_level = "Senior Level"
        elif re.search(r'\bjunior\b|\bentry\b|\bintern\b|\b0-2\s*years?\b', description_text, re.IGNORECASE):
            exp_level = "Entry Level"

        # 3. Extract education requirements
        edu_req = "Bachelor's degree or equivalent experience"
        if re.search(r'\bmaster|\bm\.s\b|\bphd\b', description_text, re.IGNORECASE):
            edu_req = "Master's or Advanced Degree"

        return {
            "required_skills": extracted_required,
            "preferred_skills": extracted_preferred,
            "experience_level": exp_level,
            "education_requirements": edu_req
        }
