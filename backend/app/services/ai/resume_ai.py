import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.client import AIService
from app.services.ai.prompts import RESUME_ANALYSIS_SYSTEM_PROMPT
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
    ResumeAnalysisResponse
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

    async def analyze_resume_text(
        self,
        db: AsyncSession,
        user_id: str,
        resume_id: str,
        filename: str,
        raw_text: str
    ) -> ResumeAnalysisResponse:
        # 1. Parse structured section content
        parsed = self.parser.parse(raw_text)

        # 2. Algorithmic ATS Evaluation & Risk Identification
        ats_breakdown, risk_flags = self.ats_engine.evaluate_resume(parsed, raw_text)

        # 3. Target Career Overlap Match against user's selected Target Role
        target_match = await self.target_matcher.match_resume_to_target(
            db, user_id, parsed.get("skills", [])
        )

        # 4. Generate Bullet Point Improvements
        improvements = self.improver.generate_improvements(
            parsed, target_match.missing_skills
        )

        # 5. Build Extracted Skills list with confidence signals
        extracted_skills = [
            ExtractedSkillSchema(
                name=sk,
                category="Technical",
                proficiency_estimated=80 if sk in target_match.matching_skills else 65,
                source="Resume Extraction",
                confidence_level="High" if sk in target_match.matching_skills else "Medium"
            )
            for sk in parsed.get("skills", [])
        ]

        contact = ParsedContactInfo(**parsed.get("contact_info", {}))

        return ResumeAnalysisResponse(
            id=resume_id,
            filename=filename,
            ats_score=ats_breakdown.overall_ats_score,
            ats_breakdown=ats_breakdown,
            target_match=target_match,
            contact_info=contact,
            extracted_skills=extracted_skills,
            formatting_risk_flags=risk_flags,
            improvement_suggestions=improvements
        )
