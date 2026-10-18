import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.roadmap import Roadmap
from app.models.skill import Skill
from app.models.profile import UserProfile
from app.models.career_catalog import CareerRole
from app.schemas.skill import SkillGapSchema, UserSkillSchema
from app.services.skill.normalizer import SkillNormalizer
from app.services.roadmap.dependencies import SkillDependencyEngine
from app.services.ai.roadmap_ai import RoadmapAIService

logger = logging.getLogger(__name__)


class RoadmapEngine:
    """Core Roadmap Engine combining deterministic Python dependency logic with Gemini AI personalization."""

    def __init__(self):
        self.normalizer = SkillNormalizer()
        self.dep_engine = SkillDependencyEngine()
        self.ai_service = RoadmapAIService()

    async def generate_roadmap(
        self,
        db: AsyncSession,
        user_id: str,
        target_career: str,
        user_skills: List[Skill],
        missing_gaps: List[SkillGapSchema],
        user_level: str = "Beginner",
        hours_per_day: int = 1,
        days_per_week: int = 5,
        learning_style: str = "Hands-on",
        preserve_progress: bool = True,
        track_pace: Optional[str] = None,
        target_phases_count: Optional[int] = None,
        career_goal: str = "Entry-level Job",
        weak_areas: Optional[List[str]] = None,
        domain_requirement: Optional[str] = None
    ) -> Roadmap:
        """Generates a personalized, adaptive learning roadmap derived from actual user skill gaps, level, career goal, and study schedule."""
        import asyncio

        # 1. Distinguish verified skills from unverified/self-reported/supported skills (Layer A)
        known_skill_names = [
            s.normalized_name for s in user_skills 
            if (getattr(s, "confidence_status", "") == "Verified" and getattr(s, "proficiency_percent", 0) >= 70)
        ]
        # Resume-supported or self-reported skills without assessment verification are NOT assumed mastered:
        skills_to_improve = [
            s.normalized_name for s in user_skills 
            if s.normalized_name not in known_skill_names
        ]
        if weak_areas:
            for w in weak_areas:
                if w not in skills_to_improve and w not in known_skill_names:
                    skills_to_improve.append(w)

        missing_skill_names = [g.skill_name for g in missing_gaps if g.gap_status == "Missing"]

        # Target learning skills = missing skills + skills needing improvement (excluding verified mastered skills)
        learning_skill_pool = list(dict.fromkeys(missing_skill_names + skills_to_improve))
        learning_skill_pool = [s for s in learning_skill_pool if s.lower() not in [k.lower() for k in known_skill_names]]

        is_scratch_beginner = user_level.lower() in ["beginner", "scratch"] or len(known_skill_names) == 0

        # Expand prerequisites recursively so beginners get all foundational basics
        expanded_pool = list(learning_skill_pool)
        for s in learning_skill_pool:
            prereqs = self.dep_engine.get_prerequisites(s)
            for p in prereqs:
                if p.lower() not in [k.lower() for k in known_skill_names] and p.lower() not in [e.lower() for e in expanded_pool]:
                    expanded_pool.append(p)

        # For absolute scratch beginners, ensure fundamental coding & setup are explicitly present
        if is_scratch_beginner:
            scratch_foundations = ["Programming Fundamentals & Logic", "Developer Setup & Git Basics"]
            for sf in reversed(scratch_foundations):
                if sf.lower() not in [e.lower() for e in expanded_pool] and sf.lower() not in [k.lower() for k in known_skill_names]:
                    expanded_pool.insert(0, sf)

        # Topologically sort learning skills by prerequisites
        ordered_skills = self.dep_engine.sort_by_dependencies(expanded_pool)

        # 2. Flexible Level Structure Generation tailored to Domain with Groq AI (Layer C)
        ai_structure = await self.ai_service.generate_domain_roadmap_structure(
            target_career=target_career,
            user_level=user_level,
            target_phases_count=target_phases_count,
            track_pace=track_pace,
            career_goal=career_goal,
            hours_per_day=hours_per_day,
            known_skills=known_skill_names,
            weak_areas=weak_areas,
            domain_requirement=domain_requirement
        )

        phase_outlines = ai_structure.phases if (ai_structure and ai_structure.phases) else []
        if not phase_outlines:
            phase_outlines = self.ai_service._fallback_domain_structure(
                target_career=target_career,
                user_level=user_level,
                target_phases_count=target_phases_count,
                track_pace=track_pace,
                career_goal=career_goal,
                known_skills=known_skill_names,
                weak_areas=weak_areas
            ).phases

        # Align topological skills into phase definitions
        phase_definitions: List[Dict[str, Any]] = []
        chunk_size = max(1, (len(ordered_skills) + len(phase_outlines) - 1) // max(1, len(phase_outlines)))

        for i, outline in enumerate(phase_outlines):
            # Combine domain-outline skills with topologically ordered missing skills
            start_idx = i * chunk_size
            end_idx = min(len(ordered_skills), (i + 1) * chunk_size)
            chunk_skills = ordered_skills[start_idx:end_idx] if start_idx < len(ordered_skills) else []

            merged_skills = list(dict.fromkeys(outline.skills + chunk_skills))
            # Ensure verified skills are not in early phase learning goals
            if i == 0:
                merged_skills = [s for s in merged_skills if s.lower() not in [k.lower() for k in known_skill_names]]
                if is_scratch_beginner and not any("fundamental" in s.lower() or "setup" in s.lower() or "html" in s.lower() for s in merged_skills):
                    merged_skills.insert(0, "Programming Fundamentals & Logic")

            if not merged_skills:
                merged_skills = outline.skills or [f"{target_career} Applied Skills"]

            # Ensure beginner first phase has Scratch/Foundation in type
            p_type = outline.phase_type
            if is_scratch_beginner and i == 0 and not ("scratch" in p_type.lower() or "foundation" in p_type.lower()):
                p_type = f"Foundations from Scratch: {p_type}"

            # Ensure career goal reflected in final phase
            if i == len(phase_outlines) - 1:
                if career_goal == "Internship" and "internship" not in p_type.lower():
                    p_type = "Internship Technical Readiness & Portfolio Capstone"
                elif career_goal == "Certification" and "certification" not in p_type.lower():
                    p_type = "Certification Exam Readiness & Verification"

            phase_definitions.append({
                "idx": i + 1,
                "title": outline.title,
                "type": p_type,
                "skills": merged_skills,
                "milestone_title": outline.milestone_title or f"{outline.title} Milestone",
                "objective": outline.level_objective
            })

        # Inject weak areas into intermediate phase if not already present
        if weak_areas:
            all_phase_skills_lower = [s.lower() for p in phase_definitions for s in p["skills"]]
            for w in weak_areas:
                if w.lower() not in all_phase_skills_lower and len(phase_definitions) > 1:
                    phase_definitions[1]["skills"].append(w)

        # 3. Generate rich AI phase content for each phase with bounded concurrency (Layer D)
        sem = asyncio.Semaphore(2)

        async def _bounded_phase_content(p_item):
            async with sem:
                return await self.ai_service.generate_phase_content(
                    phase_number=p_item["idx"],
                    phase_type=p_item["type"],
                    target_career=target_career,
                    phase_skills=p_item["skills"],
                    user_known_skills=known_skill_names,
                    user_level=user_level,
                    learning_style=learning_style,
                    hours_per_day=hours_per_day,
                    career_goal=career_goal,
                    weak_areas=weak_areas
                )

        phase_coros = [_bounded_phase_content(p_item) for p_item in phase_definitions]
        ai_results = await asyncio.gather(*phase_coros, return_exceptions=True)

        generated_phases: List[Dict[str, Any]] = []
        total_tasks_count = 0

        for idx, p_item in enumerate(phase_definitions, start=1):
            phase_id = f"phase-{idx}"
            raw_ai = ai_results[idx - 1]
            p_type = p_item["type"]
            p_skills = p_item["skills"]
            p_title = p_item["title"]
            p_milestone = p_item["milestone_title"]

            # In case of exception during AI call, use fallback content
            if isinstance(raw_ai, Exception) or not raw_ai:
                logger.warning(f"Using fallback content for phase {idx}: {raw_ai}")
                ai_content = await self.ai_service.generate_phase_content(
                    phase_number=idx,
                    phase_type=p_type,
                    target_career=target_career,
                    phase_skills=p_skills,
                    user_known_skills=known_skill_names,
                    user_level=user_level,
                    learning_style=learning_style,
                    hours_per_day=hours_per_day,
                    career_goal=career_goal,
                    weak_areas=weak_areas
                )
            else:
                ai_content = raw_ai

            # Build tasks list with actionable fields (Layer E)
            phase_tasks = []
            for t_idx, task_ai in enumerate(ai_content.tasks, start=1):
                task_id = f"{phase_id}-task-{t_idx}"
                phase_tasks.append({
                    "id": task_id,
                    "title": task_ai.title,
                    "description": task_ai.description,
                    "estimated_minutes": task_ai.estimated_minutes,
                    "task_type": task_ai.task_type,
                    "why_it_matters": task_ai.why_it_matters,
                    "is_completed": False,
                    "completed_at": None,
                    # Actionable what-to-learn & verification fields
                    "topics_to_learn": task_ai.topics_to_learn or [],
                    "learning_focus": task_ai.learning_focus or "",
                    "practice_goal": task_ai.practice_goal or "",
                    "expected_outcome": getattr(task_ai, "expected_outcome", "") or task_ai.practice_goal or f"Working implementation demonstrating mastery of {task_ai.title}.",
                    "verification_method": getattr(task_ai, "verification_method", "") or "Execute code locally and verify functionality against requirements.",
                    "recommended_resources": task_ai.recommended_resources or [f"Official {target_career} Documentation"],
                    "difficulty_level": task_ai.difficulty_level or ("Scratch" if is_scratch_beginner and idx == 1 else "Beginner"),
                    "prerequisites": task_ai.prerequisites or [],
                    # Legacy learning resource fields
                    "concept_explanation": task_ai.concept_explanation or f"{task_ai.title} provides the essential building blocks and mental models required for {target_career}.",
                    "practice_exercise": task_ai.practice_exercise or "",
                    "check_quiz_question": task_ai.check_quiz_question or "",
                    "check_quiz_options": task_ai.check_quiz_options or [],
                    "check_quiz_answer": task_ai.check_quiz_answer or "",
                    # Priority flag (set by interview feedback loop)
                    "is_priority": False,
                    "priority_reason": None,
                    "next_step": getattr(task_ai, "next_step", "") or "Complete the practice exercise and proceed to the next module."
                })
                total_tasks_count += 1

            # Build project object
            project_obj = None
            if ai_content.project:
                project_id = f"{phase_id}-project"
                project_obj = {
                    "id": project_id,
                    "title": ai_content.project.title,
                    "objective": ai_content.project.objective,
                    "skills_practiced": ai_content.project.skills_practiced or p_skills,
                    "difficulty": ai_content.project.difficulty,
                    "expected_outcome": ai_content.project.expected_outcome,
                    "resume_relevance": ai_content.project.resume_relevance,
                    "is_completed": False
                }

            # Build milestone object
            milestone_id = f"{phase_id}-milestone"
            milestone_obj = {
                "id": milestone_id,
                "title": p_milestone or ai_content.milestone_title,
                "criteria": ai_content.milestone_criteria,
                "is_completed": False
            }

            final_title = p_title or ai_content.phase_title
            generated_phases.append({
                "id": phase_id,
                "phase_number": idx,
                "title": final_title,
                "type": p_type,
                "skills": p_skills,
                "learning_objectives": ai_content.learning_objectives,
                "progress_percent": 0,
                "tasks": phase_tasks,
                "project": project_obj,
                "milestone": milestone_obj
            })

        # 4. Check existing Roadmap for user and preserve progress (Layer H)
        r_stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
        r_res = await db.execute(r_stmt)
        existing_roadmap = r_res.scalars().first()

        is_same_domain = (
            existing_roadmap is not None and
            existing_roadmap.target_role is not None and
            existing_roadmap.target_role.strip().lower() == target_career.strip().lower()
        )

        completed_task_ids = (existing_roadmap.completed_task_ids if (existing_roadmap and preserve_progress and is_same_domain) else []) or []
        completed_milestone_ids = (existing_roadmap.completed_milestone_ids if (existing_roadmap and preserve_progress and is_same_domain) else []) or []
        completed_project_ids = (existing_roadmap.completed_project_ids if (existing_roadmap and preserve_progress and is_same_domain) else []) or []

        # Preserve passed level tests from existing roadmap phases if same domain
        existing_phase_data_map = {}
        if existing_roadmap and preserve_progress and is_same_domain and existing_roadmap.phases:
            for ep in existing_roadmap.phases:
                num = ep.get("phase_number")
                if num:
                    existing_phase_data_map[num] = ep

        # Map previously completed task titles/topics for safe cross-domain recognition
        old_completed_topics = set()
        if existing_roadmap and preserve_progress and existing_roadmap.phases:
            for ep in existing_roadmap.phases:
                for et in ep.get("tasks", []):
                    if et.get("is_completed") or et.get("id") in (existing_roadmap.completed_task_ids or []):
                        if et.get("title"):
                            old_completed_topics.add(et.get("title").strip().lower())
                        for top in (et.get("topics_to_learn") or []):
                            old_completed_topics.add(str(top).strip().lower())

        # 5. Restore progress in generated phases if preserving
        if preserve_progress:
            for phase in generated_phases:
                p_num = phase.get("phase_number")
                old_phase = existing_phase_data_map.get(p_num)
                if old_phase:
                    if old_phase.get("test_passed"):
                        phase["test_passed"] = True
                        phase["test_score"] = old_phase.get("test_score")
                        phase["stars"] = old_phase.get("stars", 1)
                        phase["xp_reward"] = old_phase.get("xp_reward", 100)
                    if old_phase.get("is_unlocked"):
                        phase["is_unlocked"] = True

                p_tasks = phase.get("tasks", [])
                completed_in_phase = 0
                for task in p_tasks:
                    should_complete = False
                    if is_same_domain and task["id"] in completed_task_ids:
                        should_complete = True
                    elif task.get("title", "").strip().lower() in old_completed_topics:
                        should_complete = True
                    elif any(s.strip().lower() in [k.lower() for k in known_skill_names] for s in task.get("topics_to_learn", [])):
                        should_complete = True

                    if should_complete:
                        task["is_completed"] = True
                        if task["id"] not in completed_task_ids:
                            completed_task_ids.append(task["id"])
                        completed_in_phase += 1

                if p_tasks:
                    phase["progress_percent"] = int((completed_in_phase / len(p_tasks)) * 100)

                if phase.get("milestone") and is_same_domain and phase["milestone"]["id"] in completed_milestone_ids:
                    phase["milestone"]["is_completed"] = True

                if phase.get("project") and is_same_domain and phase["project"]["id"] in completed_project_ids:
                    phase["project"]["is_completed"] = True

        # Compute overall progress
        total_tasks_all = sum(len(p.get("tasks", [])) for p in generated_phases)
        completed_tasks_all = sum(sum(1 for t in p.get("tasks", []) if t.get("is_completed")) for p in generated_phases)
        overall_progress = int((completed_tasks_all / total_tasks_all) * 100) if total_tasks_all > 0 else 0

        # Calculate estimated weeks and realistic schedule pacing (Layer F)
        weekly_minutes = max(1, hours_per_day * days_per_week * 60)
        total_estimated_minutes = sum(sum(t.get("estimated_minutes", 30) for t in p.get("tasks", [])) for p in generated_phases)
        total_weeks = max(2, round(total_estimated_minutes / weekly_minutes))

        # Schedule realism note
        if weekly_minutes < 180:
            schedule_notes = f"Notice: {hours_per_day}h/day for {days_per_week} days/week (~{weekly_minutes // 60}h weekly) provides a steady pace across ~{total_weeks} weeks. Consider adding daily hours if you wish to accelerate completion."
        elif total_weeks > 24:
            schedule_notes = f"In-depth curriculum estimated at ~{total_weeks} weeks (~{total_estimated_minutes // 60} total study hours). Focus on consistent daily micro-goals."
        else:
            schedule_notes = f"Realistic completion timeline of ~{total_weeks} weeks based on {hours_per_day}h/day, {days_per_week} days/week commitment."

        # Attach metadata to phases JSON root
        if generated_phases and isinstance(generated_phases[0], dict):
            generated_phases[0]["career_goal"] = career_goal
            generated_phases[0]["schedule_notes"] = schedule_notes

        if not existing_roadmap:
            roadmap = Roadmap(
                user_id=user_id,
                target_role=target_career,
                user_level=user_level,
                overall_progress_percent=overall_progress,
                is_active=True,
                is_outdated=False,
                hours_per_day=hours_per_day,
                days_per_week=days_per_week,
                preferred_learning_style=learning_style,
                total_estimated_weeks=total_weeks,
                phases=generated_phases,
                completed_task_ids=completed_task_ids,
                completed_milestone_ids=completed_milestone_ids,
                completed_project_ids=completed_project_ids
            )
            db.add(roadmap)
        else:
            existing_roadmap.target_role = target_career
            existing_roadmap.user_level = user_level
            existing_roadmap.overall_progress_percent = overall_progress
            existing_roadmap.is_outdated = False
            existing_roadmap.hours_per_day = hours_per_day
            existing_roadmap.days_per_week = days_per_week
            existing_roadmap.preferred_learning_style = learning_style
            existing_roadmap.total_estimated_weeks = total_weeks
            existing_roadmap.phases = generated_phases
            existing_roadmap.completed_task_ids = completed_task_ids
            existing_roadmap.completed_milestone_ids = completed_milestone_ids
            existing_roadmap.completed_project_ids = completed_project_ids
            roadmap = existing_roadmap

        # Dynamic runtime attributes
        roadmap.career_goal = career_goal
        roadmap.schedule_notes = schedule_notes

        await db.commit()
        await db.refresh(roadmap)
        roadmap.career_goal = career_goal
        roadmap.schedule_notes = schedule_notes
        return roadmap

    def get_today_focus_tasks(self, roadmap: Roadmap) -> Dict[str, Any]:
        """Calculates a small set of daily actionable focus tasks for 'What should I do today?'."""
        if not roadmap or not roadmap.phases:
            return {
                "target_career": roadmap.target_role if roadmap else "Software Developer",
                "today_focus_title": "Setup Your Learning Roadmap",
                "today_tasks": [],
                "current_phase_title": "Onboarding",
                "recommended_minutes": 30,
                "is_level_test_recommended": False,
                "completion_status": "in_progress",
                "next_step": "Configure your domain and click Generate Roadmap.",
                "learner_level": "Beginner",
                "starting_point_note": "Starting from foundational scratch — zero prior knowledge assumed.",
                "career_goal": "Entry-level Job"
            }

        user_lvl = getattr(roadmap, "user_level", "Beginner") or "Beginner"
        career_goal = getattr(roadmap, "career_goal", None) or (
            roadmap.phases[0].get("career_goal") if roadmap.phases and isinstance(roadmap.phases[0], dict) else "Entry-level Job"
        )
        if user_lvl.lower() in ["beginner", "scratch"]:
            starting_point_note = "Starting from foundational scratch — zero prior knowledge assumed. Core concepts and mental models will be built step-by-step."
        elif "intermediate" in user_lvl.lower():
            starting_point_note = f"Intermediate track — verified foundations recognized. Fast-tracking directly into practical {roadmap.target_role} workflows."
        else:
            starting_point_note = f"Advanced track — focusing on high-scale systems, deep specialization, and capstone excellence for {roadmap.target_role}."

        # 1. Determine unlocked phases: Level 1 is always unlocked.
        # Level N is unlocked if Level N-1 test was passed (or is_unlocked is explicitly set).
        unlocked_phases = []
        prev_test_passed = True
        for idx, p in enumerate(roadmap.phases):
            is_unlocked = True if idx == 0 else (prev_test_passed or bool(p.get("is_unlocked", False)))
            if is_unlocked:
                unlocked_phases.append(p)
            prev_test_passed = bool(p.get("test_passed", False))

        # 2. Check for incomplete tasks in currently unlocked phases
        active_phase = None
        for p in unlocked_phases:
            tasks = p.get("tasks", [])
            if any(not t.get("is_completed") for t in tasks):
                active_phase = p
                break

        if active_phase:
            incomplete_tasks = [t for t in active_phase.get("tasks", []) if not t.get("is_completed")]
            daily_time_limit = max(30, (roadmap.hours_per_day or 1) * 60)
            today_tasks = []
            accumulated_time = 0

            for t in incomplete_tasks:
                t_time = t.get("estimated_minutes", 30)
                if accumulated_time + t_time <= daily_time_limit + 15 or not today_tasks:
                    today_tasks.append(t)
                    accumulated_time += t_time
                if accumulated_time >= daily_time_limit:
                    break

            first_task = today_tasks[0] if today_tasks else None
            phase_num = active_phase.get("phase_number", 1)
            focus_title = first_task["title"] if first_task else f"Master Level {phase_num}: {active_phase.get('title', 'Current Phase')}"

            return {
                "target_career": roadmap.target_role,
                "today_focus_title": focus_title,
                "current_phase_id": active_phase.get("id"),
                "current_phase_title": active_phase.get("title"),
                "today_tasks": today_tasks,
                "recommended_minutes": accumulated_time if accumulated_time > 0 else 30,
                "why_it_matters": first_task.get("why_it_matters") if first_task else f"Key prerequisite for Level {phase_num} completion.",
                "is_level_test_recommended": False,
                "completion_status": "in_progress",
                "next_step": f"Complete today's practice task to progress towards the Level {phase_num} advancement test.",
                "learner_level": user_lvl,
                "starting_point_note": starting_point_note,
                "career_goal": career_goal
            }

        # 3. All tasks in unlocked phases are complete!
        # Check if there is a next locked phase waiting for a level test
        last_unlocked = unlocked_phases[-1] if unlocked_phases else roadmap.phases[0]
        last_unlocked_num = last_unlocked.get("phase_number", len(unlocked_phases))
        has_next_phase = len(unlocked_phases) < len(roadmap.phases)

        if has_next_phase and not last_unlocked.get("test_passed"):
            next_phase_info = roadmap.phases[len(unlocked_phases)]
            next_name = next_phase_info.get("title") or f"Level {last_unlocked_num + 1}"
            return {
                "target_career": roadmap.target_role,
                "today_focus_title": f"Take Level {last_unlocked_num} Advancement Test",
                "current_phase_id": last_unlocked.get("id"),
                "current_phase_title": last_unlocked.get("title"),
                "today_tasks": [],
                "recommended_minutes": 15,
                "why_it_matters": f"All learning tasks for Level {last_unlocked_num} are completed! Pass the AI Level Test (>=70%) to unlock {next_name}.",
                "is_level_test_recommended": True,
                "completion_status": "ready_for_test",
                "next_step": f"Take the 5-question AI test for Level {last_unlocked_num} to unlock the next level.",
                "learner_level": user_lvl,
                "starting_point_note": starting_point_note,
                "career_goal": career_goal
            }

        # 4. Entire roadmap completed!
        return {
            "target_career": roadmap.target_role,
            "today_focus_title": "Roadmap Mastered! 🏆 Career Ready",
            "current_phase_id": last_unlocked.get("id"),
            "current_phase_title": last_unlocked.get("title"),
            "today_tasks": [],
            "recommended_minutes": 30,
            "why_it_matters": f"Congratulations! You have completed all levels for {roadmap.target_role}. You have verified end-to-end technical readiness.",
            "is_level_test_recommended": False,
            "completion_status": "all_completed",
            "next_step": "Take a Mock Technical Interview in the Interview Arena or explore matching jobs.",
            "learner_level": user_lvl,
            "starting_point_note": starting_point_note,
            "career_goal": career_goal
        }

    def update_task_completion(
        self,
        roadmap: Roadmap,
        task_id: str,
        completed: bool
    ) -> Roadmap:
        """Updates task completion status and recalculates exact phase & overall progress."""
        completed_tasks = set(roadmap.completed_task_ids or [])
        if completed:
            completed_tasks.add(task_id)
        else:
            completed_tasks.discard(task_id)
        
        roadmap.completed_task_ids = list(completed_tasks)

        # Update status inside phase JSON
        phases_copy = list(roadmap.phases)
        total_tasks_all = 0
        completed_tasks_all = 0

        for phase in phases_copy:
            tasks = phase.get("tasks", [])
            phase_completed_count = 0
            for t in tasks:
                if t["id"] in completed_tasks:
                    t["is_completed"] = True
                    t["completed_at"] = datetime.utcnow().isoformat()
                    phase_completed_count += 1
                else:
                    t["is_completed"] = False
                    t["completed_at"] = None
            
            total_tasks_all += len(tasks)
            completed_tasks_all += phase_completed_count

            if tasks:
                phase["progress_percent"] = int((phase_completed_count / len(tasks)) * 100)

        roadmap.phases = phases_copy
        roadmap.overall_progress_percent = int((completed_tasks_all / total_tasks_all) * 100) if total_tasks_all > 0 else 0
        return roadmap
