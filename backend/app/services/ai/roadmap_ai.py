import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from app.services.ai.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


class AIRoadmapTaskContent(BaseModel):
    title: str = Field(description="Actionable title of daily task")
    description: str = Field(description="Clear learning or practice instructions")
    estimated_minutes: int = Field(description="Estimated time in minutes (e.g. 20-45)")
    task_type: str = Field(description="Task category: Learn, Practice, Project, or Review")
    why_it_matters: str = Field(description="Personalized rationale explaining importance for target role")
    # Learning resource fields — added for Phase 3
    concept_explanation: str = Field(
        default="",
        description="2-3 sentence plain-English explanation of the core concept (no jargon). What is it and why does it exist?"
    )
    practice_exercise: str = Field(
        default="",
        description="One specific, small, actionable hands-on exercise the student can do right now (e.g., 'Write a SQL query that uses INNER JOIN to combine two tables')."
    )
    check_quiz_question: str = Field(
        default="",
        description="One short multiple-choice quiz question to check understanding."
    )
    check_quiz_options: List[str] = Field(
        default_factory=list,
        description="3 answer options labeled A), B), C). Exactly one should be correct."
    )
    check_quiz_answer: str = Field(
        default="",
        description="The correct answer letter and a one-sentence explanation (e.g., 'A) Because ...')."
    )


class AIProjectIdea(BaseModel):
    title: str = Field(description="Hands-on portfolio project title")
    objective: str = Field(description="Core project objective and scope")
    skills_practiced: List[str] = Field(default_factory=list, description="Skills reinforced in project")
    difficulty: str = Field(description="Difficulty level: Beginner, Intermediate, or Advanced")
    expected_outcome: str = Field(description="Concrete deliverable (e.g., Working REST API, Interactive UI Dashboard)")
    resume_relevance: str = Field(description="How this project strengthens candidate's resume for target role")


class AIRoadmapPhaseContent(BaseModel):
    phase_title: str = Field(description="Descriptive title of roadmap phase")
    learning_objectives: List[str] = Field(default_factory=list, description="Core phase learning objectives")
    milestone_title: str = Field(description="Milestone title for this phase")
    milestone_criteria: str = Field(description="Concrete criteria to verify milestone completion")
    tasks: List[AIRoadmapTaskContent] = Field(default_factory=list, description="Structured actionable tasks")
    project: Optional[AIProjectIdea] = Field(default=None, description="Hands-on phase project recommendation")


