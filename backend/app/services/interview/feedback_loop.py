import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

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

        # 1. Collect detected weak topics from individual question evaluations
        detected_weak_topics: List[str] = []
        for q in questions_data:
            ev = q.get("evaluation") or {}
            weak_t = ev.get("detected_weak_topic")
            q_score = ev.get("score", 100)
            # Only treat as meaningful evidence if score was genuinely low
            if weak_t and q_score < 65 and weak_t not in detected_weak_topics:
                detected_weak_topics.append(weak_t)

        # Combine with session-level weak_areas (deduplicated)
        all_weak_topics = list(dict.fromkeys(detected_weak_topics + (weak_areas or [])))

        # 2. Update Skill Intelligence Evidence
        stmt_sk = select(Skill).where(Skill.user_id == user_id)
        res_sk = await db.execute(stmt_sk)
        user_skills = res_sk.scalars().all()
        skill_name_map: Dict[str, Skill] = {
            s.normalized_name.lower(): s for s in user_skills
        }

        # 2a. Positive evidence for high-scoring performance
        if overall_score >= 75:
            for sk in user_skills[:3]:
                # Avoid duplicate same-source evidence within short window
                existing_sources = sk.evidence_sources or []
                evidence_key = f"Mock Technical Interview:{target_role}"
                if evidence_key not in existing_sources:
                    evidence_obj = SkillEvidence(
                        id=str(uuid.uuid4()),
                        user_skill_id=sk.id,
                        source="Mock Technical Interview",
                        description=f"Demonstrated solid conceptual understanding during {target_role} mock interview (score: {overall_score}%).",
                        confidence_weight=85
                    )
                    db.add(evidence_obj)

                    # Upgrade confidence status: Claimed → Supported
                    if sk.confidence_status in ["Claimed", "Missing"]:
                        sk.confidence_status = "Supported"
                        sk.confidence_score = min(90, (sk.confidence_score or 50) + 15)

        # 2b. Add weak-topic evidence to matching skills (only for meaningful weaknesses)
        for weak_topic in all_weak_topics:
            weak_lower = weak_topic.lower()
            matched_skill = skill_name_map.get(weak_lower)

            # Try partial match if exact not found
            if not matched_skill:
                for sk_name, sk in skill_name_map.items():
                    if weak_lower in sk_name or sk_name in weak_lower:
                        matched_skill = sk
                        break

            if matched_skill:
                # Record weak interview evidence — do NOT crush confidence with single answer
                # Only record if not already a weak-evidence record from recent interview
                weak_evidence_key = f"Interview Weakness:{target_role}:{weak_topic}"
                existing_sources = matched_skill.evidence_sources or []
                if weak_evidence_key not in existing_sources:
                    weak_ev = SkillEvidence(
                        id=str(uuid.uuid4()),
                        user_skill_id=matched_skill.id,
                        source="Interview Weakness Detection",
                        description=f"Weak area identified in {target_role} interview: {weak_topic}. Needs focused practice.",
                        confidence_weight=30  # Low weight — single interview answer is not conclusive
                    )
                    db.add(weak_ev)

                    # Only downgrade if already Verified/Supported and weak performance is consistent
                    # Do NOT downgrade from Claimed to lower just from one weak answer
                    if matched_skill.confidence_status == "Verified" and overall_score < 50:
                        matched_skill.confidence_status = "Supported"
                        matched_skill.confidence_score = max(30, (matched_skill.confidence_score or 50) - 10)
                        logger.info(f"Downgraded {matched_skill.skill_name} confidence: Verified → Supported due to consistent weak performance.")

        # 3. Match weak areas against active Roadmap for recommendations + prioritization
        stmt_rm = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
        res_rm = await db.execute(stmt_rm)
        roadmap = res_rm.scalars().first()

        if roadmap and roadmap.phases:
            phases_copy = list(roadmap.phases)
            roadmap_modified = False

            for wa in all_weak_topics:
                wa_lower = wa.lower()
                for p_idx, phase in enumerate(phases_copy):
                    # Match by phase skills list
                    p_name = phase.get("title", phase.get("name", f"Phase {p_idx + 1}"))
                    p_skills = [str(s).lower() for s in phase.get("skills", [])]

                    skill_match = (
                        any(wa_lower in s_name for s_name in p_skills)
                        or any(s_name in wa_lower for s_name in p_skills if len(s_name) >= 3)
                    )

                    if skill_match:
                        rec_str = f"Revisit '{wa}' in {p_name}"
                        if rec_str not in recommended_roadmap_topics:
                            recommended_roadmap_topics.append(rec_str)

                        # Mark the first incomplete matching task as priority
                        for task in phase.get("tasks", []):
                            task_title_lower = task.get("title", "").lower()
                            if not task.get("is_completed") and (wa_lower in task_title_lower or any(s in task_title_lower for s in p_skills if s in wa_lower or wa_lower in s)):
                                task["is_priority"] = True
                                task["priority_reason"] = f"Interview identified '{wa}' as a weak area."
                                roadmap_modified = True
                                break
                        break  # Only match first phase per weak area

            if roadmap_modified:
                roadmap.phases = phases_copy
                flag_modified(roadmap, "phases")

        if not recommended_roadmap_topics and all_weak_topics:
            recommended_roadmap_topics = [
                f"Review foundational concepts for '{w}'" for w in all_weak_topics[:3]
            ]

        await db.commit()
        return recommended_roadmap_topics
