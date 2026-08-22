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
        hours_per_day: int = 1,
        days_per_week: int = 5,
        learning_style: str = "Hands-on",
        preserve_progress: bool = True
    ) -> Roadmap:
        """Generates a personalized, adaptive learning roadmap derived from actual user skill gaps and study schedule."""

        # 1. Collect user's known/verified skills vs missing/weak skills
        known_skill_names = [s.normalized_name for s in user_skills if s.proficiency_percent >= 75 or s.confidence_status == "Verified"]
        skills_to_improve = [s.normalized_name for s in user_skills if s.proficiency_percent < 75 and s.confidence_status != "Verified"]
        missing_skill_names = [g.skill_name for g in missing_gaps if g.gap_status == "Missing"]

        # Target learning skills = missing skills + skills to improve (excluding strong verified skills)
        learning_skill_pool = list(dict.fromkeys(missing_skill_names + skills_to_improve))
        learning_skill_pool = [s for s in learning_skill_pool if s.lower() not in [k.lower() for k in known_skill_names]]

        # Topologically sort learning skills by prerequisites
        ordered_skills = self.dep_engine.sort_by_dependencies(learning_skill_pool)

        if not ordered_skills:
            # Fallback if profile has no gaps
            ordered_skills = ["Advanced Architecture", "System Performance", "Portfolio Integration"]

        # 2. Divide ordered skills into 4-5 adaptive phases
        chunks_count = min(4, max(2, len(ordered_skills) // 2))
        chunk_size = max(1, len(ordered_skills) // chunks_count)
        
        phase_types = ["Foundation", "Core Skills", "Advanced Skills", "Portfolio Projects", "Job & Interview Readiness"]
        phase_definitions: List[Tuple[str, List[str]]] = []

        for i in range(chunks_count):
            start_idx = i * chunk_size
            end_idx = (i + 1) * chunk_size if i < chunks_count - 1 else len(ordered_skills)
            p_skills = ordered_skills[start_idx:end_idx]
            p_type = phase_types[i] if i < len(phase_types) else f"Specialization {i+1}"
            phase_definitions.append((p_type, p_skills))

        # Always append Job Readiness final phase
        phase_definitions.append(("Job & Interview Readiness", [f"{target_career} Interview Prep", "Portfolio Optimization"]))

        # 3. Generate rich AI phase content for each phase
        generated_phases: List[Dict[str, Any]] = []
        total_tasks_count = 0

        for idx, (p_type, p_skills) in enumerate(phase_definitions, start=1):
            phase_id = f"phase-{idx}"

            # Call AI service for structured content
            ai_content = await self.ai_service.generate_phase_content(
                phase_number=idx,
                phase_type=p_type,
                target_career=target_career,
                phase_skills=p_skills,
                user_known_skills=known_skill_names,
                learning_style=learning_style,
                hours_per_day=hours_per_day
            )

            # Build tasks list
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
                    # Learning resource fields (Phase 3)
                    "concept_explanation": task_ai.concept_explanation or "",
                    "practice_exercise": task_ai.practice_exercise or "",
                    "check_quiz_question": task_ai.check_quiz_question or "",
                    "check_quiz_options": task_ai.check_quiz_options or [],
                    "check_quiz_answer": task_ai.check_quiz_answer or "",
                    # Priority flag (set by interview feedback loop)
                    "is_priority": False,
                    "priority_reason": None
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
                "title": ai_content.milestone_title,
                "criteria": ai_content.milestone_criteria,
                "is_completed": False
            }

            generated_phases.append({
                "id": phase_id,
                "phase_number": idx,
                "title": ai_content.phase_title,
                "type": p_type,
                "skills": p_skills,
                "learning_objectives": ai_content.learning_objectives,
                "progress_percent": 0,
                "tasks": phase_tasks,
                "project": project_obj,
                "milestone": milestone_obj
            })

        # 4. Check existing Roadmap for user
        r_stmt = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
        r_res = await db.execute(r_stmt)
        existing_roadmap = r_res.scalars().first()

        completed_task_ids = existing_roadmap.completed_task_ids if (existing_roadmap and preserve_progress) else []
        completed_milestone_ids = existing_roadmap.completed_milestone_ids if (existing_roadmap and preserve_progress) else []
        completed_project_ids = existing_roadmap.completed_project_ids if (existing_roadmap and preserve_progress) else []

        # 5. Restore progress in generated phases if preserving
        if preserve_progress and (completed_task_ids or completed_milestone_ids or completed_project_ids):
            for phase in generated_phases:
                p_tasks = phase.get("tasks", [])
                completed_in_phase = 0
                for task in p_tasks:
                    if task["id"] in completed_task_ids:
                        task["is_completed"] = True
                        completed_in_phase += 1
                
                if p_tasks:
                    phase["progress_percent"] = int((completed_in_phase / len(p_tasks)) * 100)

                if phase.get("milestone") and phase["milestone"]["id"] in completed_milestone_ids:
                    phase["milestone"]["is_completed"] = True

                if phase.get("project") and phase["project"]["id"] in completed_project_ids:
                    phase["project"]["is_completed"] = True

        # Compute overall progress
        total_tasks_all = sum(len(p.get("tasks", [])) for p in generated_phases)
        completed_tasks_all = sum(sum(1 for t in p.get("tasks", []) if t.get("is_completed")) for p in generated_phases)
        overall_progress = int((completed_tasks_all / total_tasks_all) * 100) if total_tasks_all > 0 else 0

        # Calculate estimated weeks
        weekly_minutes = hours_per_day * days_per_week * 60
        total_estimated_minutes = sum(sum(t.get("estimated_minutes", 30) for t in p.get("tasks", [])) for p in generated_phases)
        total_weeks = max(2, round(total_estimated_minutes / max(1, weekly_minutes)))

        if not existing_roadmap:
            roadmap = Roadmap(
                user_id=user_id,
                target_role=target_career,
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

        await db.commit()
        await db.refresh(roadmap)
        return roadmap

    def get_today_focus_tasks(self, roadmap: Roadmap) -> Dict[str, Any]:
        """Calculates a small set of daily actionable focus tasks for 'What should I do today?'."""
        if not roadmap or not roadmap.phases:
            return {
                "target_career": roadmap.target_role if roadmap else "Software Developer",
                "today_focus_title": "Setup Your Learning Roadmap",
                "today_tasks": [],
                "current_phase_title": "Onboarding",
                "recommended_minutes": 30
            }

        # Find first phase with incomplete tasks
        current_phase = None
        for p in roadmap.phases:
            tasks = p.get("tasks", [])
            if any(not t.get("is_completed") for t in tasks):
                current_phase = p
                break

        if not current_phase:
            current_phase = roadmap.phases[-1]

        incomplete_tasks = [t for t in current_phase.get("tasks", []) if not t.get("is_completed")]
        
        # Pick top 2-3 tasks fitting user's daily study hours (e.g. 1 hour = 60 mins)
        daily_time_limit = roadmap.hours_per_day * 60
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
        focus_title = first_task["title"] if first_task else f"Master {current_phase['title']}"

        return {
            "target_career": roadmap.target_role,
            "today_focus_title": focus_title,
            "current_phase_id": current_phase.get("id"),
            "current_phase_title": current_phase.get("title"),
            "today_tasks": today_tasks,
            "recommended_minutes": accumulated_time if accumulated_time > 0 else 30,
            "why_it_matters": first_task.get("why_it_matters") if first_task else f"Critical prerequisite for {roadmap.target_role} readiness."
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
