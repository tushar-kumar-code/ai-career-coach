import random
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.job import Job
from app.models.roadmap import Roadmap
from app.services.ai.client import AIService

logger = logging.getLogger(__name__)


class InterviewQuestionGenerator:
    """Service generating personalized, role-adaptive interview questions grounded in actual user profile & resume data."""

    def __init__(self, ai=None):
        self.ai = ai or AIService.get_provider()

    async def generate_question(
        self,
        db: AsyncSession,
        user_id: str,
        mode: str,
        difficulty: str,
        question_index: int,
        previous_evaluations: List[Dict[str, Any]],
        job_id: Optional[str] = None,
        target_role_override: Optional[str] = None,
        topic_focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a personalized question grounded in user evidence."""
        # 1. Fetch User Profile
        stmt_prof = select(UserProfile).where(UserProfile.user_id == user_id)
        res_prof = await db.execute(stmt_prof)
        profile = res_prof.scalar_one_or_none()

        target_role = target_role_override or (profile.target_career if profile and profile.target_career else "Software Developer")
        skills_matrix = profile.skills_matrix if profile and profile.skills_matrix else {}

        # 2. Fetch User Resume
        stmt_res = select(Resume).where(Resume.user_id == user_id)
        res_res = await db.execute(stmt_res)
        resume = res_res.scalars().first()

        parsed_projects = resume.parsed_projects if resume and resume.parsed_projects else []
        parsed_skills = resume.parsed_skills if resume and resume.parsed_skills else []
        parsed_experience = resume.parsed_experience if resume and resume.parsed_experience else []

        # 3. Fetch Job Details if Job-Specific
        job = None
        if job_id:
            stmt_j = select(Job).where(Job.id == job_id)
            res_j = await db.execute(stmt_j)
            job = res_j.scalars().first()

        # 4. Determine Effective Category for this question
        category = self._determine_category(mode, question_index)

        # 5. Build question text deterministically or via AI
        question_data = self._generate_deterministic_question(
            mode=mode,
            category=category,
            difficulty=difficulty,
            target_role=target_role,
            skills_matrix=skills_matrix,
            parsed_projects=parsed_projects,
            parsed_skills=parsed_skills,
            parsed_experience=parsed_experience,
            job=job,
            question_index=question_index,
            topic_focus=topic_focus
        )

        return question_data

    def _determine_category(self, mode: str, index: int) -> str:
        if mode == "Technical":
            return "Technical"
        elif mode == "HR":
            return "HR"
        elif mode == "Behavioral":
            return "Behavioral"
        elif mode == "Resume-Based":
            return "Resume-Based"
        elif mode == "Job-Specific":
            return "Job-Specific"
        else:  # Mixed
            pattern = ["Technical", "Resume-Based", "Behavioral", "Technical", "HR"]
            return pattern[index % len(pattern)]

    def _generate_deterministic_question(
        self,
        mode: str,
        category: str,
        difficulty: str,
        target_role: str,
        skills_matrix: Dict[str, Any],
        parsed_projects: List[Any],
        parsed_skills: List[Any],
        parsed_experience: List[Any],
        job: Optional[Job],
        question_index: int,
        topic_focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured question with context tip."""
        top_skill = topic_focus if topic_focus else (list(skills_matrix.keys())[0] if skills_matrix else "Python")
        proj_title = parsed_projects[0].get("title", "your portfolio project") if parsed_projects and isinstance(parsed_projects[0], dict) else "your major project"

        if category == "Technical":
            if difficulty == "Beginner":
                q_text = f"As a candidate for {target_role}, can you explain the core concepts of {top_skill} and why it is essential for modern software applications?"
                tip = f"Focus on core syntax, primary data structures, and practical use cases of {top_skill}."
            elif difficulty == "Intermediate":
                q_text = f"How would you handle asynchronous requests, error handling, and database connection pooling when building backend services in {top_skill}?"
                tip = "Explain concurrency patterns, try/except blocks, and connection lifecycle."
            else:  # Advanced
                q_text = f"Describe how you would architect a high-throughput microservice system handling thousands of concurrent users in {target_role}. What caching and database indexing strategies would you apply?"
                tip = "Discuss trade-offs, caching layers (Redis), database sharding/indexing, and API latency minimization."

        elif category == "Resume-Based":
            if parsed_projects:
                q_text = f"In your resume, you listed '{proj_title}'. Can you describe the technical architecture, key challenges you solved, and your individual contribution?"
                tip = f"Highlight your specific technical choices and measurable achievements in {proj_title}."
            else:
                q_text = f"Looking at your experience as {target_role}, what was the most complex technical task you completed, and what technologies did you use?"
                tip = "Be specific about tools, frameworks, and your exact responsibilities."

        elif category == "Behavioral":
            q_text = "Tell me about a time when you encountered a major obstacle or tight deadline while working on a software project. How did you prioritize tasks and communicate with team members?"
            tip = "Structure your answer using the STAR method (Situation, Task, Action, Result)."

        elif category == "HR":
            q_text = f"Why are you interested in pursuing a career as a {target_role}, and where do you see your technical growth over the next two years?"
            tip = "Align your personal career goals with continuous learning and technical mastery."

        elif category == "Job-Specific" and job:
            q_text = f"This position at {job.company} requires proficiency in {', '.join(job.required_skills[:3])}. Can you walk me through your experience applying these technologies in production?"
            tip = f"Directly connect your experience to {job.company}'s requirements."

        else:
            q_text = f"What is your approach to learning a brand new framework or technology required for a {target_role} position?"
            tip = "Demonstrate problem-solving agility and structured self-learning."

        return {
            "question_index": question_index,
            "category": category,
            "difficulty": difficulty,
            "question_text": q_text,
            "context_tip": tip
        }
