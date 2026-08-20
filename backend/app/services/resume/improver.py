from typing import List, Dict, Any
from app.schemas.resume import BulletImprovementSchema


class ResumeImprover:
    """Generates actionable bullet point & content improvement suggestions without inventing fake metrics."""

    def generate_improvements(
        self,
        parsed_data: Dict[str, Any],
        missing_skills: List[str]
    ) -> List[BulletImprovementSchema]:
        suggestions: List[BulletImprovementSchema] = []

        experience = parsed_data.get("experience", [])
        projects = parsed_data.get("projects", [])

        # 1. Experience bullet improvements
        if experience:
            exp_item = experience[0]
            orig = exp_item.get("description", "").splitlines()[0] if exp_item.get("description") else exp_item.get("title", "")
            if orig:
                improved = f"Engineered and delivered {orig.strip()} using modern best practices and clean modular architecture."
                suggestions.append(
                    BulletImprovementSchema(
                        original_text=orig.strip(),
                        improved_text=improved,
                        explanation="Strengthened action verb ('Engineered and delivered') and highlighted architectural quality. [Note: Add specific metrics like % latency reduction or user count if available]."
                    )
                )

        # 2. Project bullet improvements
        if projects:
            proj_item = projects[0]
            orig_proj = proj_item.get("name", "Project")
            suggestions.append(
                BulletImprovementSchema(
                    original_text=f"Built project {orig_proj}.",
                    improved_text=f"Developed full-stack application '{orig_proj}' featuring structured API integration, client state management, and automated test coverage.",
                    explanation="Replaced passive description with explicit technical tools and production quality signals."
                )
            )

        # 3. Missing Target Skill Integration suggestion
        if missing_skills:
            top_missing = missing_skills[0]
            suggestions.append(
                BulletImprovementSchema(
                    original_text=f"Missing key skill: {top_missing}",
                    improved_text=f"Add demonstrated project experience or coursework covering {top_missing}.",
                    explanation=f"Target role highly values '{top_missing}'. Highlight relevant repository code or certifications."
                )
            )

        return suggestions
