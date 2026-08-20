import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.profile import UserProfile
from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence
from app.models.roadmap import Roadmap

logger = logging.getLogger(__name__)


class InterviewFeedbackLoop:
    """Service synchronizing interview evaluation results back into Skill Intelligence & Roadmap System."""

    async def process_interview_feedback(
        self,
        db: AsyncSession,
        user_id: str,
        target_role: str,
        overall_score: int,
        category_scores: Dict[str, int],
        weak_areas: List[str],
        questions_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Add evidence to Skill Intelligence and generate roadmap topic recommendations."""
        recommended_roadmap_topics: List[str] = []

        # 1. Update Skill Intelligence Evidence for high-performing areas
        if overall_score >= 75:
            stmt_sk = select(Skill).where(Skill.user_id == user_id)
            res_sk = await db.execute(stmt_sk)
            user_skills = res_sk.scalars().all()

            for sk in user_skills[:3]:
                # Add evidence record
                evidence_obj = SkillEvidence(
                    id=str(uuid.uuid4()),
                    user_skill_id=sk.id,
                    source="Mock Technical Interview",
                    description=f"Demonstrated solid conceptual understanding during {target_role} mock interview.",
                    confidence_weight=85
                )
                db.add(evidence_obj)

                # Upgrade confidence status if claimed
                if sk.confidence_status in ["Claimed", "Missing"]:
                    sk.confidence_status = "Supported"
                    sk.confidence_score = min(90, (sk.confidence_score or 50) + 15)

        # 2. Match weak areas against active Roadmap
        stmt_rm = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
        res_rm = await db.execute(stmt_rm)
        roadmap = res_rm.scalars().first()

        if roadmap and roadmap.phases:
            for wa in weak_areas:
                wa_lower = wa.lower()
                for p_idx, phase in enumerate(roadmap.phases, start=1):
                    p_name = phase.get("name", f"Phase {p_idx}")
                    p_skills = [s.get("name", "").lower() for s in phase.get("skills", [])]

                    if any(s_name in wa_lower for s_name in p_skills) or any(wa_lower in s_name for s_name in p_skills):
                        rec_str = f"Revisit '{wa}' in {p_name}"
                        if rec_str not in recommended_roadmap_topics:
                            recommended_roadmap_topics.append(rec_str)
                            break

        if not recommended_roadmap_topics and weak_areas:
            recommended_roadmap_topics = [f"Review foundational concepts for '{w}'" for w in weak_areas[:3]]

        await db.commit()
        return recommended_roadmap_topics
