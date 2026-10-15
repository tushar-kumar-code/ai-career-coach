import logging
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.services.ai.client import AIService
from app.schemas.roadmap import (
    LevelTestQuestion,
    LevelTestResponse,
    QuestionResultDetail,
    LevelTestSubmitResponse
)

logger = logging.getLogger(__name__)

LEVEL_METADATA = [
    {
        "level_number": 1,
        "level_name": "Spawn Point",
        "level_theme": "Foundations & Environment Setup",
        "level_icon": "Compass",
        "description": "Your journey begins here. Master the foundational logic, syntax, and workspace configuration."
    },
    {
        "level_number": 2,
        "level_name": "Starter Camp",
        "level_theme": "Core Logic & Problem Solving",
        "level_icon": "Tent",
        "description": "Build solid core programming habits, control flow, functions, and structured problem solving."
    },
    {
        "level_number": 3,
        "level_name": "Skill Forest",
        "level_theme": "Essential Frameworks & Data Structures",
        "level_icon": "Trees",
        "description": "Navigate real-world application frameworks, databases, and structured state management."
    },
    {
        "level_number": 4,
        "level_name": "Challenge Cave",
        "level_theme": "Full-Stack Integration & Architecture",
        "level_icon": "Mountain",
        "description": "Conquer distributed system design, API contracts, security patterns, and testing."
    },
    {
        "level_number": 5,
        "level_name": "Boss Battle",
        "level_theme": "Production Capstone & Interview Mastery",
        "level_icon": "Swords",
        "description": "The ultimate test: build production portfolio projects and ace technical interview drills."
    },
    {
        "level_number": 6,
        "level_name": "Mastery Island",
        "level_theme": "Industry Ready & Career Mastery",
        "level_icon": "Trophy",
        "description": "Final destination: you have achieved end-to-end verified career readiness!"
    }
]


class _AIQuestionItem(BaseModel):
    id: str = Field(description="Unique id like q_1, q_2")
    topic: str = Field(description="Subtopic or skill tested")
    question: str = Field(description="Clear multiple choice question text")
    code_snippet: Optional[str] = Field(default=None, description="Optional code snippet or output challenge")
    difficulty: Optional[str] = Field(default="Intermediate", description="Beginner, Intermediate, or Advanced")
    question_type: Optional[str] = Field(default="conceptual", description="conceptual, code_analysis, or architecture")
    options: List[str] = Field(description="List of 4 distinct choices with prefix A), B), C), D)")
    correct_answer: str = Field(description="Exact string of the correct choice e.g. 'A) ...'")
    explanation: str = Field(description="Clear explanation of the correct concept")


class _AILevelTestContainer(BaseModel):
    questions: List[_AIQuestionItem] = Field(description="List of 5 multiple-choice questions")