class RoadmapAIService:
    """Dedicated AI Service generating personalized learning objectives, task content, and project ideas using Gemini Provider."""

    def __init__(self):
        self.provider = GeminiProvider()

    async def generate_phase_content(
        self,
        phase_number: int,
        phase_type: str,
        target_career: str,
        phase_skills: List[str],
        user_known_skills: List[str],
        learning_style: str = "Hands-on",
        hours_per_day: int = 1
    ) -> AIRoadmapPhaseContent:
        """Generates structured learning tasks, objectives, learning resources, and project for a roadmap phase."""
        prompt = f"""
You are an expert AI Career Coach building Phase {phase_number} ({phase_type}) of a personalized roadmap for a student targeting '{target_career}'.

Skills in this Phase: {', '.join(phase_skills) if phase_skills else 'General Readiness'}
Already Verified User Skills: {', '.join(user_known_skills[:8]) if user_known_skills else 'None'}
Preferred Learning Style: {learning_style}
Available Daily Time: {hours_per_day} hour(s)/day

Generate a highly tailored phase plan containing:
1. 3-4 specific learning objectives.
2. A clear milestone title and verification criteria.
3. 3-4 actionable daily tasks. For each task include:
   - title: short, action-oriented task title
   - description: clear 1-2 sentence instruction
   - estimated_minutes: realistic time estimate (fit {hours_per_day}h budget)
   - task_type: one of Learn | Practice | Project | Review
   - why_it_matters: 1 sentence explaining career relevance
   - concept_explanation: 2-3 plain-English sentences explaining the core concept. Avoid jargon. Target a 2nd-year CS student.
   - practice_exercise: one specific, small, immediately actionable exercise (e.g., write code, build a tiny demo, fill a template)
   - check_quiz_question: one clear multiple-choice question to test understanding
   - check_quiz_options: exactly 3 options labeled "A) ...", "B) ...", "C) ..."
   - check_quiz_answer: the correct letter + a 1-sentence explanation (e.g., "A) Because...")
4. A concrete, portfolio-worthy project recommendation that reinforces the phase skills and boosts resume relevance.

Do NOT generate generic fluff. Everything must be specific to {target_career} and the skills listed.
"""
        try:
            return await self.provider.generate_structured(
                prompt=prompt,
                output_schema=AIRoadmapPhaseContent,
                system_instruction="You are a senior technical curriculum architect creating personalized career roadmaps for CS students."
            )
        except Exception as e:
            logger.warning(f"Gemini roadmap phase content fallback: {e}")
            skills_str = ", ".join(phase_skills[:2]) if phase_skills else "Target Requirements"
            skill_0 = phase_skills[0] if phase_skills else "this skill"
            return AIRoadmapPhaseContent(
                phase_title=f"Phase {phase_number}: {phase_type} ({skills_str})",
                learning_objectives=[
                    f"Master core concepts and syntax of {skills_str}.",
                    f"Apply {skills_str} in practical exercise scenarios.",
                    f"Build production-grade projects demonstrating {target_career} proficiency."
                ],
                milestone_title=f"{skills_str} Mastery Milestone",
                milestone_criteria=f"Successfully build and verify a project demonstrating {skills_str} for {target_career}.",
                tasks=[
                    AIRoadmapTaskContent(
                        title=f"Learn {skill_0} Fundamentals",
                        description=f"Study core documentation and fundamental concepts for {skill_0}.",
                        estimated_minutes=30,
                        task_type="Learn",
                        why_it_matters=f"Essential foundation required for {target_career} role.",
                        concept_explanation=f"{skill_0} is a core technology used in {target_career}. Understanding its fundamentals helps you build reliable, maintainable applications. Most companies expect hands-on familiarity from day one.",
                        practice_exercise=f"Write a small working example using {skill_0} — for example, implement the simplest possible use case (e.g., a 'Hello World' equivalent for {skill_0}) and verify it runs without errors.",
                        check_quiz_question=f"What is the primary purpose of {skill_0} in a {target_career} project?",
                        check_quiz_options=[
                            f"A) It handles the core {target_career} functionality efficiently",
                            f"B) It is only used for documentation purposes",
                            f"C) It replaces all other technologies in the stack"
                        ],
                        check_quiz_answer=f"A) {skill_0} is a core building block that directly enables the key functionality expected in {target_career} roles."
                    ),
                    AIRoadmapTaskContent(
                        title=f"Practice {skill_0} Hands-on Exercises",
                        description=f"Implement 2-3 code examples using {skill_0}.",
                        estimated_minutes=30,
                        task_type="Practice",
                        why_it_matters=f"Solidifies conceptual understanding with practical experience.",
                        concept_explanation=f"Practice is how concepts become skills. With {skill_0}, the gap between reading documentation and actually using it in a project is large — hands-on exercises close that gap fast.",
                        practice_exercise=f"Take the example you built in the Learn task and extend it: add error handling, a second feature, or refactor it to follow a best practice you read about.",
                        check_quiz_question=f"When is the best time to add error handling to your {skill_0} code?",
                        check_quiz_options=[
                            "A) From the very beginning, not as an afterthought",
                            "B) Only after the project is fully deployed",
                            "C) It is optional and only for senior developers"
                        ],
                        check_quiz_answer="A) Error handling should be built in from the start to prevent unexpected failures in production."
                    )
                ],
                project=AIProjectIdea(
                    title=f"Build {target_career} {skills_str} Showcase App",
                    objective=f"Develop an end-to-end practical application implementing {skills_str}.",
                    skills_practiced=phase_skills,
                    difficulty="Intermediate",
                    expected_outcome=f"Working application featuring {skills_str} integration.",
                    resume_relevance=f"Provides concrete evidence of {skills_str} competency on resume for {target_career}."
                )
            )
