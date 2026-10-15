import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.models.roadmap import Roadmap
from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence
from app.models.profile import UserProfile
from app.models.digital_twin import CareerDigitalTwin
from app.services.skill.normalizer import SkillNormalizer
from app.services.skill.ingestion_engine import SkillIngestionEngine
from app.services.digital_twin.readiness_engine import ReadinessEngine
from app.services.firestore.user_repo import UserRepository
from app.services.firestore.skills_repo import SkillsRepository
from app.services.firestore.roadmap_repo import RoadmapRepository

logger = logging.getLogger(__name__)


class ProfileProgressSyncService:
    """
    Synchronizes user roadmap milestones and skill learning directly into:
    1. User's Skill Inventory & SkillEvidence
    2. UserProfile (Readiness Score, Skills Matrix, Evidence Points)
    3. Career Digital Twin (Readiness Snapshot & Live Breakdown)
    4. Firestore Mirrors
    """

    def __init__(self):
        self.normalizer = SkillNormalizer()
        self.ingestion_engine = SkillIngestionEngine()
        self.readiness_engine = ReadinessEngine()

    async def sync_task_completion_to_profile(
        self,
        db: AsyncSession,
        user_id: str,
        roadmap: Roadmap,
        task_id: str,
        completed: bool = True
    ) -> Dict[str, Any]:
        """
        Invoked whenever a roadmap task is marked complete or uncomplete.
        Extracts learned topics, upgrades skill confidence/proficiency,
        recomputes overall job readiness, and updates UserProfile & Digital Twin.
        """
        # 1. Locate the task and containing phase
        target_task: Optional[Dict[str, Any]] = None
        target_phase: Optional[Dict[str, Any]] = None

        for phase in (roadmap.phases or []):
            for t in phase.get("tasks", []):
                if t.get("id") == task_id:
                    target_task = t
                    target_phase = phase
                    break
            if target_task:
                break

        task_title = (target_task.get("title") if target_task else f"Task {task_id}")
        task_type = (target_task.get("task_type") if target_task else "Learn")
        phase_title = (target_phase.get("title") if target_phase else "Roadmap Phase")

        # 2. Extract learned skill candidates
        learned_skills_raw: List[str] = []
        if target_task:
            if target_task.get("topics_to_learn"):
                learned_skills_raw.extend(target_task.get("topics_to_learn"))
            if target_task.get("skill"):
                learned_skills_raw.append(target_task.get("skill"))
            if target_task.get("learning_focus"):
                learned_skills_raw.append(target_task.get("learning_focus"))

        # Fallback to phase skills or task title
        if not learned_skills_raw and target_phase and target_phase.get("skills"):
            learned_skills_raw.extend(target_phase.get("skills")[:3])
        if not learned_skills_raw and target_task:
            learned_skills_raw.append(task_title)

        # Normalize and deduplicate skills
        learned_skills: List[str] = []
        for s in learned_skills_raw:
            norm = self.normalizer.normalize(str(s))
            if norm and norm not in learned_skills:
                learned_skills.append(norm)

        updated_skills_summary: List[Dict[str, Any]] = []

        if completed:
            # 3. Upgrade or Ingest learned skills
            for norm_skill in learned_skills:
                sk_stmt = select(Skill).where(Skill.user_id == user_id, Skill.normalized_name == norm_skill)
                sk_res = await db.execute(sk_stmt)
                existing_skill = sk_res.scalars().first()

                now = datetime.utcnow()
                category = self.ingestion_engine._fallback_categorize(norm_skill)

                if existing_skill:
                    # Boost proficiency and confidence
                    prof_boost = 20 if task_type == "Project" else 15
                    conf_boost = 15 if task_type == "Project" else 10
                    existing_skill.proficiency_percent = min(100, (existing_skill.proficiency_percent or 50) + prof_boost)
                    existing_skill.confidence_score = min(95, (existing_skill.confidence_score or 50) + conf_boost)

                    # Upgrade confidence status
                    if existing_skill.confidence_status in ["Claimed", "Missing"]:
                        existing_skill.confidence_status = "Supported"
                    elif existing_skill.confidence_status == "Supported" and (task_type == "Project" or existing_skill.confidence_score >= 80):
                        existing_skill.confidence_status = "Verified"
                        existing_skill.is_verified = True

                    # Update gap status
                    if existing_skill.is_gap:
                        if existing_skill.proficiency_percent >= 70:
                            existing_skill.is_gap = False
                            existing_skill.gap_status = "Resolved"
                        else:
                            existing_skill.gap_status = "In Progress"

                    # Add Roadmap evidence source
                    sources = list(existing_skill.evidence_sources or [])
                    if "Roadmap" not in sources:
                        sources.append("Roadmap")
                    existing_skill.evidence_sources = sources
                    existing_skill.last_evaluated_at = now
                    db.add(existing_skill)

                    # Add SkillEvidence
                    ev = SkillEvidence(
                        id=str(uuid.uuid4()),
                        user_skill_id=existing_skill.id,
                        source="Roadmap Task Completion",
                        description=f"Completed task '{task_title}' ({task_type}) in '{phase_title}'.",
                        confidence_weight=90 if task_type == "Project" else 80
                    )
                    db.add(ev)

                    updated_skills_summary.append({
                        "skill_name": existing_skill.skill_name,
                        "status": existing_skill.confidence_status,
                        "proficiency": existing_skill.proficiency_percent
                    })
                else:
                    # New Skill acquired through roadmap
                    is_ver = (task_type == "Project")
                    new_skill = Skill(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        skill_name=norm_skill,
                        normalized_name=norm_skill,
                        category=category,
                        proficiency_percent=75 if task_type == "Project" else 65,
                        proficiency_level="Intermediate" if task_type == "Project" else "Beginner",
                        confidence_score=85 if task_type == "Project" else 70,
                        confidence_status="Verified" if task_type == "Project" else "Supported",
                        is_verified=is_ver,
                        evidence_sources=["Roadmap"],
                        gap_status="Resolved" if task_type == "Project" else "In Progress",
                        last_evaluated_at=now
                    )
                    db.add(new_skill)
                    await db.flush()

                    ev = SkillEvidence(
                        id=str(uuid.uuid4()),
                        user_skill_id=new_skill.id,
                        source="Roadmap Task Completion",
                        description=f"Acquired through completing '{task_title}' ({task_type}) in '{phase_title}'.",
                        confidence_weight=90 if task_type == "Project" else 80
                    )
                    db.add(ev)

                    updated_skills_summary.append({
                        "skill_name": new_skill.skill_name,
                        "status": new_skill.confidence_status,
                        "proficiency": new_skill.proficiency_percent
                    })

        # 4. Recompute Career Readiness with live evidence
        readiness_data = await self.readiness_engine.compute(db, user_id)
        new_readiness_score = readiness_data.get("overall_readiness_score", 0)

        # 5. Fetch and update UserProfile
        p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        p_res = await db.execute(p_stmt)
        profile = p_res.scalar_one_or_none()

        if not profile:
            profile = UserProfile(
                user_id=user_id,
                target_career=roadmap.target_role or "Software Developer",
                job_readiness_score=new_readiness_score,
                skills_matrix={},
                evidence_points=[]
            )
            db.add(profile)
            await db.flush()

        # Update profile readiness score
        profile.job_readiness_score = new_readiness_score

        # Query all live user skills to assemble skills_matrix
        all_skills_stmt = select(Skill).where(Skill.user_id == user_id)
        all_skills_res = await db.execute(all_skills_stmt)
        all_user_skills = all_skills_res.scalars().all()

        verified_names = [s.skill_name for s in all_user_skills if s.confidence_status == "Verified"]
        supported_names = [s.skill_name for s in all_user_skills if s.confidence_status == "Supported"]
        gap_names = [s.skill_name for s in all_user_skills if s.is_gap or s.gap_status == "Missing"]

        current_matrix = dict(profile.skills_matrix or {})
        recent_learned = list(current_matrix.get("recent_learned", []))

        if completed and learned_skills:
            recent_learned.insert(0, {
                "task_id": task_id,
                "task_title": task_title,
                "task_type": task_type,
                "skills": learned_skills,
                "completed_at": datetime.utcnow().isoformat()
            })
            recent_learned = recent_learned[:10]  # Retain last 10 milestones
        elif not completed:
            recent_learned = [r for r in recent_learned if r.get("task_id") != task_id]

        profile.skills_matrix = {
            "verified_skills": verified_names,
            "supported_skills": supported_names,
            "skill_gaps": gap_names,
            "recent_learned": recent_learned,
            "roadmap_progress": roadmap.overall_progress_percent,
            "total_skills": len(all_user_skills),
            "readiness_breakdown": {
                "skill_readiness": readiness_data.get("skill_readiness", 0),
                "roadmap_progress": readiness_data.get("roadmap_progress", 0),
                "resume_readiness": readiness_data.get("resume_readiness", 0),
                "interview_readiness": readiness_data.get("interview_readiness", 0),
                "job_match_readiness": readiness_data.get("job_match_readiness", 0),
            }
        }
        flag_modified(profile, "skills_matrix")

        # Update evidence points
        evidence_list = list(profile.evidence_points or [])
        ev_item = f"Roadmap: Completed '{task_title}' ({task_type})"
        if completed and ev_item not in evidence_list:
            evidence_list.insert(0, ev_item)
            profile.evidence_points = evidence_list[:15]
            flag_modified(profile, "evidence_points")
        elif not completed and ev_item in evidence_list:
            evidence_list.remove(ev_item)
            profile.evidence_points = evidence_list
            flag_modified(profile, "evidence_points")

        # 6. Update CareerDigitalTwin if it exists
        dt_stmt = select(CareerDigitalTwin).where(CareerDigitalTwin.user_id == user_id)
        dt_res = await db.execute(dt_stmt)
        digital_twin = dt_res.scalar_one_or_none()
        if digital_twin:
            digital_twin.overall_readiness_score = new_readiness_score
            digital_twin.readiness_label = readiness_data.get("readiness_label", "In Progress")
            digital_twin.skill_readiness = readiness_data.get("skill_readiness", 0)
            digital_twin.roadmap_progress = readiness_data.get("roadmap_progress", 0)
            digital_twin.resume_readiness = readiness_data.get("resume_readiness", 0)
            digital_twin.interview_readiness = readiness_data.get("interview_readiness", 0)
            digital_twin.last_computed_at = datetime.utcnow()
            db.add(digital_twin)

        await db.commit()

        # 7. Mirror to Firestore asynchronously (graceful fallback)
        try:
            await UserRepository.save_user(user_id, {
                "job_readiness_score": new_readiness_score,
                "skills_matrix": profile.skills_matrix,
                "evidence_points": profile.evidence_points,
            })
            for sk_item in updated_skills_summary:
                await SkillsRepository.save_skill(user_id, sk_item["skill_name"], sk_item)
        except Exception as e:
            logger.warning(f"Firestore profile sync notice: {e}")

        return {
            "task_id": task_id,
            "task_title": task_title,
            "completed": completed,
            "learned_skills": learned_skills,
            "new_readiness_score": new_readiness_score,
            "updated_skills": updated_skills_summary
        }
