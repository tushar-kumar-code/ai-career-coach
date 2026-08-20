import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class AdaptiveInterviewEngine:
    """Deterministic state machine adjusting question difficulty and tracking recurring weak areas."""

    def compute_next_difficulty(self, current_difficulty: str, last_score: int) -> str:
        """Determine next question difficulty based on candidate's answer score."""
        difficulties = ["Beginner", "Intermediate", "Advanced"]
        curr_idx = difficulties.index(current_difficulty) if current_difficulty in difficulties else 0

        if last_score >= 85 and curr_idx < len(difficulties) - 1:
            return difficulties[curr_idx + 1]
        elif last_score < 60 and curr_idx > 0:
            return difficulties[curr_idx - 1]
        else:
            return current_difficulty

    def aggregate_session_scores(
        self,
        questions_data: List[Dict[str, Any]]
    ) -> Tuple[int, Dict[str, int], str, str, List[str]]:
        """Calculate overall score, sub-scores, readiness status, explanation, and weak areas list."""
        if not questions_data:
            return 0, {
                "technical": 0,
                "communication": 0,
                "problem_solving": 0,
                "behavioral": 0,
                "resume_knowledge": 0
            }, "NEEDS PRACTICE", "No questions answered yet.", []

        valid_evals = []
        for q in questions_data:
            if isinstance(q, dict):
                ev = q.get("evaluation")
                if isinstance(ev, dict) and "score" in ev:
                    valid_evals.append(ev)
                elif q.get("score") is not None:
                    sc = q.get("score", 70)
                    valid_evals.append({
                        "score": sc,
                        "technical_score": sc,
                        "communication_score": sc,
                        "problem_solving_score": sc,
                        "behavioral_score": sc,
                        "resume_knowledge_score": sc,
                        "strengths": ["Clear answer"],
                        "weaknesses": []
                    })

        if not valid_evals:
            return 0, {
                "technical": 0,
                "communication": 0,
                "problem_solving": 0,
                "behavioral": 0,
                "resume_knowledge": 0
            }, "NEEDS PRACTICE", "No evaluated questions found.", []

        total_questions = len(valid_evals)

        avg_overall = int(round(sum(e.get("score", 0) for e in valid_evals) / total_questions))
        avg_tech = int(round(sum(e.get("technical_score", 0) for e in valid_evals) / total_questions))
        avg_comm = int(round(sum(e.get("communication_score", 0) for e in valid_evals) / total_questions))
        avg_ps = int(round(sum(e.get("problem_solving_score", 0) for e in valid_evals) / total_questions))
        avg_beh = int(round(sum(e.get("behavioral_score", 0) for e in valid_evals) / total_questions))
        avg_res = int(round(sum(e.get("resume_knowledge_score", 0) for e in valid_evals) / total_questions))

        category_scores = {
            "technical": avg_tech,
            "communication": avg_comm,
            "problem_solving": avg_ps,
            "behavioral": avg_beh,
            "resume_knowledge": avg_res
        }

        # Extract weak topics
        weak_topics = []
        for e in valid_evals:
            weak_t = e.get("detected_weak_topic")
            if weak_t and weak_t not in weak_topics:
                weak_topics.append(weak_t)

            for w in e.get("weaknesses", []):
                if w not in weak_topics and len(weak_topics) < 5:
                    weak_topics.append(w)

        # Determine Readiness Status
        if avg_overall >= 85:
            status = "EXCELLENT"
            exp = "Outstanding technical depth, problem-solving, and communication. Fully interview-ready for target roles."
        elif avg_overall >= 75:
            status = "READY"
            exp = "Solid interview performance across technical and behavioral questions. Good candidate standing."
        elif avg_overall >= 60:
            status = "NEARLY READY"
            exp = "Demonstrates good core knowledge, but needs practice explaining technical details and project trade-offs clearly."
        else:
            status = "NEEDS PRACTICE"
            exp = "Multiple weak areas identified. Focus on foundational concepts and structured STAR answers."

        return avg_overall, category_scores, status, exp, weak_topics