class LevelTestEngine:
    """Engine responsible for AI-driven Level Tests gating roadmap progression."""

    @staticmethod
    def get_level_info(phase_number: int) -> Dict[str, str]:
        """Returns standard level name, theme, and icon based on phase number."""
        idx = min(max(phase_number - 1, 0), len(LEVEL_METADATA) - 1)
        return LEVEL_METADATA[idx]

    async def generate_test(
        self,
        phase: Dict[str, Any],
        target_career: str,
        user_level: str = "Beginner"
    ) -> LevelTestResponse:
        """Generates a 5-question AI test based on the actual topics and tasks of the phase."""
        phase_number = phase.get("phase_number", 1)
        phase_id = phase.get("id") or phase.get("phase_id") or f"phase-{phase_number}"
        phase_title = phase.get("title") or phase.get("name") or f"Phase {phase_number}"
        level_info = self.get_level_info(phase_number)
        level_name = level_info["level_name"]

        # Collect topics and skills from phase
        phase_skills = [
            s if isinstance(s, str) else s.get("name", "")
            for s in phase.get("skills", [])
        ]
        
        all_topics: List[str] = []
        for t in phase.get("tasks", []):
            if t.get("topics_to_learn"):
                all_topics.extend(t.get("topics_to_learn", []))
            elif t.get("title"):
                all_topics.append(t.get("title"))

        objectives = phase.get("learning_objectives", [])

        # Limit topics list for prompt readability
        topics_str = ", ".join(all_topics[:8]) if all_topics else (", ".join(phase_skills) or "Core Fundamentals")
        skills_str = ", ".join(phase_skills[:5]) if phase_skills else "General Software Concepts"

        prompt = f"""
You are an expert AI Assessment Examiner creating a strict, interactive 5-question Level Advancement Test.
The student is at Level {phase_number}: '{level_name}' ({phase_title}) aiming for the role of '{target_career}'.
Student Experience Level: {user_level}

Topics Covered in this Level:
{topics_str}

Key Skills:
{skills_str}

Core Objectives:
{", ".join(objectives[:4]) if objectives else "Master core concepts and practical application"}

REQUIREMENTS:
1. Generate exactly 5 questions testing this level. Include variety:
   - 2 Conceptual/scenario questions (real-world problem solving).
   - 2 Code Analysis or 'What does this output/do?' questions with clear code_snippet (valid snippet in Python, JS, SQL, or relevant language).
   - 1 Architecture or best-practice question.
2. Each question MUST have exactly 4 distinct options prefixed with 'A) ', 'B) ', 'C) ', 'D) '.
3. Include clear correct_answer matching one of the options.
4. Include an explanation explaining why that answer is correct and key engineering principle.
5. Make questions realistic for job readiness in {target_career}.
"""

        questions: List[LevelTestQuestion] = []
        try:
            ai_provider = AIService.get_provider()
            res = await ai_provider.generate_structured(
                prompt=prompt,
                output_schema=_AILevelTestContainer,
                system_instruction="You are an expert Technical Interviewer and Curriculum Architect. Generate rigorous, helpful multiple-choice questions matching the schema."
            )
            if res and res.questions and len(res.questions) >= 3:
                for q in res.questions:
                    # Sanitize correct answer matching
                    corr = q.correct_answer.strip()
                    options = [opt.strip() for opt in q.options]
                    if corr not in options and len(options) > 0:
                        for opt in options:
                            if corr.startswith(opt[:3]):
                                corr = opt
                                break
                        else:
                            corr = options[0]

                    questions.append(LevelTestQuestion(
                        id=q.id or f"q_{uuid.uuid4().hex[:6]}",
                        topic=q.topic or phase_title,
                        question=q.question,
                        code_snippet=q.code_snippet,
                        difficulty=q.difficulty or "Intermediate",
                        question_type=q.question_type or "conceptual",
                        options=options,
                        correct_answer=corr,
                        explanation=q.explanation or "This demonstrates the core design principle required for this level."
                    ))
        except Exception as e:
            logger.warning(f"AI level test generation failed, using deterministic fallback: {e}")

        # Deterministic fallback if AI response was empty or insufficient
        if len(questions) < 4:
            questions = self._generate_fallback_questions(
                phase=phase,
                phase_number=phase_number,
                level_name=level_name,
                target_career=target_career,
                topics=all_topics or phase_skills or ["Core Concepts"]
            )

        return LevelTestResponse(
            phase_id=phase_id,
            phase_number=phase_number,
            phase_title=phase_title,
            level_name=level_name,
            target_career=target_career,
            passing_score_percent=70,
            questions=questions[:5]
        )

    def _generate_fallback_questions(
        self,
        phase: Dict[str, Any],
        phase_number: int,
        level_name: str,
        target_career: str,
        topics: List[str]
    ) -> List[LevelTestQuestion]:
        """Provides high-quality fallback questions derived from phase content."""
        questions: List[LevelTestQuestion] = []
        clean_topics = [t for t in topics if t.strip()][:5]
        if not clean_topics:
            clean_topics = [f"{target_career} Fundamentals", "Data Processing", "System Components", "Best Practices", "Debugging"]

        templates = [
            (
                "What is the primary role of {topic} when building modern {career} solutions?",
                None,
                "Intermediate",
                "conceptual",
                "A) It establishes the foundational logic and structured execution flow",
                "B) It is only used for cosmetic styling and has no execution value",
                "C) It replaces all external databases permanently",
                "D) It is an outdated legacy tool deprecated in modern environments",
                "A) It establishes the foundational logic and structured execution flow",
                "{topic} is essential for establishing predictable execution, maintainability, and correct application state."
            ),
            (
                "Examine the following code implementation for {topic}. What is the expected behavior?",
                "async def process_task(data: dict):\n    result = await execute_core(data)\n    if not result:\n        raise ValueError('Invalid state')\n    return {'status': 'success', 'data': result}",
                "Intermediate",
                "code_analysis",
                "A) It executes asynchronously and raises ValueError if the result is empty",
                "B) It causes an infinite recursion deadlock",
                "C) The dictionary return structure is invalid syntax",
                "D) Async functions cannot return dictionary structures",
                "A) It executes asynchronously and raises ValueError if the result is empty",
                "This standard pattern uses async execution with explicit state validation and typed response envelopes."
            ),
            (
                "Consider this implementation pattern for {topic}. What core engineering principle does it demonstrate?",
                "function handlePayload(payload) {\n  if (!payload || typeof payload !== 'object') return null;\n  return Object.freeze({ ...payload, processedAt: Date.now() });\n}",
                "Advanced",
                "code_analysis",
                "A) Immutability and defensive input sanitation before state mutation",
                "B) Writing unsafe side-effects to the global browser window object",
                "C) Synchronously blocking the runtime event loop",
                "D) Creating unhandled memory leaks in background workers",
                "A) Immutability and defensive input sanitation before state mutation",
                "Object immutability and defensive type checks protect application integrity from unpredictable side effects."
            ),
            (
                "When implementing {topic}, which best practice ensures high code quality and reliability?",
                None,
                "Intermediate",
                "best_practice",
                "A) Hardcoding credentials and ignoring input validation",
                "B) Modularizing components, handling edge cases, and writing automated unit tests",
                "C) Writing all logic inside a single monolithic file without error handlers",
                "D) Disabling logging and performance monitoring",
                "B) Modularizing components, handling edge cases, and writing automated unit tests",
                "Clean modular architecture with comprehensive error boundaries and testing ensures production stability."
            ),
            (
                "How does mastering {topic} prepare you for senior-level {career} technical interviews?",
                None,
                "Advanced",
                "architecture",
                "A) Interviewers frequently probe trade-offs, architecture decisions, and edge-case handling around it",
                "B) It is never asked in any technical interview",
                "C) It only requires memorizing syntax without conceptual depth",
                "D) It eliminates the need to understand data structures or system design",
                "A) Interviewers frequently probe trade-offs, architecture decisions, and edge-case handling around it",
                "Engineering interviewers evaluate candidates on architectural reasoning, scalability trade-offs, and practical troubleshooting."
            )
        ]

        for i, (q_tmpl, snippet, diff, q_type, opt_a, opt_b, opt_c, opt_d, corr, expl) in enumerate(templates):
            topic = clean_topics[i % len(clean_topics)]
            questions.append(LevelTestQuestion(
                id=f"gen_q_{i+1}",
                topic=topic,
                question=q_tmpl.format(topic=topic, career=target_career),
                code_snippet=snippet,
                difficulty=diff,
                question_type=q_type,
                options=[
                    opt_a.format(topic=topic, career=target_career),
                    opt_b.format(topic=topic, career=target_career),
                    opt_c.format(topic=topic, career=target_career),
                    opt_d.format(topic=topic, career=target_career),
                ],
                correct_answer=corr.format(topic=topic, career=target_career),
                explanation=expl.format(topic=topic, career=target_career)
            ))

        return questions

    def evaluate_test(
        self,
        phase: Dict[str, Any],
        user_answers: Dict[str, str],
        questions: List[LevelTestQuestion],
        next_phase: Optional[Dict[str, Any]] = None
    ) -> LevelTestSubmitResponse:
        """Evaluates submitted answers, computes pass status (>=70%), stars, XP, and unlocks next level."""
        phase_number = phase.get("phase_number", 1)
        phase_id = phase.get("id") or phase.get("phase_id") or f"phase-{phase_number}"
        level_info = self.get_level_info(phase_number)
        level_name = level_info["level_name"]

        correct_count = 0
        total_questions = len(questions)
        results_detail: List[QuestionResultDetail] = []
        missed_topics: List[str] = []

        for q in questions:
            user_ans = (user_answers.get(q.id) or "").strip()
            correct_ans = q.correct_answer.strip()

            is_correct = False
            if user_ans and correct_ans:
                clean_u = user_ans.strip().lower()
                clean_c = correct_ans.strip().lower()
                if clean_u == clean_c:
                    is_correct = True
                elif len(user_ans.strip()) <= 3 and user_ans.strip()[0].upper() == correct_ans.strip()[0].upper():
                    is_correct = True

            if is_correct:
                correct_count += 1
            else:
                if q.topic and q.topic not in missed_topics:
                    missed_topics.append(q.topic)

            results_detail.append(QuestionResultDetail(
                question_id=q.id,
                question=q.question,
                topic=q.topic,
                user_answer=user_ans or "No answer selected",
                correct_answer=correct_ans,
                is_correct=is_correct,
                explanation=q.explanation,
                code_snippet=q.code_snippet
            ))

        score_percent = round((correct_count / total_questions) * 100) if total_questions > 0 else 0
        passing_threshold = 70
        passed = score_percent >= passing_threshold

        if score_percent >= 95:
            stars_awarded = 3
            xp_earned = 200
            mastery_level = "Flawless Mastery ⭐⭐⭐"
        elif score_percent >= 80:
            stars_awarded = 2
            xp_earned = 150
            mastery_level = "Proficient ⭐⭐"
        elif score_percent >= 70:
            stars_awarded = 1
            xp_earned = 100
            mastery_level = "Level Cleared ⭐"
        else:
            stars_awarded = 0
            xp_earned = 25
            mastery_level = "Needs Practice"

        next_level_unlocked = False
        unlocked_phase_id = None
        unlocked_level_name = None

        if passed and next_phase:
            next_level_unlocked = True
            unlocked_phase_id = next_phase.get("id") or next_phase.get("phase_id")
            next_num = next_phase.get("phase_number", phase_number + 1)
            unlocked_level_name = self.get_level_info(next_num)["level_name"]
            feedback = (
                f"Shabaash! 🎉 You scored {score_percent}% ({mastery_level}) on Level {phase_number}: '{level_name}'! "
                f"+{xp_earned} XP earned. Level {next_num}: '{unlocked_level_name}' is now UNLOCKED on your World Map."
            )
        elif passed:
            feedback = (
                f"Congratulations! 🏆 You scored {score_percent}% ({mastery_level}) on Level {phase_number}: '{level_name}'! "
                f"+{xp_earned} XP earned. You have demonstrated thorough mastery of all core learning objectives."
            )
        else:
            feedback = (
                f"Score: {score_percent}% ({correct_count}/{total_questions} correct). You need at least 70% to unlock the next level. "
                f"+{xp_earned} encouragement XP added. Review the missed topics in your syllabus, then retake the AI test!"
            )

        return LevelTestSubmitResponse(
            phase_id=phase_id,
            phase_number=phase_number,
            level_name=level_name,
            score_percent=score_percent,
            passed=passed,
            passing_score_percent=passing_threshold,
            correct_count=correct_count,
            total_questions=total_questions,
            stars_awarded=stars_awarded,
            xp_earned=xp_earned,
            mastery_level=mastery_level,
            next_level_unlocked=next_level_unlocked,
            unlocked_phase_id=unlocked_phase_id,
            unlocked_level_name=unlocked_level_name,
            feedback=feedback,
            missed_topics=missed_topics,
            results_detail=results_detail
        )
