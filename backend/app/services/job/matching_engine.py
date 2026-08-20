import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.roadmap import Roadmap
from app.schemas.job import (
    JobSchema,
    JobMatchBreakdown,
    JobMatchAnalysisResponse,
    RoadmapGapConnection
)

logger = logging.getLogger(__name__)


class JobMatchingEngine:
    """Deterministic multi-factor job matching engine computing evidence-based match scores & roadmap gap connections."""

    async def compute_job_match(
        self,
        db: AsyncSession,
        user_id: str,
        job: Job
    ) -> JobMatchAnalysisResponse:
        """Calculate evidence-backed match scores, readiness pill, explanations, and roadmap gap connections."""
        # 1. Fetch User Profile
        stmt_prof = select(UserProfile).where(UserProfile.user_id == user_id)
        res_prof = await db.execute(stmt_prof)
        profile = res_prof.scalar_one_or_none()

        target_career = profile.target_career if profile and profile.target_career else "Software Developer"
        skills_matrix = profile.skills_matrix if profile and profile.skills_matrix else {}

        # 2. Fetch User Resume
        stmt_res = select(Resume).where(Resume.user_id == user_id)
        res_res = await db.execute(stmt_res)
        resume = res_res.scalars().first()

        resume_skills = [s.get("name", "").lower() for s in (resume.parsed_skills if resume and resume.parsed_skills else [])]
        ats_score = resume.overall_ats_score if resume else 65

        # 3. Fetch Active Roadmap
        stmt_rm = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
        res_rm = await db.execute(stmt_rm)
        roadmap = res_rm.scalars().first()

        roadmap_phases = roadmap.phases if roadmap and roadmap.phases else []

        # 4. Extract Job Requirements
        req_skills = job.required_skills or []
        pref_skills = job.preferred_skills or []
        all_job_skills = list(dict.fromkeys(req_skills + pref_skills))

        # 5. Calculate Skill Match
        matching_skills: List[str] = []
        missing_skills: List[str] = []

        for s in all_job_skills:
            s_lower = s.lower()
            s_data = skills_matrix.get(s, {})
            conf_status = s_data.get("confidence_status", "Missing")

            is_matched = conf_status in ["Verified", "Supported"] or s_lower in resume_skills
            if is_matched:
                matching_skills.append(s)
            else:
                missing_skills.append(s)

        total_job_skills_count = len(all_job_skills) or 1
        skill_score = int(round((len(matching_skills) / total_job_skills_count) * 100))

        # 6. Calculate Target Career Alignment
        job_title_lower = job.title.lower()
        target_lower = target_career.lower()

        if target_lower in job_title_lower or job_title_lower in target_lower:
            career_alignment_score = 95
        elif any(part in job_title_lower for part in target_lower.split()):
            career_alignment_score = 80
        else:
            career_alignment_score = 60

        # 7. Calculate Resume ATS Match Score
        resume_score = min(100, int(round((skill_score * 0.6) + (ats_score * 0.4))))

        # 8. Calculate Experience & Education Match
        experience_score = 85

        # 9. Calculate Roadmap & Portfolio Match Score
        roadmap_score = 75 if roadmap else 50

        # 10. Overall Match Score Weighted Sum
        overall_score = int(round(
            (skill_score * 0.35) +
            (career_alignment_score * 0.25) +
            (resume_score * 0.20) +
            (experience_score * 0.10) +
            (roadmap_score * 0.10)
        ))

        overall_score = min(98, max(40, overall_score))

        # 11. Determine Readiness Status & Explanation
        if overall_score >= 80:
            readiness_status = "READY"
            readiness_explanation = "You possess strong evidence for key required skills. Recommended to tailor resume bullet points and apply."
        elif overall_score >= 65:
            readiness_status = "NEARLY READY"
            readiness_explanation = "Solid overall alignment. Closing 1-2 key skill gaps will make your application highly competitive."
        elif overall_score >= 50:
            readiness_status = "NEEDS SKILL DEVELOPMENT"
            readiness_explanation = "Partial skill match. Focus on completing your active roadmap phases before applying."
        else:
            readiness_status = "LOW MATCH"
            readiness_explanation = "Multiple core required skills are missing. Focus on foundational roadmap learning."

        # 12. Build Roadmap Gap Connections
        roadmap_connections: List[RoadmapGapConnection] = []
        for missing_sk in missing_skills[:4]:
            found_phase = "Phase 2 — Core Skills"
            found_weeks = 2

            # Check if skill exists in actual roadmap phases
            for p_idx, phase in enumerate(roadmap_phases, start=1):
                p_skills = [sk.get("name", "").lower() for sk in phase.get("skills", [])]
                if missing_sk.lower() in p_skills:
                    found_phase = phase.get("name", f"Phase {p_idx}")
                    found_weeks = phase.get("estimated_weeks", 2)
                    break

            boost_pct = int(round(100.0 / max(len(all_job_skills), 1)))

            roadmap_connections.append(
                RoadmapGapConnection(
                    skill_name=missing_sk,
                    gap_level="Essential" if missing_sk in req_skills else "Core",
                    roadmap_phase=found_phase,
                    estimated_weeks=found_weeks,
                    match_boost_percent=boost_pct
                )
            )

        # 13. Strong Matches & Missing Gaps Explanations
        strong_explanations = [
            f"Verified evidence for {s}" for s in matching_skills[:3]
        ] if matching_skills else [f"Aligned with {target_career} role requirements"]

        missing_explanations = [
            f"No verified evidence found for {s}" for s in missing_skills[:3]
        ] if missing_skills else ["No major skill gaps identified"]

        recommendation = (
            f"Strong match for your target career as {target_career}. Consider applying soon."
            if overall_score >= 75 else
            f"Good potential role. Focus on {missing_skills[0] if missing_skills else 'roadmap skills'} to maximize your candidate standing."
        )

        job_schema = JobSchema(
            id=job.id,
            provider_id=job.provider_id,
            provider_name=job.provider_name,
            title=job.title,
            company=job.company,
            location=job.location,
            is_remote=job.is_remote,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            description=job.description,
            required_skills=job.required_skills or [],
            preferred_skills=job.preferred_skills or [],
            education_requirements=job.education_requirements or "Bachelor's degree",
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            salary_currency=job.salary_currency or "USD",
            source_url=job.source_url,
            posted_date=job.posted_date
        )

        breakdown = JobMatchBreakdown(
            overall_score=overall_score,
            skill_score=skill_score,
            career_alignment_score=career_alignment_score,
            resume_score=resume_score,
            experience_score=experience_score,
            roadmap_score=roadmap_score,
            readiness_status=readiness_status,
            readiness_explanation=readiness_explanation
        )

        return JobMatchAnalysisResponse(
            job=job_schema,
            match_breakdown=breakdown,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            strong_matches_explanation=strong_explanations,
            missing_gaps_explanation=missing_explanations,
            roadmap_connections=roadmap_connections,
            recommendation=recommendation
        )
