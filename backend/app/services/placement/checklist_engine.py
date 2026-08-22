import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.skill import Skill
from app.models.roadmap import Roadmap
from app.models.interview import InterviewSession
from app.models.job import JobApplication
from app.services.digital_twin.readiness_engine import ReadinessEngine
from app.services.digital_twin.gap_analyzer import GapAnalyzer
from app.schemas.placement import PlacementChecklistItem, PlacementChecklistResponse

logger = logging.getLogger(__name__)

# Centralized Placement Tiers & Student-Friendly Descriptions
PLACEMENT_TIERS: List[Tuple[int, str, str]] = [
    (
        85,
        "Placement Ready",
        "Your profile demonstrates strong preparation across skills, resume ATS, projects, and interviews. You are in a great position for on-campus & off-campus recruitment drives."
    ),
    (
        70,
        "Targeted Ready",
        "Solid foundation built for targeted technical roles. Closing 1–2 remaining gaps will maximize your interview shortlist rate."
    ),
    (
        50,
        "In Preparation",
        "Core skills established. Focus on building your capstone project, optimizing your resume ATS score, and completing mock interviews."
    ),
    (
        0,
        "Early Foundation",
        "You are just getting started. Follow your personalized roadmap and verify foundational skills to build strong placement readiness."
    ),
]


def get_placement_tier(score: int) -> Tuple[str, str]:
    """Translates a 0-100 readiness score into a placement readiness tier and student-friendly description."""
    for threshold, tier_name, tier_desc in PLACEMENT_TIERS:
        if score >= threshold:
            return tier_name, tier_desc
    return PLACEMENT_TIERS[-1][1], PLACEMENT_TIERS[-1][2]


