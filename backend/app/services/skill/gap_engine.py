import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.skill import Skill
from app.models.profile import UserProfile
from app.models.career_catalog import CareerRole
from app.schemas.skill import SkillGapSchema, UserSkillSchema
from app.services.skill.normalizer import SkillNormalizer

logger = logging.getLogger(__name__)


class SkillGapEngine:
    """Evaluates User Skill Profile against Target Career Requirements to compute gaps, proficiencies, and learning priorities."""

    async def calculate_skill_gaps(
        self,
        db: AsyncSession,
        user_id: str,
        user_skills: List[Skill]
    ) -> Tuple[str, List[UserSkillSchema], List[UserSkillSchema], List[SkillGapSchema], List[UserSkillSchema]]:
        normalizer = SkillNormalizer()

        # 1. Get Target Career Title from User Profile
        p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        p_res = await db.execute(p_stmt)
        user_profile = p_res.scalars().first()

        target_title = user_profile.target_career if (user_profile and user_profile.target_career) else "Software Developer"

        # 2. Get Target Role catalog requirements
        c_stmt = select(CareerRole).where(CareerRole.title == target_title)
        c_res = await db.execute(c_stmt)
        target_role = c_res.scalars().first()

        if not target_role:
            c_stmt = select(CareerRole).where(CareerRole.slug.ilike(f"%{target_title.lower().replace(' ', '-')}%"))
            c_res = await db.execute(c_stmt)
            target_role = c_res.scalars().first()

        raw_req = target_role.required_skills if (target_role and target_role.required_skills) else ["Python", "JavaScript", "SQL"]
        raw_imp = (target_role.important_skills if (target_role and target_role.important_skills) else (target_role.preferred_strengths if target_role else ["React", "Git"]))
        raw_opt = target_role.optional_skills if (target_role and target_role.optional_skills) else []
        rec_prof_map = target_role.recommended_proficiency if (target_role and target_role.recommended_proficiency) else {}

        required_skills = [normalizer.normalize(s) for s in raw_req if s]
        important_skills = [normalizer.normalize(s) for s in raw_imp if s]
        optional_skills = [normalizer.normalize(s) for s in raw_opt if s]

        # Map user skills by normalized name lower
        user_skill_map: Dict[str, Skill] = {s.normalized_name.lower(): s for s in user_skills}

        strong_skills: List[UserSkillSchema] = []
        skills_to_improve: List[UserSkillSchema] = []
        missing_gaps: List[SkillGapSchema] = []
        recommended_next: List[UserSkillSchema] = []

        # Process user's existing skills
        for sk in user_skills:
            sk_norm = sk.normalized_name
            sk_lower = sk_norm.lower()

            if sk_lower in [r.lower() for r in required_skills]:
                target_req = "Required"
            elif sk_lower in [i.lower() for i in important_skills]:
                target_req = "Important"
            else:
                target_req = "Optional"

            req_level = rec_prof_map.get(sk_norm, rec_prof_map.get(sk_lower, "Intermediate"))

            # Determine gap status & priority based on level & confidence
            if sk.proficiency_percent >= 75 and sk.confidence_score >= 60:
                gap_status = "Matched"
                priority = "Low"
                p_reason = f"Strong proficiency ({sk.proficiency_level}) with {sk.confidence_status} system confidence."
            elif sk.proficiency_percent >= 50:
                gap_status = "Partially Matched"
                priority = "High" if target_req == "Required" else ("Medium" if target_req == "Important" else "Low")
                p_reason = f"Current level is {sk.proficiency_level}; target role '{target_title}' requires {req_level} proficiency."
            else:
                gap_status = "Weak"
                priority = "High" if target_req in ["Required", "Important"] else "Medium"
                p_reason = f"Weak proficiency ({sk.proficiency_level}, {sk.proficiency_percent}%) for core {target_req} skill in {target_title}."

            sk.target_required_level = target_req
            sk.gap_status = gap_status
            sk.priority = priority
            sk.priority_reason = p_reason
            db.add(sk)

            schema_item = UserSkillSchema(
                id=sk.id,
                skill_name=sk.skill_name,
                normalized_name=sk.normalized_name,
                category=sk.category,
                proficiency_percent=sk.proficiency_percent,
                proficiency_level=sk.proficiency_level,
                confidence_score=sk.confidence_score,
                confidence_status=sk.confidence_status,
                target_required_level=target_req,
                gap_status=gap_status,
                priority=priority,
                priority_reason=p_reason,
                evidence_sources=sk.evidence_sources or [],
                last_evaluated_at=sk.last_evaluated_at.isoformat() if sk.last_evaluated_at else None
            )

            if gap_status == "Matched":
                strong_skills.append(schema_item)
            else:
                skills_to_improve.append(schema_item)
                if priority in ["High", "Medium"]:
                    recommended_next.append(schema_item)

        # Identify missing target skills (Required + Important)
        all_target_skills = [(r, "Required") for r in required_skills] + [(i, "Important") for i in important_skills]
        seen_missing = set()

        for req_name, req_type in all_target_skills:
            req_lower = req_name.lower()
            if req_lower not in user_skill_map and req_lower not in seen_missing:
                seen_missing.add(req_lower)
                is_req = (req_type == "Required")
                priority = "High" if is_req else "Medium"
                rec_level = rec_prof_map.get(req_name, rec_prof_map.get(req_lower, "Intermediate" if is_req else "Beginner"))
                reason = f"Essential {req_type.lower()} skill for '{target_title}' missing from your evidence profile."

                missing_gaps.append(
                    SkillGapSchema(
                        skill_name=req_name,
                        category="Technical",
                        current_proficiency="None",
                        required_proficiency=rec_level,
                        gap_status="Missing",
                        priority=priority,
                        priority_reason=reason
                    )
                )

        await db.commit()

        return target_title, strong_skills, skills_to_improve, missing_gaps, recommended_next
