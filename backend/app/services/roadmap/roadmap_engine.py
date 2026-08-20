import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.profile import UserProfile
from app.models.career_catalog import CareerRole
from app.models.roadmap import Roadmap
from app.services.roadmap.dependency_graph import topological_sort_skills
from app.services.ai.roadmap_ai import RoadmapAIService
from app.schemas.roadmap import (
    RoadmapDetailResponse,
    RoadmapPhaseSchema,
    RoadmapTaskSchema,
    RoadmapProjectSchema,
    RoadmapMilestoneSchema,
    RoadmapSkillItem
)

logger = logging.getLogger(__name__)


# Default fallback skills per career domain
ROLE_DEFAULT_SKILLS: Dict[str, List[str]] = {
    "Software Developer": ["Programming Fundamentals", "Git", "HTML/CSS", "JavaScript", "Python", "SQL", "REST APIs", "Unit Testing"],
    "Frontend Developer": ["HTML/CSS", "JavaScript", "TypeScript", "React", "Next.js", "Git", "REST APIs", "Unit Testing"],
    "Backend Developer": ["Python", "FastAPI", "SQL", "PostgreSQL", "REST APIs", "Git", "Docker", "Unit Testing"],
    "Full Stack Engineer": ["HTML/CSS", "JavaScript", "React", "Python", "FastAPI", "SQL", "Git", "Docker", "REST APIs"],
    "Data Analyst": ["Excel", "SQL", "Python", "Pandas", "NumPy", "Data Visualization", "Power BI", "Statistics"],
    "Data Scientist": ["Python", "SQL", "Pandas", "NumPy", "Statistics", "Machine Learning", "Deep Learning", "Data Visualization"],
    "DevOps Engineer": ["Linux Basics", "Networking", "Git", "Docker", "Kubernetes", "CI/CD", "Python", "Security Fundamentals"],
    "Cybersecurity Analyst": ["Networking", "Linux Basics", "Security Fundamentals", "Threat Analysis", "SIEM", "Python"],
    "Product Manager": ["Agile/Scrum", "User Research", "Product Strategy", "Data-Driven Decisions", "SQL"]
}


