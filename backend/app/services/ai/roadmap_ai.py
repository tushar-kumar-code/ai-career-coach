import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from app.services.ai.client import AIService

logger = logging.getLogger(__name__)



class AIRoadmapTaskContent(BaseModel):
    title: str = Field(description="Actionable title of topic/module to learn")
    description: str = Field(description="Clear overview of what this topic covers and why it fits here")
    estimated_minutes: int = Field(description="Estimated study & practice time in minutes (e.g. 30-60)")
    task_type: str = Field(description="Task category: Learn, Practice, Project, or Review")
    why_it_matters: str = Field(description="Personalized rationale explaining importance for target role")
    # Topic-wise syllabus & guidance fields (tells user WHAT to learn)
    topics_to_learn: List[str] = Field(
        default_factory=list,
        description="Detailed list of 4-6 specific subtopics, concepts, keywords, or syntax rules the student must cover"
    )
    learning_focus: str = Field(
        default="",
        description="Clear advice on what to prioritize or watch out for while studying this topic"
    )
    practice_goal: str = Field(
        default="",
        description="Specific hands-on coding task, exercise, or mini-program to build to verify understanding"
    )
    recommended_resources: List[str] = Field(
        default_factory=list,
        description="Recommended standard documentation topics, tutorials, or search queries (e.g. 'MDN - JS Functions', 'Official Docs')"
    )
    difficulty_level: str = Field(
        default="Beginner",
        description="Difficulty tier: Scratch, Beginner, Intermediate, or Advanced"
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Key prerequisites required before tackling this topic"
    )
    # Legacy fields for backwards compatibility
    concept_explanation: str = Field(default="")
    practice_exercise: str = Field(default="")
    check_quiz_question: str = Field(default="")
    check_quiz_options: List[str] = Field(default_factory=list)
    check_quiz_answer: str = Field(default="")


