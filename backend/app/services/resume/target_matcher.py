from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.career_catalog import CareerRole
from app.models.profile import UserProfile
from app.schemas.resume import TargetCareerMatchSchema


class TargetCareerMatcher:
    """Engine matching parsed resume data against user's selected Career Discovery Target Role."""

    async def match_resume_to_target(
        self,
        db: AsyncSession,
        user_id: str,
        resume_skills: List[str]
    ) -> TargetCareerMatchSchema:
        # Fetch user's target career from UserProfile
        p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        p_res = await db.execute(p_stmt)
        user_profile = p_res.scalars().first()

        target_role_title = user_profile.target_career if (user_profile and user_profile.target_career) else "Software Developer"

        # Fetch CareerRole catalog requirements
        c_stmt = select(CareerRole).where(CareerRole.title == target_role_title)
        c_res = await db.execute(c_stmt)
        catalog_role = c_res.scalars().first()

        if not catalog_role:
            # Fallback search by slug substring
            c_stmt = select(CareerRole).where(CareerRole.slug.ilike(f"%{target_role_title.lower().replace(' ', '-')}%"))
            c_res = await db.execute(c_stmt)
            catalog_role = c_res.scalars().first()

        required_skills = catalog_role.required_skills if catalog_role else ["Python", "JavaScript", "SQL", "Git"]

        # Calculate matching vs missing skills
        resume_skills_lower = {s.lower() for s in resume_skills}
        matching = []
        missing = []

        for req in required_skills:
            if req.lower() in resume_skills_lower or any(req.lower() in s for s in resume_skills_lower):
                matching.append(req)
            else:
                missing.append(req)

        # Calculate match percentage
        total_req = len(required_skills) if required_skills else 1
        pct = int((len(matching) / total_req) * 45 + 50)
        pct = min(95, max(45, pct))

        alignment_msg = (
            f"Strong technical overlap with {len(matching)} key {target_role_title} requirements."
            if pct >= 75 else
            f"Moderate skill overlap for {target_role_title}. Recommended to add missing keywords."
        )

        recommendation_msg = (
            f"Target role is set to '{target_role_title}'. Focus on closing missing gaps: {', '.join(missing[:3]) if missing else 'None'}."
        )

        return TargetCareerMatchSchema(
            target_career_name=target_role_title,
            match_percentage=pct,
            matching_skills=matching,
            missing_skills=missing,
            experience_alignment=alignment_msg,
            recommendation=recommendation_msg
        )