class PlacementChecklistEngine:
    """
    Evaluates a 10-point Placement Readiness Checklist strictly against live DB facts.
    Never invents scores, percentages, or fake booleans.
    """

    def __init__(self):
        self.readiness_engine = ReadinessEngine()
        self.gap_analyzer = GapAnalyzer()

    async def evaluate_checklist(self, db: AsyncSession, user_id: str) -> PlacementChecklistResponse:
        """Runs the 10-point deterministic placement audit for a student."""
        # 1. Fetch live readiness scores (authoritative composite)
        readiness_data = await self.readiness_engine.compute(db, user_id)
        overall_score = readiness_data.get("overall_readiness_score", 0)
        tier_name, tier_desc = get_placement_tier(overall_score)

        # 2. Fetch gap analysis
        gap_data = await self.gap_analyzer.analyze(db, user_id)
        critical_missing_skills = gap_data.get("critical_missing_skills", [])

        # 3. Query User Profile
        p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        p_res = await db.execute(p_stmt)
        profile = p_res.scalar_one_or_none()
        target_career = profile.target_career if profile else None

        # 4. Query Latest Resume
        r_stmt = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
        r_res = await db.execute(r_stmt)
        latest_resume = r_res.scalar_one_or_none()

        # 5. Query Skills
        sk_stmt = select(Skill).where(Skill.user_id == user_id)
        sk_res = await db.execute(sk_stmt)
        user_skills = sk_res.scalars().all()
        verified_skills = [s for s in user_skills if s.is_verified]

        # 6. Query Active Roadmap
        rm_stmt = (
            select(Roadmap)
            .where(Roadmap.user_id == user_id, Roadmap.is_active == True)
            .order_by(Roadmap.created_at.desc())
            .limit(1)
        )
        rm_res = await db.execute(rm_stmt)
        active_roadmap = rm_res.scalar_one_or_none()
        completed_projects = active_roadmap.completed_project_ids if active_roadmap else []

        # 7. Query Interview Sessions
        iv_stmt = (
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id, InterviewSession.is_completed == True)
        )
        iv_res = await db.execute(iv_stmt)
        completed_interviews = iv_res.scalars().all()

        # 8. Query Job Applications
        app_stmt = select(JobApplication).where(JobApplication.user_id == user_id)
        app_res = await db.execute(app_stmt)
        applications = app_res.scalars().all()

        # -------------------------------------------------------------
        # EVALUATE 10 CHECKLIST ITEMS
        # -------------------------------------------------------------
        items: List[PlacementChecklistItem] = []

        # Item 1: Target Career Defined
        has_target = bool(target_career and len(target_career.strip()) > 0)
        items.append(PlacementChecklistItem(
            key="target_career",
            title="Target Career Role Defined",
            description="Select your target job profile to generate tailored skill requirements and curriculum.",
            category="Career Strategy",
            completed=has_target,
            current_value=target_career if has_target else "Not set",
            target_value="1 Target Role",
            action_title="Select Target Career" if not has_target else "Review Career Profile",
            action_route="/assessment" if not has_target else "/profile"
        ))

        # Item 2: Resume Uploaded
        has_resume = bool(latest_resume is not None)
        items.append(PlacementChecklistItem(
            key="resume_uploaded",
            title="Resume Document Uploaded",
            description="Upload your latest PDF or DOCX resume to extract verified skills and assess ATS readiness.",
            category="Resume & ATS",
            completed=has_resume,
            current_value=latest_resume.filename if has_resume else "No resume uploaded",
            target_value="PDF / DOCX Resume",
            action_title="Upload Resume" if not has_resume else "Manage Resume",
            action_route="/resume"
        ))

        # Item 3: ATS Score Optimization (>= 70%)
        ats_score = latest_resume.overall_ats_score if latest_resume else 0
        ats_completed = ats_score >= 70
        items.append(PlacementChecklistItem(
            key="ats_optimization",
            title="ATS Screening Score ≥ 70%",
            description="Ensure your resume passes automated company applicant tracking systems without keyword or formatting blockers.",
            category="Resume & ATS",
            completed=ats_completed,
            current_value=f"{ats_score}%" if has_resume else "0%",
            target_value="≥ 70%",
            action_title="Improve ATS Score" if not ats_completed else "View ATS Report",
            action_route="/resume"
        ))

        # Item 4: Core Skills Verified (>= 3 verified skills)
        verified_count = len(verified_skills)
        skills_completed = verified_count >= 3
        items.append(PlacementChecklistItem(
            key="core_skills_verified",
            title="Core Technical Skills Verified (≥ 3)",
            description="Demonstrate concrete proof for at least 3 required technologies via resume, assessments, or interviews.",
            category="Skill Mastery",
            completed=skills_completed,
            current_value=f"{verified_count} verified",
            target_value="≥ 3 verified skills",
            action_title="Verify Skills" if not skills_completed else "View Skill Matrix",
            action_route="/skills"
        ))

        # Item 5: Critical Skill Gaps Closed
        critical_count = len(critical_missing_skills)
        gaps_completed = has_target and critical_count == 0
        items.append(PlacementChecklistItem(
            key="critical_skill_gaps",
            title="Zero Critical Skill Gaps",
            description="Master all must-have prerequisite skills demanded by employers for your target career role.",
            category="Skill Mastery",
            completed=gaps_completed,
            current_value=f"{critical_count} critical missing" if critical_count > 0 else ("All closed ✓" if has_target else "Target not set"),
            target_value="0 critical gaps",
            action_title="Close Skill Gaps" if not gaps_completed else "Review Skill Matrix",
            action_route="/skills"
        ))

        # Item 6: DSA / Micro Practice Completed
        practice_count = len(completed_interviews)
        practice_completed = practice_count >= 1
        items.append(PlacementChecklistItem(
            key="micro_practice",
            title="Skill & DSA Micro Practice Completed",
            description="Complete focused 3-question micro practice drills to strengthen conceptual and problem-solving accuracy.",
            category="Interview & Practice",
            completed=practice_completed,
            current_value=f"{practice_count} session(s) completed" if practice_completed else "0 completed",
            target_value="≥ 1 practice session",
            action_title="Start Micro Practice" if not practice_completed else "Practice More Topics",
            action_route="/practice"
        ))

        # Item 7: Capstone Portfolio Project (>= 1 project)
        project_count = len(completed_projects)
        project_completed = project_count >= 1
        items.append(PlacementChecklistItem(
            key="portfolio_project",
            title="Portfolio Project Completed (≥ 1)",
            description="Build a production-grade portfolio project that provides concrete proof of competency on your resume.",
            category="Portfolio",
            completed=project_completed,
            current_value=f"{project_count} project(s) completed" if project_completed else "0 completed",
            target_value="≥ 1 project",
            action_title="Build Roadmap Project" if not project_completed else "View Projects in Roadmap",
            action_route="/roadmap"
        ))

        # Item 8: Technical Mock Interview (Score >= 65%)
        max_tech_score = 0
        for s in completed_interviews:
            cat_scores = s.category_scores or {}
            tech_s = cat_scores.get("technical", s.overall_score)
            if tech_s > max_tech_score:
                max_tech_score = tech_s

        tech_interview_completed = max_tech_score >= 65
        items.append(PlacementChecklistItem(
            key="technical_interview",
            title="Technical Mock Interview (Score ≥ 65%)",
            description="Clear an adaptive technical interview covering domain concepts and problem-solving.",
            category="Interview & Practice",
            completed=tech_interview_completed,
            current_value=f"{max_tech_score}% best score" if completed_interviews else "None completed",
            target_value="≥ 65%",
            action_title="Take Technical Interview" if not tech_interview_completed else "Practice Again",
            action_route="/interview"
        ))

        # Item 9: Behavioral STAR Interview Verified
        star_completed = False
        for s in completed_interviews:
            # Check question data evaluations for star_complete
            q_data = s.questions_data or []
            for q in q_data:
                ev = q.get("evaluation") or {}
                star_a = ev.get("star_analysis") or {}
                if star_a.get("star_complete"):
                    star_completed = True
                    break
            if star_completed:
                break
            # Fallback: behavioral score >= 70
            cat_scores = s.category_scores or {}
            if cat_scores.get("behavioral", 0) >= 70:
                star_completed = True
                break

        items.append(PlacementChecklistItem(
            key="behavioral_star_interview",
            title="Behavioral STAR Interview Coaching Cleared",
            description="Structure HR responses with all 4 components (Situation, Task, Action, Result) for campus HR rounds.",
            category="Interview & Practice",
            completed=star_completed,
            current_value="STAR verified ✓" if star_completed else "Needs practice",
            target_value="STAR Complete",
            action_title="Practice STAR Method" if not star_completed else "Refine STAR Answers",
            action_route="/practice?topic=STAR%20Method"
        ))

        # Item 10: Campus Applications Pipeline (>= 1 tracked application)
        app_count = len(applications)
        app_completed = app_count >= 1
        items.append(PlacementChecklistItem(
            key="application_pipeline",
            title="Campus / Job Applications Tracked (≥ 1)",
            description="Maintain an active job or internship application pipeline and track status transitions.",
            category="Application Pipeline",
            completed=app_completed,
            current_value=f"{app_count} application(s) tracked" if app_completed else "0 tracked",
            target_value="≥ 1 application",
            action_title="Track First Application" if not app_completed else "View Application Pipeline",
            action_route="/jobs"
        ))

        # Counts & percent
        completed_count = sum(1 for item in items if item.completed)
        total_count = len(items)
        completion_percent = int(round((completed_count / total_count) * 100)) if total_count > 0 else 0

        return PlacementChecklistResponse(
            overall_readiness_score=overall_score,
            readiness_tier=tier_name,
            tier_description=tier_desc,
            completed_count=completed_count,
            total_count=total_count,
            checklist_completion_percent=completion_percent,
            items=items
        )