class RoadmapEngine:
    def __init__(self):
        self.ai_service = RoadmapAIService()

    async def generate_user_roadmap(
        self,
        db: AsyncSession,
        user_id: str,
        user_level: str = "Beginner",
        hours_per_day: int = 1,
        days_per_week: int = 5,
        preferred_learning_style: str = "Hands-on",
        target_career_id: Optional[str] = None
    ) -> Roadmap:
        """Generate a personalized, dependency-ordered, AI-enriched career roadmap."""
        # 1. Fetch User Profile
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        res = await db.execute(stmt)
        profile = res.scalar_one_or_none()

        target_role_name = profile.target_career if profile and profile.target_career else "Software Developer"
        skills_matrix = profile.skills_matrix if profile and profile.skills_matrix else {}

        # 2. Get target role required skills from CareerRole catalog or defaults
        required_skills: List[str] = []
        stmt_role = select(CareerRole).where(CareerRole.title == target_role_name)
        res_role = await db.execute(stmt_role)
        career_obj = res_role.scalar_one_or_none()

        if career_obj and career_obj.required_skills:
            required_skills = career_obj.required_skills
        else:
            required_skills = ROLE_DEFAULT_SKILLS.get(target_role_name, ROLE_DEFAULT_SKILLS["Software Developer"])

        # 3. Categorize user verified skills vs gaps
        verified_skills: List[str] = []
        skill_gaps: List[str] = []

        for s in required_skills:
            s_data = skills_matrix.get(s, {})
            confidence = s_data.get("confidence_level", "Missing")
            if confidence in ["Verified", "Supported"]:
                verified_skills.append(s)
            else:
                skill_gaps.append(s)

        # Ensure all required skills are included if no gaps found
        all_skills_to_order = required_skills

        # 4. Apply Topological Sort (Prerequisites -> Advanced)
        sorted_skills = topological_sort_skills(all_skills_to_order)

        # 5. Group skills into adaptive roadmap phases
        phase_groups = self._partition_skills_into_phases(sorted_skills, verified_skills, target_role_name)

        # 6. Build phase JSON models and enrich with AI objectives, tasks, projects, milestones
        built_phases: List[Dict[str, Any]] = []
        total_estimated_hours = 0

        for idx, (p_id, p_name, p_desc, p_skills) in enumerate(phase_groups, start=1):
            # Calculate skills objects for phase
            skill_items = []
            for sk in p_skills:
                is_ver = sk in verified_skills
                skill_items.append({
                    "name": sk,
                    "status": "Verified" if is_ver else "Missing",
                    "priority": "Essential" if idx <= 2 else "Core",
                    "level": user_level
                })

            # AI / Fallback Enrichment
            enrichment = await self.ai_service.enrich_phase(
                target_role=target_role_name,
                user_level=user_level,
                preferred_style=preferred_learning_style,
                phase_name=p_name,
                skills=p_skills,
                verified_skills=verified_skills
            )

            # Assign unique task/project/milestone IDs
            phase_tasks = []
            for t_idx, t in enumerate(enrichment.tasks, start=1):
                task_id = f"p{idx}_t{t_idx}_{uuid.uuid4().hex[:6]}"
                est_min = t.get("estimated_minutes", 30)
                total_estimated_hours += est_min / 60.0
                phase_tasks.append({
                    "id": task_id,
                    "title": t.get("title", f"Task {t_idx}"),
                    "skill": t.get("skill", p_skills[0] if p_skills else "General"),
                    "estimated_minutes": est_min,
                    "why_matters": t.get("why_matters", f"Essential for {target_role_name}."),
                    "practice_activity": t.get("practice_activity", "Practice coding lab."),
                    "completed": False,
                    "completed_at": None
                })

            phase_projects = []
            for pr_idx, pr in enumerate(enrichment.projects, start=1):
                proj_id = f"p{idx}_proj{pr_idx}_{uuid.uuid4().hex[:6]}"
                phase_projects.append({
                    "id": proj_id,
                    "title": pr.get("title", f"{p_name} Capstone Project"),
                    "objective": pr.get("objective", "Build a real-world application."),
                    "skills_practiced": pr.get("skills_practiced", p_skills),
                    "difficulty": pr.get("difficulty", "Intermediate"),
                    "expected_outcome": pr.get("expected_outcome", "Production repository"),
                    "resume_relevance": pr.get("resume_relevance", "High impact resume item"),
                    "completed": False
                })

            phase_milestones = []
            for m_idx, m in enumerate(enrichment.milestones, start=1):
                m_id = f"p{idx}_m{m_idx}_{uuid.uuid4().hex[:6]}"
                phase_milestones.append({
                    "id": m_id,
                    "title": m.get("title", f"{p_name} Completion"),
                    "criteria": m.get("criteria", "Complete tasks & verify skills."),
                    "completed": False
                })

            est_weeks = max(1, round(len(phase_tasks) * 0.75))

            built_phases.append({
                "phase_id": f"phase_{idx}",
                "name": p_name,
                "description": p_desc,
                "estimated_weeks": est_weeks,
                "skills": skill_items,
                "learning_objectives": enrichment.learning_objectives,
                "tasks": phase_tasks,
                "projects": phase_projects,
                "milestones": phase_milestones
            })

        # 7. Calculate overall estimated weeks based on weekly study budget
        weekly_hours = hours_per_day * days_per_week
        total_estimated_weeks = max(2, int(round(total_estimated_hours / max(weekly_hours, 1))))

        # 8. Deactivate previous active roadmaps for user
        stmt_old = select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active == True)
        res_old = await db.execute(stmt_old)
        old_roadmaps = res_old.scalars().all()
        for r in old_roadmaps:
            r.is_active = False

        # 9. Create and save new Roadmap record
        new_roadmap = Roadmap(
            id=str(uuid.uuid4()),
            user_id=user_id,
            target_career_id=target_career_id,
            target_role=target_role_name,
            user_level=user_level,
            overall_progress_percent=0,
            is_active=True,
            is_outdated=False,
            hours_per_day=hours_per_day,
            days_per_week=days_per_week,
            preferred_learning_style=preferred_learning_style,
            total_estimated_weeks=total_estimated_weeks,
            phases=built_phases,
            completed_task_ids=[],
            completed_milestone_ids=[],
            completed_project_ids=[]
        )

        db.add(new_roadmap)
        await db.commit()
        await db.refresh(new_roadmap)
        return new_roadmap

    def _partition_skills_into_phases(
        self,
        sorted_skills: List[str],
        verified_skills: List[str],
        target_role: str
    ) -> List[tuple]:
        """Partition ordered skills into role-adaptive phases."""
        total = len(sorted_skills)
        if total <= 3:
            p1_skills = sorted_skills[:1]
            p2_skills = sorted_skills[1:2]
            p3_skills = sorted_skills[2:]
        elif total <= 6:
            p1_skills = sorted_skills[:2]
            p2_skills = sorted_skills[2:4]
            p3_skills = sorted_skills[4:]
        else:
            n = total // 3
            p1_skills = sorted_skills[:n]
            p2_skills = sorted_skills[n:2*n]
            p3_skills = sorted_skills[2*n:]

        # Customize phase titles based on target role domain
        if "Data" in target_role:
            ph1_name, ph1_desc = "Phase 1 — Data Foundations & Querying", "Master core data querying, spreadsheet tools, and prerequisite programming syntax."
            ph2_name, ph2_desc = "Phase 2 — Core Analytics & Visualization", "Build statistical models, clean datasets with Python/Pandas, and create dashboards."
            ph3_name, ph3_desc = "Phase 3 — Advanced Data Engineering & ML", "Implement advanced analytics, machine learning pipelines, and database optimization."
        elif "DevOps" in target_role or "Security" in target_role:
            ph1_name, ph1_desc = "Phase 1 — Systems & Networking Foundations", "Master Linux terminal navigation, shell scripting, and core networking."
            ph2_name, ph2_desc = "Phase 2 — Infrastructure & Automation", "Configure containerization, CI/CD pipelines, and cloud security controls."
            ph3_name, ph3_desc = "Phase 3 — Orchestration & Threat Monitoring", "Deploy scalable Kubernetes clusters, SIEM monitoring, and automated auditing."
        else:
            ph1_name, ph1_desc = "Phase 1 — Core Foundations & Syntax", "Master essential syntax, version control, and core software architecture principles."
            ph2_name, ph2_desc = "Phase 2 — Key Frameworks & APIs", "Develop scalable backend/frontend modules, REST APIs, and database integrations."
            ph3_name, ph3_desc = "Phase 3 — Advanced Architecture & Testing", "Implement end-to-end unit testing, state management, and performance tuning."

        ph4_name, ph4_desc = "Phase 4 — Portfolio Projects & Capstones", "Build production-ready projects to demonstrate technical competence on your resume."
        ph5_name, ph5_desc = "Phase 5 — Interview Preparation & Job Readiness", "Practice STAR behavioral interviews, ATS resume optimization, and mock technical assessments."

        phases = [
            ("phase_1", ph1_name, ph1_desc, p1_skills if p1_skills else sorted_skills[:1]),
            ("phase_2", ph2_name, ph2_desc, p2_skills if p2_skills else sorted_skills[1:2]),
            ("phase_3", ph3_name, ph3_desc, p3_skills if p3_skills else sorted_skills[2:]),
            ("phase_4", ph4_name, ph4_desc, sorted_skills[:3]),
            ("phase_5", ph5_name, ph5_desc, sorted_skills[-2:] if len(sorted_skills) >= 2 else sorted_skills)
        ]
        return phases

    def calculate_progress(self, roadmap: Roadmap) -> int:
        """Calculate exact deterministic progress percentage based on completed tasks."""
        total_tasks = 0
        for phase in (roadmap.phases or []):
            tasks = phase.get("tasks", [])
            total_tasks += len(tasks)

        if total_tasks == 0:
            return 0

        completed_count = len(roadmap.completed_task_ids or [])
        progress_pct = int(round((completed_count / total_tasks) * 100))
        return min(100, max(0, progress_pct))