class AIProjectIdea(BaseModel):
    title: str = Field(description="Hands-on portfolio project title")
    objective: str = Field(description="Core project objective and scope")
    skills_practiced: List[str] = Field(default_factory=list, description="Skills reinforced in project")
    difficulty: str = Field(description="Difficulty level: Scratch, Beginner, Intermediate, or Advanced")
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
    """Dedicated AI Service generating personalized learning objectives, task content, and project ideas."""

    def __init__(self, provider=None):
        self.provider = provider or AIService.get_provider()

    async def generate_phase_content(
        self,
        phase_number: int,
        phase_type: str,
        target_career: str,
        phase_skills: List[str],
        user_known_skills: List[str],
        user_level: str = "Beginner",
        learning_style: str = "Hands-on",
        hours_per_day: int = 1
    ) -> AIRoadmapPhaseContent:
        """Generates structured learning syllabus, objectives, topic checklist, and project for a roadmap phase."""
        is_beginner = user_level.lower() in ["beginner", "scratch"] or len(user_known_skills) == 0

        scratch_guidance = (
            "THE USER IS A COMPLETE BEGINNER (OR STARTS FROM SCRATCH). "
            "Assume ZERO prior programming or technical knowledge. Explain WHAT to learn in simple, accessible, "
            "step-by-step topics. Never jump to complex frameworks without laying foundational syntax and logic first."
            if is_beginner else
            f"The user has experience level '{user_level}'. Build on their verified foundation and bridge exact gaps."
        )

        prompt = f"""
You are an expert Principal Curriculum Architect creating Phase {phase_number} ({phase_type}) of a complete career roadmap for a student aiming to become a '{target_career}'.

{scratch_guidance}

Phase Details:
- Phase Number: {phase_number}
- Phase Type: {phase_type}
- Targeted Skills in this Phase: {', '.join(phase_skills) if phase_skills else 'Core Foundations'}
- User Verified Skills: {', '.join(user_known_skills[:8]) if user_known_skills else 'None (Starting from scratch)'}
- User Level: {user_level}
- Learning Style: {learning_style}
- Daily Study Budget: {hours_per_day} hour(s)/day

CRITICAL GUIDELINES (STRICT COMPLIANCE REQUIRED):
1. WHAT TO LEARN, NOT TEACHING: Your goal is to tell the student EXACTLY WHAT TO LEARN (curriculum, syllabus, key topics, subtopics, and practice milestones). DO NOT try to lecture, write miniature textbook lessons, or teach the content here. The roadmap is a clear, structured navigation guide.
2. DETAILED TOPIC-WISE BREAKDOWN: Each task MUST represent a distinct, logical topic. Provide an exhaustive list of 4-6 specific sub-topics/concepts (`topics_to_learn`) so the student knows exactly what to cover with zero guesswork.
3. ADAPT TO USER LEVEL: If the user is starting from scratch, start from the absolute ground zero (prerequisites, setup, basic concepts). Never skip steps or make steep difficulty leaps.
4. ACCURACY & COMPLETENESS: Ensure topics reflect modern, industry-standard best practices for '{target_career}'.

Generate:
1. 3-4 clear learning objectives for this phase.
2. A concrete milestone title and verification criteria.
3. 3-4 structured, topic-wise daily tasks. For each task provide:
   - title: Specific topic name (e.g. "JavaScript Basics: Variables, Data Types & Operators" or "FastAPI: Request Validation & Pydantic Models")
   - description: 1-2 sentence overview of what this topic covers and why it fits here in the journey
   - estimated_minutes: Realistic time estimate (30-60 mins fitting {hours_per_day}h budget)
   - task_type: One of Learn | Practice | Project | Review
   - why_it_matters: 1 sentence on why this is necessary for {target_career}
   - topics_to_learn: Exactly 4-6 concrete sub-topics, syntax points, or concepts to learn (e.g. ["let vs const vs var", "Primitive types (string, number, boolean)", "Template literals", "Comparison operators (== vs ===)"])
   - learning_focus: 1-2 sentences on what key concept to focus on while self-studying
   - practice_goal: One specific hands-on exercise or mini-program to code and verify
   - recommended_resources: 2-3 standard topics or official docs to look up (e.g. ["MDN JavaScript Guide", "W3Schools JS Basics"])
   - difficulty_level: Scratch, Beginner, Intermediate, or Advanced
   - prerequisites: 1-2 prerequisite concepts (or ["None - Starts from Scratch"])
4. A concrete, portfolio-worthy project recommendation that reinforces the phase skills and boosts resume relevance.

Do NOT generate generic fluff. Everything must be accurate, specific, and tailored for {target_career}.
"""
        try:
            return await self.provider.generate_structured(
                prompt=prompt,
                output_schema=AIRoadmapPhaseContent,
                system_instruction="You are a senior technical curriculum architect creating personalized, zero-difficulty career roadmaps."
            )
        except Exception as e:
            logger.warning(f"Gemini roadmap phase content fallback: {e}")
            skills_str = ", ".join(phase_skills[:2]) if phase_skills else "Target Requirements"
            skill_0 = phase_skills[0] if phase_skills else "Core Programming"
            
            diff_level = "Scratch" if is_beginner and phase_number == 1 else ("Beginner" if is_beginner else "Intermediate")
            
            return AIRoadmapPhaseContent(
                phase_title=f"Phase {phase_number}: {phase_type} ({skills_str})",
                learning_objectives=[
                    f"Understand the core syntax, mental model, and fundamental principles of {skills_str}.",
                    f"Master the essential subtopics and development patterns of {skills_str}.",
                    f"Build hands-on practical exercises demonstrating practical competence for {target_career}."
                ],
                milestone_title=f"{skills_str} Practical Competence Milestone",
                milestone_criteria=f"Complete hands-on implementation demonstrating end-to-end understanding of {skills_str} for {target_career}.",
                tasks=[
                    AIRoadmapTaskContent(
                        title=f"{skill_0}: Core Fundamentals & Syntax",
                        description=f"Learn the foundational principles, syntax conventions, and essential building blocks of {skill_0}.",
                        estimated_minutes=45,
                        task_type="Learn",
                        why_it_matters=f"Forms the foundational bedrock required for all subsequent {target_career} technical work.",
                        topics_to_learn=[
                            f"{skill_0} environment setup and execution basics",
                            "Variables, data types, and naming conventions",
                            "Operators, expressions, and evaluation rules",
                            "Basic input/output and code debugging"
                        ],
                        learning_focus=f"Focus on understanding the execution flow and foundational rules of {skill_0} before moving to advanced features.",
                        practice_goal=f"Write a simple standalone script in {skill_0} implementing variables, arithmetic operations, and console output.",
                        recommended_resources=[
                            f"Official {skill_0} Documentation - Getting Started",
                            f"{skill_0} Syntax & Fundamentals Guide"
                        ],
                        difficulty_level=diff_level,
                        prerequisites=["None - Starts from Scratch"] if is_beginner else ["Basic logic building"]
                    ),
                    AIRoadmapTaskContent(
                        title=f"{skill_0}: Control Flow, Functions & Modular Code",
                        description=f"Learn conditional logic, loops, and reusable modular functions in {skill_0}.",
                        estimated_minutes=45,
                        task_type="Practice",
                        why_it_matters=f"Required to write dynamic logic and clean, maintainable code for {target_career} applications.",
                        topics_to_learn=[
                            "Conditional branching (if, else if, else)",
                            "Looping constructs (for, while, iteration)",
                            "Function definitions, parameters, and return values",
                            "Variable scope and code modularity"
                        ],
                        learning_focus="Focus on breaking down problems into small, reusable functions with clear input and output.",
                        practice_goal="Build 2 small logic programs (e.g. a temperature converter, a number guessing game, or a basic calculator).",
                        recommended_resources=[
                            f"Official {skill_0} Functions Tutorial",
                            "FreeCodeCamp - Programming Logic and Control Flow"
                        ],
                        difficulty_level=diff_level,
                        prerequisites=[f"{skill_0} Fundamentals & Syntax"]
                    ),
                    AIRoadmapTaskContent(
                        title=f"{skill_0}: Data Structures & Practical Problem Solving",
                        description=f"Learn standard data structures and error handling to solve real-world problems in {skill_0}.",
                        estimated_minutes=45,
                        task_type="Practice",
                        why_it_matters=f"Every production application for {target_career} relies on organizing and querying structured data.",
                        topics_to_learn=[
                            "Lists, arrays, and sequence indexing",
                            "Key-value collections (dictionaries/objects)",
                            "Common collection methods and iterations",
                            "Basic error handling (try/catch or try/except)"
                        ],
                        learning_focus="Focus on selecting the right data structure for storing and accessing information efficiently.",
                        practice_goal="Implement a small contact list or todo-item manager storing and filtering items in memory.",
                        recommended_resources=[
                            f"{skill_0} Standard Library Documentation",
                            "Problem Solving and Data Collections Guide"
                        ],
                        difficulty_level=diff_level,
                        prerequisites=[f"{skill_0} Control Flow & Functions"]
                    )
                ],
                project=AIProjectIdea(
                    title=f"Build {target_career} {skills_str} Practical Mini-Project",
                    objective=f"Develop a complete, functioning application implementing all topics learned in this phase for {skills_str}.",
                    skills_practiced=phase_skills,
                    difficulty="Beginner" if is_beginner else "Intermediate",
                    expected_outcome=f"Working modular project showcasing {skills_str} integration.",
                    resume_relevance=f"Provides tangible proof of {skills_str} proficiency on resume for {target_career} roles."
                )
            )
