import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence
from app.models.resume import Resume
from app.models.assessment import AssessmentResponse
from app.models.skill_catalog import SkillDefinition
from app.services.skill.normalizer import SkillNormalizer

logger = logging.getLogger(__name__)


class SkillIngestionEngine:
    """Ingests user skills from Resume and Assessment sources, creates evidence records, and calculates transparent confidence."""

    async def ingest_user_skills(self, db: AsyncSession, user_id: str) -> List[Skill]:
        normalizer = SkillNormalizer()
        skill_evidence_map: Dict[str, List[Dict[str, Any]]] = {}

        # 1. Ingest skills from latest Resume
        r_stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
        r_res = await db.execute(r_stmt)
        latest_resume = r_res.scalars().first()

        if latest_resume and latest_resume.parsed_skills:
            for sk_item in latest_resume.parsed_skills:
                raw_name = sk_item.get("name") if isinstance(sk_item, dict) else str(sk_item)
                if not raw_name:
                    continue
                norm_name = normalizer.normalize(raw_name)
                if not norm_name:
                    continue

                if norm_name not in skill_evidence_map:
                    skill_evidence_map[norm_name] = []

                skill_evidence_map[norm_name].append({
                    "source": "Resume",
                    "description": f"Claimed on resume '{latest_resume.filename or 'Uploaded Resume'}'.",
                    "weight": 50
                })

        # 2. Ingest skills & strengths from Career Discovery Assessment
        a_stmt = select(AssessmentResponse).where(
            AssessmentResponse.user_id == user_id,
            AssessmentResponse.status == "COMPLETED"
        ).order_by(AssessmentResponse.updated_at.desc())
        a_res = await db.execute(a_stmt)
        latest_assessment = a_res.scalars().first()

        if latest_assessment and latest_assessment.ai_analysis_json:
            strengths = latest_assessment.ai_analysis_json.get("top_strengths", [])
            for st in strengths:
                s_name = st.get("strength_name", "") if isinstance(st, dict) else str(st)
                if not s_name:
                    continue
                norm_name = normalizer.normalize(s_name)
                if not norm_name:
                    continue

                if norm_name not in skill_evidence_map:
                    skill_evidence_map[norm_name] = []

                skill_evidence_map[norm_name].append({
                    "source": "Assessment",
                    "description": st.get("evidence_reason", "Demonstrated in Career Discovery Assessment.") if isinstance(st, dict) else "Career Discovery evidence.",
                    "weight": 40
                })

        # 3. Fetch Skill Taxonomy definitions for categorizing
        sdef_stmt = select(SkillDefinition)
        sdef_res = await db.execute(sdef_stmt)
        skill_catalog_map = {sd.name.lower(): sd.category for sd in sdef_res.scalars().all()}

        # 4. Create or Update Skill records in DB
        processed_skills: List[Skill] = []
        for norm_name, evidences in skill_evidence_map.items():
            sk_stmt = select(Skill).where(Skill.user_id == user_id, Skill.normalized_name == norm_name)
            sk_res = await db.execute(sk_stmt)
            skill = sk_res.scalars().first()

            sources = list({e["source"] for e in evidences})
            total_weight = sum(e["weight"] for e in evidences)

            # Transparent Confidence System:
            # Multi-source -> Verified (80-95%)
            # Assessment only -> Supported (65-75%)
            # Resume only -> Claimed (40-50%)
            if len(sources) >= 2 or total_weight >= 85:
                confidence_status = "Verified"
                confidence_score = min(95, 75 + total_weight // 4)
                is_verified = True
            elif "Assessment" in sources:
                confidence_status = "Supported"
                confidence_score = 65
                is_verified = False
            else:
                confidence_status = "Claimed"
                confidence_score = 45
                is_verified = False

            prof_percent = min(90, 50 + len(evidences) * 15)
            prof_level = "Advanced" if prof_percent >= 80 else ("Intermediate" if prof_percent >= 60 else "Beginner")

            category = skill_catalog_map.get(norm_name.lower()) or self._fallback_categorize(norm_name)

            now = datetime.utcnow()

            if not skill:
                skill = Skill(
                    user_id=user_id,
                    skill_name=norm_name,
                    normalized_name=norm_name,
                    category=category,
                    proficiency_percent=prof_percent,
                    proficiency_level=prof_level,
                    confidence_score=confidence_score,
                    confidence_status=confidence_status,
                    is_verified=is_verified,
                    evidence_sources=sources,
                    last_evaluated_at=now
                )
                db.add(skill)
                await db.flush()
            else:
                skill.category = category
                skill.proficiency_percent = prof_percent
                skill.proficiency_level = prof_level
                skill.confidence_score = confidence_score
                skill.confidence_status = confidence_status
                skill.is_verified = is_verified
                skill.evidence_sources = sources
                skill.last_evaluated_at = now
                db.add(skill)

            # Add SkillEvidence records if not present
            for ev in evidences:
                e_stmt = select(SkillEvidence).where(
                    SkillEvidence.user_skill_id == skill.id,
                    SkillEvidence.source == ev["source"]
                )
                e_res = await db.execute(e_stmt)
                if not e_res.scalars().first():
                    evidence_record = SkillEvidence(
                        user_skill_id=skill.id,
                        source=ev["source"],
                        description=ev["description"],
                        confidence_weight=ev["weight"]
                    )
                    db.add(evidence_record)

            processed_skills.append(skill)

        await db.commit()
        return processed_skills

    def _fallback_categorize(self, name: str) -> str:
        nl = name.lower()
        if nl in ["python", "javascript", "typescript", "java", "c++", "go", "rust", "c#", "php"]:
            return "Programming Languages"
        elif nl in ["react", "next.js", "html", "css", "tailwind css", "node.js", "fastapi", "express.js"]:
            return "Web Development"
        elif nl in ["sql", "postgresql", "mongodb", "redis"]:
            return "Databases"
        elif nl in ["pandas", "numpy", "tableau", "powerbi", "data visualization"]:
            return "Data & Analytics"
        elif nl in ["pytorch", "tensorflow", "scikit-learn", "llms", "vector databases"]:
            return "AI/ML"
        elif nl in ["aws", "gcp", "azure"]:
            return "Cloud"
        elif nl in ["docker", "kubernetes", "terraform", "ci/cd pipelines"]:
            return "DevOps"
        elif nl in ["networking protocols", "linux", "vulnerability testing"]:
            return "Cybersecurity"
        elif nl in ["data structures", "oop", "rest apis", "git"]:
            return "Software Engineering"
        elif nl in ["github", "figma", "jira"]:
            return "Tools"
        elif nl in ["communication", "stakeholder communication"]:
            return "Communication"
        elif nl in ["leadership", "agile/scrum"]:
            return "Leadership"
        elif nl in ["problem solving", "logical reasoning"]:
            return "Problem Solving"
        elif nl in ["analytical thinking", "systems thinking"]:
            return "Analytical Thinking"
        return "Technical"
