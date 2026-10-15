import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.career_catalog import CareerRole
from app.models.profile import UserProfile
from app.schemas.resume import TargetCareerMatchSchema
from app.services.skill.normalizer import SkillNormalizer, SKILL_ALIASES


class TargetCareerMatcher:
    """Engine matching parsed resume data against selected Career Discovery Target Role or specific Job Description."""

    def check_skill_match(self, target_skill: str, candidate_skills: List[str]) -> bool:
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
            if re.search(r'\b' + re.escape(tgt_clean) + r'\b', c_clean):
                return True
            if re.search(r'\b' + re.escape(c_clean) + r'\b', tgt_clean):
                return True
        return False

    async def match_resume_to_target(
        self,
        db: AsyncSession,
        user_id: str,
        resume_skills: List[str],
        job_description: Optional[str] = None,
        override_role_title: Optional[str] = None
    ) -> TargetCareerMatchSchema:
        # 1. Specific Job Description Matching
        if job_description and len(job_description.strip()) >= 20:
            from app.services.resume.ats_engine import ATSEngine
            engine = ATSEngine()
            req_skills, pref_skills, _ = engine._extract_jd_skills_and_keywords(job_description)
            if not req_skills:
                req_skills = ["Python", "JavaScript", "SQL", "Git"]

            matching_req = [req for req in req_skills if self.check_skill_match(req, resume_skills)]
            missing_req = [req for req in req_skills if req not in matching_req]

            matching_pref = [p for p in pref_skills if self.check_skill_match(p, resume_skills)]
            missing_pref = [p for p in pref_skills if p not in matching_pref]

            total_req = len(req_skills)
            pct = int(round((len(matching_req) / total_req) * 100)) if total_req > 0 else 0
            pct = min(100, max(0, pct))

            return TargetCareerMatchSchema(
                target_career_name="Specific Job Description Vacancy",
                match_percentage=pct,
                matching_skills=matching_req,
                missing_skills=missing_req,
                experience_alignment=f"Matched {len(matching_req)}/{total_req} required skills against uploaded job vacancy.",
                recommendation=f"Prioritize acquiring missing job requirements: {', '.join(missing_req[:3]) if missing_req else 'None'}.",
                match_source="job_description",
                preferred_skills_matching=matching_pref,
                preferred_skills_missing=missing_pref
            )

        # 2. Known Career Role Matching (from profile or override)
        target_role_title = override_role_title
        if not target_role_title:
            p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
            p_res = await db.execute(p_stmt)
            user_profile = p_res.scalars().first()
            if user_profile and user_profile.target_career and user_profile.target_career.strip():
                target_role_title = user_profile.target_career.strip()

        # 3. Mode B: No target role selected
        if not target_role_title or target_role_title.lower() in ["none", "null", "undefined"]:
            return TargetCareerMatchSchema(
                target_career_name="None Selected (General Mode)",
                match_percentage=0,
                matching_skills=[],
                missing_skills=[],
                experience_alignment="General resume evaluation mode active. No target career specified.",
                recommendation="Select a target career from Career Discovery or paste a job description to see role-specific matching.",
                match_source="none",
                preferred_skills_matching=[],
                preferred_skills_missing=[]
            )

        # Fetch CareerRole catalog requirements
        c_stmt = select(CareerRole).where(CareerRole.title == target_role_title)
        c_res = await db.execute(c_stmt)
        catalog_role = c_res.scalars().first()

        if not catalog_role:
            c_stmt = select(CareerRole).where(CareerRole.slug.ilike(f"%{target_role_title.lower().replace(' ', '-')}%"))
            c_res = await db.execute(c_stmt)
            catalog_role = c_res.scalars().first()

        required_skills = catalog_role.required_skills if catalog_role else ["Python", "JavaScript", "SQL", "Git"]
        preferred_skills = (catalog_role.important_skills or catalog_role.optional_skills) if catalog_role else ["Docker", "AWS", "CI/CD"]

        matching_req = [req for req in required_skills if self.check_skill_match(req, resume_skills)]
        missing_req = [req for req in required_skills if req not in matching_req]

        matching_pref = [p for p in preferred_skills if self.check_skill_match(p, resume_skills)]
        missing_pref = [p for p in preferred_skills if p not in matching_pref]

        total_req = len(required_skills) if required_skills else 1
        pct = int(round((len(matching_req) / total_req) * 100))
        pct = min(100, max(0, pct))

        alignment_msg = (
            f"Strong technical overlap with {len(matching_req)}/{total_req} key {target_role_title} requirements."
            if pct >= 70 else
            f"Moderate skill overlap for {target_role_title} ({len(matching_req)}/{total_req} skills matched)."
            if pct > 0 else
            f"No matching technical skills found for {target_role_title} requirements."
        )

        recommendation_msg = (
            f"Target role is set to '{target_role_title}'. Focus on closing missing gaps: {', '.join(missing_req[:3]) if missing_req else 'None'}."
        )

        return TargetCareerMatchSchema(
            target_career_name=target_role_title,
            match_percentage=pct,
            matching_skills=matching_req,
            missing_skills=missing_req,
            experience_alignment=alignment_msg,
            recommendation=recommendation_msg,
            match_source="catalog",
            preferred_skills_matching=matching_pref,
            preferred_skills_missing=missing_pref
        )
