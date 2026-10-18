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

        from app.services.skill.ingestion_engine import is_valid_profile_skill

        # Normalize and filter to only legitimate skills
        learned_skills: List[str] = []
        for s in learned_skills_raw:
            if not s or not is_valid_profile_skill(str(s)):
                continue
            norm = self.normalizer.normalize(str(s))
            if norm and is_valid_profile_skill(norm) and norm not in learned_skills:
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

    async def sync_level_test_to_profile(
        self,
        db: AsyncSession,
        user_id: str,
        roadmap: Roadmap,
        phase_number: int,
        test_score: int,
        passed: bool,
        stars: int = 0,
        xp_reward: int = 100
    ) -> Dict[str, Any]:
        """
        Invoked when a user submits and completes a Roadmap Level Test.
        Upgrades confidence/proficiency for skills covered in the phase,
        records verified test evidence, and updates UserProfile & Digital Twin.
        """
        # 1. Identify target phase
        target_phase: Optional[Dict[str, Any]] = None
        for p in (roadmap.phases or []):
            if p.get("phase_number") == phase_number:
                target_phase = p
                break
        if not target_phase and roadmap.phases:
            target_phase = roadmap.phases[min(phase_number - 1, len(roadmap.phases) - 1)]

        phase_title = target_phase.get("title", f"Level {phase_number}") if target_phase else f"Level {phase_number}"
        phase_skills_raw = list(target_phase.get("skills", []) if target_phase else [])

        from app.services.skill.ingestion_engine import is_valid_profile_skill
        tested_skills: List[str] = []
        for s in phase_skills_raw:
            if not s or not is_valid_profile_skill(str(s)):
                continue
            norm = self.normalizer.normalize(str(s))
            if norm and is_valid_profile_skill(norm) and norm not in tested_skills:
                tested_skills.append(norm)

        updated_skills_summary: List[Dict[str, Any]] = []
        now = datetime.utcnow()

        if passed and test_score >= 60:
            for norm_skill in tested_skills:
                sk_stmt = select(Skill).where(Skill.user_id == user_id, Skill.normalized_name == norm_skill)
                sk_res = await db.execute(sk_stmt)
                existing_skill = sk_res.scalars().first()

                conf_boost = 20 if test_score >= 80 else 15
                prof_boost = 25 if test_score >= 80 else 15

                if existing_skill:
                    existing_skill.proficiency_percent = min(100, (existing_skill.proficiency_percent or 50) + prof_boost)
                    existing_skill.confidence_score = min(100, (existing_skill.confidence_score or 50) + conf_boost)
                    existing_skill.confidence_status = "Verified" if test_score >= 75 else "Supported"
                    if test_score >= 75:
                        existing_skill.is_verified = True

                    if existing_skill.is_gap and existing_skill.proficiency_percent >= 65:
                        existing_skill.is_gap = False
                        existing_skill.gap_status = "Resolved"

                    sources = list(existing_skill.evidence_sources or [])
                    if "Level Test" not in sources:
                        sources.append("Level Test")
                    existing_skill.evidence_sources = sources
                    existing_skill.last_evaluated_at = now
                    db.add(existing_skill)

                    ev = SkillEvidence(
                        id=str(uuid.uuid4()),
                        user_skill_id=existing_skill.id,
                        source="Level Test",
                        description=f"Passed {phase_title} Assessment with {test_score}% score ({stars} stars, +{xp_reward} XP).",
                        confidence_weight=90 if test_score >= 80 else 75
                    )
                    db.add(ev)
                    updated_skills_summary.append({
                        "skill_name": existing_skill.skill_name,
                        "status": existing_skill.confidence_status,
                        "proficiency": existing_skill.proficiency_percent
                    })
                else:
                    category = self.ingestion_engine._fallback_categorize(norm_skill)
                    new_skill = Skill(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        skill_name=norm_skill,
                        normalized_name=norm_skill,
                        category=category,
                        proficiency_percent=min(100, 60 + int(test_score * 0.3)),
                        proficiency_level="Intermediate" if test_score >= 75 else "Beginner",
                        confidence_score=min(95, 60 + int(test_score * 0.35)),
                        confidence_status="Verified" if test_score >= 80 else "Supported",
                        is_verified=(test_score >= 80),
                        evidence_sources=["Level Test"],
                        gap_status="Resolved" if test_score >= 70 else "In Progress",
                        last_evaluated_at=now
                    )
                    db.add(new_skill)
                    await db.flush()

                    ev = SkillEvidence(
                        id=str(uuid.uuid4()),
                        user_skill_id=new_skill.id,
                        source="Level Test",
                        description=f"Demonstrated proficiency in {phase_title} test with {test_score}% score.",
                        confidence_weight=90 if test_score >= 80 else 75
                    )
                    db.add(ev)
                    updated_skills_summary.append({
                        "skill_name": new_skill.skill_name,
                        "status": new_skill.confidence_status,
                        "proficiency": new_skill.proficiency_percent
                    })

        # 2. Recompute Career Readiness
        readiness_data = await self.readiness_engine.compute(db, user_id)
        new_readiness_score = readiness_data.get("overall_readiness_score", 0)

        # 3. Update UserProfile
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

        profile.job_readiness_score = new_readiness_score

        # Update evidence points
        evidence_list = list(profile.evidence_points or [])
        ev_label = f"Level Test: Passed {phase_title} ({test_score}%, {stars}★)" if passed else f"Level Test: Attempted {phase_title} ({test_score}%)"
        if ev_label not in evidence_list:
            evidence_list.insert(0, ev_label)
            profile.evidence_points = evidence_list[:15]
            flag_modified(profile, "evidence_points")

        # Update skills_matrix
        matrix = dict(profile.skills_matrix or {})
        recent_tests = list(matrix.get("recent_level_tests", []))
        recent_tests.insert(0, {
            "phase_number": phase_number,
            "phase_title": phase_title,
            "score": test_score,
            "passed": passed,
            "stars": stars,
            "xp_reward": xp_reward,
            "completed_at": now.isoformat()
        })
        matrix["recent_level_tests"] = recent_tests[:10]
        matrix["readiness_breakdown"] = {
            "skill_readiness": readiness_data.get("skill_readiness", 0),
            "roadmap_progress": readiness_data.get("roadmap_progress", 0),
            "resume_readiness": readiness_data.get("resume_readiness", 0),
            "interview_readiness": readiness_data.get("interview_readiness", 0),
            "job_match_readiness": readiness_data.get("job_match_readiness", 0),
        }
        profile.skills_matrix = matrix
        flag_modified(profile, "skills_matrix")

        # 4. Update CareerDigitalTwin
        dt_stmt = select(CareerDigitalTwin).where(CareerDigitalTwin.user_id == user_id)
        dt_res = await db.execute(dt_stmt)
        digital_twin = dt_res.scalar_one_or_none()
        if digital_twin:
            digital_twin.overall_readiness_score = new_readiness_score
            digital_twin.readiness_label = readiness_data.get("readiness_label", "In Progress")
            digital_twin.skill_readiness = readiness_data.get("skill_readiness", 0)
            digital_twin.roadmap_progress = readiness_data.get("roadmap_progress", 0)
            digital_twin.last_computed_at = datetime.utcnow()
            db.add(digital_twin)

        await db.commit()

        # 5. Mirror to Firestore
        try:
            await UserRepository.save_user(user_id, {
                "job_readiness_score": new_readiness_score,
                "skills_matrix": profile.skills_matrix,
                "evidence_points": profile.evidence_points,
            })
            for sk_item in updated_skills_summary:
                await SkillsRepository.save_skill(user_id, sk_item["skill_name"], sk_item)
        except Exception as e:
            logger.warning(f"Firestore test sync warning: {e}")

        return {
            "phase_number": phase_number,
            "phase_title": phase_title,
            "passed": passed,
            "test_score": test_score,
            "new_readiness_score": new_readiness_score,
            "updated_skills": updated_skills_summary
        }

    async def sync_practice_drill_to_profile(
        self,
        db: AsyncSession,
        user_id: str,
        topic: str,
        is_correct: bool,
        score: int
    ) -> Dict[str, Any]:
        """
        Invoked when a user answers an Interactive Practice Drill question.
        On correct answer: adds skill evidence, raises topic proficiency & confidence,
        recomputes readiness, and updates UserProfile & Digital Twin.
        """
        if not topic or not topic.strip():
            return {"synced": False}

        from app.services.skill.ingestion_engine import is_valid_profile_skill
        norm_topic = self.normalizer.normalize(topic.strip())
        if not norm_topic or not is_valid_profile_skill(norm_topic):
            norm_topic = topic.strip().title()

        now = datetime.utcnow()
        updated_skills_summary: List[Dict[str, Any]] = []

        if is_correct:
            sk_stmt = select(Skill).where(Skill.user_id == user_id, Skill.normalized_name == norm_topic)
            sk_res = await db.execute(sk_stmt)
            existing_skill = sk_res.scalars().first()

            if existing_skill:
                existing_skill.proficiency_percent = min(100, (existing_skill.proficiency_percent or 50) + 8)
                existing_skill.confidence_score = min(95, (existing_skill.confidence_score or 50) + 8)
                if existing_skill.confidence_status in ["Claimed", "Missing"]:
                    existing_skill.confidence_status = "Supported"
                elif existing_skill.confidence_status == "Supported" and existing_skill.confidence_score >= 85:
                    existing_skill.confidence_status = "Verified"
                    existing_skill.is_verified = True

                if existing_skill.is_gap and existing_skill.proficiency_percent >= 70:
                    existing_skill.is_gap = False
                    existing_skill.gap_status = "Resolved"

                sources = list(existing_skill.evidence_sources or [])
                if "Practice Drill" not in sources:
                    sources.append("Practice Drill")
                existing_skill.evidence_sources = sources
                existing_skill.last_evaluated_at = now
                db.add(existing_skill)

                ev = SkillEvidence(
                    id=str(uuid.uuid4()),
                    user_skill_id=existing_skill.id,
                    source="Interactive Skill Practice Drill",
                    description=f"Solved practice question on '{norm_topic}' with 100% precision.",
                    confidence_weight=80
                )
                db.add(ev)
                updated_skills_summary.append({
                    "skill_name": existing_skill.skill_name,
                    "status": existing_skill.confidence_status,
                    "proficiency": existing_skill.proficiency_percent
                })
            else:
                category = self.ingestion_engine._fallback_categorize(norm_topic)
                new_skill = Skill(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    skill_name=norm_topic,
                    normalized_name=norm_topic,
                    category=category,
                    proficiency_percent=65,
                    proficiency_level="Beginner",
                    confidence_score=70,
                    confidence_status="Supported",
                    is_verified=False,
                    evidence_sources=["Practice Drill"],
                    gap_status="In Progress",
                    last_evaluated_at=now
                )
                db.add(new_skill)
                await db.flush()

                ev = SkillEvidence(
                    id=str(uuid.uuid4()),
                    user_skill_id=new_skill.id,
                    source="Interactive Skill Practice Drill",
                    description=f"Solved interactive drill for '{norm_topic}'.",
                    confidence_weight=75
                )
                db.add(ev)
                updated_skills_summary.append({
                    "skill_name": new_skill.skill_name,
                    "status": new_skill.confidence_status,
                    "proficiency": new_skill.proficiency_percent
                })

        # Recompute Readiness
        readiness_data = await self.readiness_engine.compute(db, user_id)
        new_readiness_score = readiness_data.get("overall_readiness_score", 0)

        # Update UserProfile
        p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        p_res = await db.execute(p_stmt)
        profile = p_res.scalar_one_or_none()
        if profile:
            profile.job_readiness_score = new_readiness_score
            matrix = dict(profile.skills_matrix or {})
            recent_drills = list(matrix.get("recent_practice_drills", []))
            recent_drills.insert(0, {
                "topic": norm_topic,
                "is_correct": is_correct,
                "score": score,
                "practiced_at": now.isoformat()
            })
            matrix["recent_practice_drills"] = recent_drills[:10]
            profile.skills_matrix = matrix
            flag_modified(profile, "skills_matrix")

            if is_correct:
                ev_label = f"Practice: Solved '{norm_topic}' drill"
                evidence_list = list(profile.evidence_points or [])
                if ev_label not in evidence_list:
                    evidence_list.insert(0, ev_label)
                    profile.evidence_points = evidence_list[:15]
                    flag_modified(profile, "evidence_points")

        # Update Digital Twin
        dt_stmt = select(CareerDigitalTwin).where(CareerDigitalTwin.user_id == user_id)
        dt_res = await db.execute(dt_stmt)
        digital_twin = dt_res.scalar_one_or_none()
        if digital_twin:
            digital_twin.overall_readiness_score = new_readiness_score
            digital_twin.readiness_label = readiness_data.get("readiness_label", "In Progress")
            digital_twin.skill_readiness = readiness_data.get("skill_readiness", 0)
            digital_twin.last_computed_at = datetime.utcnow()
            db.add(digital_twin)

        await db.commit()

        # Firestore mirror
        try:
            if profile:
                await UserRepository.save_user(user_id, {
                    "job_readiness_score": new_readiness_score,
                    "skills_matrix": profile.skills_matrix,
                    "evidence_points": profile.evidence_points,
                })
            for sk_item in updated_skills_summary:
                await SkillsRepository.save_skill(user_id, sk_item["skill_name"], sk_item)
        except Exception as e:
            logger.warning(f"Firestore practice sync notice: {e}")

        return {
            "topic": norm_topic,
            "is_correct": is_correct,
            "new_readiness_score": new_readiness_score,
            "updated_skills": updated_skills_summary
        }

    async def sync_interview_to_profile(
        self,
        db: AsyncSession,
        user_id: str,
        target_role: str,
        overall_score: int,
        category_scores: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Invoked when an interview session is finalized.
        Recomputes readiness score, updates UserProfile evidence, and synchronizes Digital Twin.
        """
        now = datetime.utcnow()

        # Recompute Readiness
        readiness_data = await self.readiness_engine.compute(db, user_id)
        new_readiness_score = readiness_data.get("overall_readiness_score", 0)

        # Update UserProfile
        p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        p_res = await db.execute(p_stmt)
        profile = p_res.scalar_one_or_none()

        if profile:
            profile.job_readiness_score = new_readiness_score

            ev_item = f"Interview: Completed {target_role} ({overall_score}% score)"
            evidence_list = list(profile.evidence_points or [])
            if ev_item not in evidence_list:
                evidence_list.insert(0, ev_item)
                profile.evidence_points = evidence_list[:15]
                flag_modified(profile, "evidence_points")

            matrix = dict(profile.skills_matrix or {})
            recent_interviews = list(matrix.get("recent_interviews", []))
            recent_interviews.insert(0, {
                "target_role": target_role,
                "overall_score": overall_score,
                "category_scores": category_scores,
                "completed_at": now.isoformat()
            })
            matrix["recent_interviews"] = recent_interviews[:10]
            matrix["readiness_breakdown"] = {
                "skill_readiness": readiness_data.get("skill_readiness", 0),
                "roadmap_progress": readiness_data.get("roadmap_progress", 0),
                "resume_readiness": readiness_data.get("resume_readiness", 0),
                "interview_readiness": readiness_data.get("interview_readiness", 0),
                "job_match_readiness": readiness_data.get("job_match_readiness", 0),
            }
            profile.skills_matrix = matrix
            flag_modified(profile, "skills_matrix")

        # Update Digital Twin
        dt_stmt = select(CareerDigitalTwin).where(CareerDigitalTwin.user_id == user_id)
        dt_res = await db.execute(dt_stmt)
        digital_twin = dt_res.scalar_one_or_none()
        if digital_twin:
            digital_twin.overall_readiness_score = new_readiness_score
            digital_twin.readiness_label = readiness_data.get("readiness_label", "In Progress")
            digital_twin.interview_readiness = readiness_data.get("interview_readiness", 0)
            digital_twin.skill_readiness = readiness_data.get("skill_readiness", 0)
            digital_twin.last_computed_at = datetime.utcnow()
            db.add(digital_twin)

        await db.commit()

        # Firestore mirror
        try:
            if profile:
                await UserRepository.save_user(user_id, {
                    "job_readiness_score": new_readiness_score,
                    "skills_matrix": profile.skills_matrix,
                    "evidence_points": profile.evidence_points,
                })
        except Exception as e:
            logger.warning(f"Firestore interview sync notice: {e}")

        return {
            "target_role": target_role,
            "overall_score": overall_score,
            "new_readiness_score": new_readiness_score
        }

