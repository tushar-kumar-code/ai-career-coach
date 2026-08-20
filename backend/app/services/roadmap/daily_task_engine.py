import logging
from typing import List, Dict, Any, Optional
from app.models.roadmap import Roadmap
from app.schemas.roadmap import DailyTasksResponse, RoadmapTaskSchema

logger = logging.getLogger(__name__)


class DailyTaskEngine:
    """Engine selecting actionable 'What should I do today?' tasks from active roadmap."""

    def get_today_tasks(self, roadmap: Roadmap) -> DailyTasksResponse:
        hours_budget = float(roadmap.hours_per_day)
        minutes_budget = hours_budget * 60.0

        completed_task_ids = set(roadmap.completed_task_ids or [])
        phases = roadmap.phases or []

        current_phase_name = "Phase 1 — Core Foundations"
        selected_tasks: List[Dict[str, Any]] = []

        # Find first phase with incomplete tasks
        for phase in phases:
            tasks = phase.get("tasks", [])
            incomplete = [t for t in tasks if t.get("id") not in completed_task_ids]

            if incomplete:
                current_phase_name = phase.get("name", "Active Phase")
                accumulated_min = 0.0

                for t in incomplete:
                    t_min = float(t.get("estimated_minutes", 30))
                    # Allow up to budget + 15 min tolerance
                    if accumulated_min + t_min <= minutes_budget + 15 or not selected_tasks:
                        selected_tasks.append(t)
                        accumulated_min += t_min
                    if accumulated_min >= minutes_budget:
                        break
                break

        # Fallback if all tasks in all phases are completed
        if not selected_tasks and phases:
            current_phase_name = phases[-1].get("name", "Final Phase")
            all_tasks = phases[-1].get("tasks", [])
            if all_tasks:
                selected_tasks = all_tasks[:2]

        # Convert to Pydantic task schemas
        task_schemas = [
            RoadmapTaskSchema(
                id=t["id"],
                title=t["title"],
                skill=t["skill"],
                estimated_minutes=t.get("estimated_minutes", 30),
                why_matters=t.get("why_matters", f"Key skill for {roadmap.target_role}."),
                practice_activity=t.get("practice_activity", "Complete coding exercise."),
                completed=t["id"] in completed_task_ids,
                completed_at=t.get("completed_at")
            )
            for t in selected_tasks
        ]

        top_task_title = task_schemas[0].title if task_schemas else "Master Core Target Skills"
        top_task_why = task_schemas[0].why_matters if task_schemas else f"High priority for {roadmap.target_role}."

        return DailyTasksResponse(
            roadmap_id=roadmap.id,
            target_role=roadmap.target_role,
            current_phase_name=current_phase_name,
            hours_budget=hours_budget,
            today_focus_title=top_task_title,
            why_it_matters=top_task_why,
            tasks=task_schemas
        )
