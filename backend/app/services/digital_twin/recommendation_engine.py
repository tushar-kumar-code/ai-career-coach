"""
Next Best Action Recommendation Engine
=======================================
Deterministically selects the single highest-impact action based on
the user''s computed readiness sub-scores and real DB gaps.

Priority: targets the LOWEST sub-score dimension first.
Provides: what, why, expected_impact, related_goal, action_type, action_link.
"""
import logging
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.skill import Skill
from app.models.resume import Resume
from app.models.roadmap import Roadmap
from app.models.interview import InterviewSession

logger = logging.getLogger(__name__)

# Maps dimension name -> (action_type, default action text, action link)
DIMENSION_ACTIONS = {
    "interview_readiness": (
        "practice_interview",
        "Complete a Mock Interview Session",
        "/interview",
        "Your interview readiness is the weakest area. Completing even one session dramatically improves confidence and score.",
        "high",
    ),
    "resume_readiness": (
        "improve_resume",
        "Upload or Improve Your Resume",
        "/resume",
        "Resume ATS score directly determines if applications pass automated screening. Improving it unlocks more job matches.",
        "high",
    ),
    "skill_readiness": (
        "learn_skill",
        "Work on a Priority Skill Gap",
        "/skills",
        "Closing a critical skill gap makes you visible to more job listings and increases job match scores.",
        "high",
    ),
    "roadmap_progress": (
        "complete_task",
        "Complete Today''s Roadmap Task",
        "/roadmap",
        "Consistent daily roadmap progress is the fastest path to career readiness.",
        "medium",
    ),
    "job_match_readiness": (
        "apply_job",
        "Apply to a Matched Job Opportunity",
        "/jobs",
        "With your current profile, you have matching job opportunities. Applying builds real pipeline.",
        "medium",
    ),
    "portfolio_readiness": (
        "build_project",
        "Complete a Roadmap Project",
        "/roadmap",
        "A completed project provides concrete evidence for recruiters and significantly boosts your profile.",
        "medium",
    ),
}


class RecommendationEngine:
    """Produces the single Next Best Action based on actual user data."""

    async def get_next_action(
        self,
        db: AsyncSession,
        user_id: str,
        sub_scores: Dict[str, int],
        priority_gaps: List[Dict],
    ) -> Dict:
        """
        Selects the highest-impact action:
        1. Find the lowest-scoring sub-score dimension
        2. Look for a specific gap/item within that dimension
        3. Return actionable recommendation with context
        """
        if not sub_scores:
            return self._default_action()

        # Sort dimensions by score ascending (lowest first)
        sorted_dims = sorted(
            [(k, v) for k, v in sub_scores.items() if k in DIMENSION_ACTIONS],
            key=lambda x: x[1]
        )

        # Special case: if no modules used at all → start with assessment
        if all(v == 0 for _, v in sorted_dims):
            return {
                "action_type": "complete_assessment",
                "title": "Complete Your Career Discovery Assessment",
                "description": "You haven''t set a target career yet. This is the required first step.",
                "why_it_matters": "Without a target career, no readiness scores can be computed.",
                "expected_impact": "Unlocks all other modules and sets your career direction.",
                "related_goal": "Career Discovery",
                "action_link": "/assessment",
                "impact_level": "critical",
                "specific_item": None,
            }

        target_dimension, target_score = sorted_dims[0]
        action_type, default_title, action_link, why, impact = DIMENSION_ACTIONS[target_dimension]

        # Get a specific item to work on within this dimension
        specific_item = await self._get_specific_item(db, user_id, target_dimension, priority_gaps)

        title = default_title
        description = default_title
        if specific_item:
            title = specific_item.get("title", default_title)
            description = specific_item.get("description", default_title)

        impact_level = "high" if target_score < 30 else "medium" if target_score < 60 else "low"

        return {
            "action_type": action_type,
            "title": title,
            "description": description,
            "why_it_matters": why,
            "expected_impact": f"Estimated +{self._estimate_gain(target_score)} pts to overall readiness score.",
            "related_goal": target_dimension.replace("_", " ").title(),
            "action_link": action_link,
            "impact_level": impact_level,
            "specific_item": specific_item,
            "current_sub_score": target_score,
        }

    def _estimate_gain(self, current_score: int) -> int:
        """Estimate readiness score gain from improving the worst dimension."""
        gap = 100 - current_score
        return min(int(gap * 0.3), 15)

    async def _get_specific_item(
        self,
        db: AsyncSession,
        user_id: str,
        dimension: str,
        priority_gaps: List[Dict],
    ) -> Dict:
        """Look for a specific actionable item within a dimension."""
        if dimension == "skill_readiness":
            # Find highest-priority skill gap
            skill_gaps = [g for g in priority_gaps if g["source"] == "skill_matrix"]
            if skill_gaps:
                top = skill_gaps[0]
                return {
                    "title": f"Learn: {top['name']}",
                    "description": f"Improve your {top['name']} from {top['current_level']} to {top['required_level']}",
                    "skill_name": top["name"],
                }
            return None

        if dimension == "resume_readiness":
            result = await db.execute(
                select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc()).limit(1)
            )
            resume = result.scalar_one_or_none()
            if resume and resume.improvement_suggestions:
                top_suggestion = resume.improvement_suggestions[0] if resume.improvement_suggestions else None
                if top_suggestion:
                    tip = top_suggestion if isinstance(top_suggestion, str) else top_suggestion.get("suggestion", "")
                    return {
                        "title": f"Resume Fix: {tip[:60]}...",
                        "description": tip,
                    }
            elif not resume:
                return {"title": "Upload Your Resume PDF", "description": "No resume uploaded yet."}
            return None

        if dimension == "interview_readiness":
            result = await db.execute(
                select(InterviewSession)
                .where(InterviewSession.user_id == user_id)
                .order_by(InterviewSession.created_at.desc())
                .limit(1)
            )
            last_session = result.scalar_one_or_none()
            if last_session and last_session.weak_areas:
                weak = last_session.weak_areas[0]
                topic = weak if isinstance(weak, str) else weak.get("topic", "")
                return {
                    "title": f"Practice: {topic}",
                    "description": f"You scored low on '{topic}'. Start a focused interview on this topic.",
                    "weak_topic": topic,
                }
            return {"title": "Start Your First Mock Interview", "description": "No sessions completed yet."}

        if dimension == "roadmap_progress":
            result = await db.execute(
                select(Roadmap)
                .where(Roadmap.user_id == user_id, Roadmap.is_active == True)
                .order_by(Roadmap.created_at.desc())
                .limit(1)
            )
            roadmap = result.scalar_one_or_none()
            if roadmap:
                completed = set(roadmap.completed_task_ids or [])
                for phase in (roadmap.phases or []):
                    for task in phase.get("tasks", []):
                        if task.get("id") not in completed:
                            return {
                                "title": f"Complete: {task.get('title', 'Next Task')}",
                                "description": task.get("why_matters", "Complete this task to advance your roadmap."),
                                "task_id": task.get("id"),
                            }
            return None

        return None

    def _default_action(self) -> Dict:
        return {
            "action_type": "complete_assessment",
            "title": "Complete Your Career Discovery Assessment",
            "description": "Start here to unlock your personalized career journey.",
            "why_it_matters": "This is the required first step to build your Career Digital Twin.",
            "expected_impact": "Unlocks all readiness scoring and personalized roadmap.",
            "related_goal": "Career Discovery",
            "action_link": "/assessment",
            "impact_level": "critical",
            "specific_item": None,
        }
