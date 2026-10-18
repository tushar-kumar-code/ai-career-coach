import re
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence
from app.models.resume import Resume
from app.models.assessment import AssessmentResponse
from app.models.profile import UserProfile
from app.models.skill_catalog import SkillDefinition
from app.services.skill.normalizer import SkillNormalizer

logger = logging.getLogger(__name__)

INVALID_SKILL_PATTERNS = [
    r'\b(b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?|b\.?sc|m\.?sc|bca|mca|degree|diploma)\b',
    r'\b(school|college|institute|university|secondary|vidyalaya|academy)\b',
    r'\b(10th|12th|percentage|\b\d{1,2}\.?\d{0,2}%\b)',
    r'\b(20\d\d|19\d\d)\b',
    r'\b(raipur|chhattisgarh|dhamtari|darba|india)\b',
    r'\b(installing|install|configuring|verifying|running|opening|focus on|write each|snippets?|code snippet)\b',
    r'\b(primitive data types|arithmetic and comparison|control flow|loops:|basic data structures:)\b',
    r'\b(variables and|terminal basics|visual studio code|vs code)\b',
]

def is_valid_profile_skill(name: str) -> bool:
    if not name or len(name.strip()) == 0 or len(name.strip()) > 35:
        return False
    clean = name.strip()
    clean_lower = clean.lower()
    if clean_lower in ['c', 'r', 'go']:
        return True
    if len(clean) < 2:
        return False
    if '.' in clean and not clean_lower.endswith(('.js', '.net')):
        return False
    for pattern in INVALID_SKILL_PATTERNS:
        if re.search(pattern, clean_lower):
            return False
    return True


class SkillIngestionEngine:
    """Ingests user skills strictly from active Profile sources (latest Resume and Assessment),
    filtering out non-skill artifacts (education, locations, dates, task instructions)."""

    async def ingest_user_skills(self, db: AsyncSession, user_id: str) -> List[Skill]:
        normalizer = SkillNormalizer()
        skill_evidence_map: Dict[str, List[Dict[str, Any]]] = {}

        # 1. Ingest skills strictly from active user Profile (latest Resume extracted skills)
        r_stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
        r_res = await db.execute(r_stmt)
        latest_resume = r_res.scalars().first()

        if latest_resume and latest_resume.parsed_skills:
            for sk_item in latest_resume.parsed_skills:
                raw_name = sk_item.get("name") if isinstance(sk_item, dict) else str(sk_item)
                if not raw_name or not is_valid_profile_skill(raw_name):
                    continue
                norm_name = normalizer.normalize(raw_name)
                if not norm_name or not is_valid_profile_skill(norm_name):
                    continue

                if norm_name not in skill_evidence_map:
                    skill_evidence_map[norm_name] = []

                skill_evidence_map[norm_name].append({
                    "source": "Resume",
                    "description": f"Extracted from profile resume '{latest_resume.filename or 'Uploaded Resume'}'.",
                    "weight": 50
                })

        # 2. Ingest explicitly known/verified skills from UserProfile if present
        p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        p_res = await db.execute(p_stmt)
        user_prof = p_res.scalars().first()
        if user_prof and user_prof.skills_matrix and isinstance(user_prof.skills_matrix, dict):
            prof_known = user_prof.skills_matrix.get("known_skills", [])
            for pk in prof_known:
                if pk and is_valid_profile_skill(str(pk)):
                    norm_pk = normalizer.normalize(str(pk))
                    if norm_pk and is_valid_profile_skill(norm_pk):
                        if norm_pk not in skill_evidence_map:
                            skill_evidence_map[norm_pk] = []
                        skill_evidence_map[norm_pk].append({
                            "source": "Profile",
                            "description": "Explicitly listed in user profile.",
                            "weight": 50
                        })

        # 3. Fallback only if no resume or profile skills found: check assessment known_skills
        if not skill_evidence_map:
            a_stmt = select(AssessmentResponse).where(
                AssessmentResponse.user_id == user_id,
                AssessmentResponse.status == "COMPLETED"
            ).order_by(AssessmentResponse.updated_at.desc())
            a_res = await db.execute(a_stmt)
            latest_assessment = a_res.scalars().first()
            if latest_assessment and latest_assessment.ai_analysis_json:
                known_skills = latest_assessment.ai_analysis_json.get("known_skills", [])
                for ks in known_skills:
                    if ks and is_valid_profile_skill(str(ks)):
                        norm_ks = normalizer.normalize(str(ks))
                        if norm_ks and is_valid_profile_skill(norm_ks):
                            if norm_ks not in skill_evidence_map:
                                skill_evidence_map[norm_ks] = []
                            skill_evidence_map[norm_ks].append({
                                "source": "Assessment",
                                "description": "Verified known skill in career assessment.",
                                "weight": 45
                            })

        # 4. Fetch Skill Taxonomy definitions for categorizing
        sdef_stmt = select(SkillDefinition)
        sdef_res = await db.execute(sdef_stmt)
        skill_catalog_map = {sd.name.lower(): sd.category for sd in sdef_res.scalars().all()}

        # 5. Fetch all existing user skills and clean up duplicates / obsolete rows
        existing_stmt = select(Skill).where(Skill.user_id == user_id)
        existing_res = await db.execute(existing_stmt)
        all_user_skills = existing_res.scalars().all()

        profile_skill_keys = {k.lower(): k for k in skill_evidence_map.keys()}

        skill_db_map: Dict[str, Skill] = {}
        for s in all_user_skills:
            raw = s.normalized_name or s.skill_name or ""
            canonical = normalizer.normalize(raw)
            canonical_lower = canonical.lower()

            # If not in the profile skills, delete it and its evidences immediately
            if not canonical or not is_valid_profile_skill(canonical) or canonical_lower not in profile_skill_keys:
                await db.execute(delete(SkillEvidence).where(SkillEvidence.user_skill_id == s.id))
                await db.delete(s)
                try:
                    from app.services.firestore.skills_repo import SkillsRepository
                    await SkillsRepository.delete_skill(user_id, s.id)
                except Exception:
                    pass
                continue

            # It's a genuine profile skill
            proper_name = profile_skill_keys[canonical_lower]
            if canonical_lower not in skill_db_map:
                s.normalized_name = proper_name
                s.skill_name = proper_name
                pct = s.proficiency_percent or 50
                s.proficiency_level = "Advanced" if pct >= 80 else ("Intermediate" if pct >= 60 else "Beginner")
                skill_db_map[canonical_lower] = s
                db.add(s)
            else:
                primary = skill_db_map[canonical_lower]
                primary.proficiency_percent = max(primary.proficiency_percent or 0, s.proficiency_percent or 0)
                pct = primary.proficiency_percent
                primary.proficiency_level = "Advanced" if pct >= 80 else ("Intermediate" if pct >= 60 else "Beginner")
                primary.confidence_score = max(primary.confidence_score or 0, s.confidence_score or 0)
                merged_sources = list(set((primary.evidence_sources or []) + (s.evidence_sources or [])))
                primary.evidence_sources = merged_sources
                if s.confidence_status == "Verified" or primary.confidence_status == "Verified":
                    primary.confidence_status = "Verified"
                    primary.is_verified = True
                db.add(primary)
                await db.execute(
                    update(SkillEvidence).where(SkillEvidence.user_skill_id == s.id).values(user_skill_id=primary.id)
                )
                await db.delete(s)

        await db.flush()

        # 6. Ingest / Update skills from Profile evidence
        for norm_name, evidences in skill_evidence_map.items():
            norm_lower = norm_name.lower()
            skill = skill_db_map.get(norm_lower)

            existing_sources = set(skill.evidence_sources or []) if skill else set()
            new_sources = {e["source"] for e in evidences}
            sources = list(existing_sources.union(new_sources))
            total_weight = sum(e["weight"] for e in evidences)

            if len(sources) >= 2 or total_weight >= 85 or (skill and skill.confidence_status == "Verified"):
                confidence_status = "Verified"
                confidence_score = min(95, max((skill.confidence_score if skill else 0), 75 + total_weight // 4))
                is_verified = True
            elif "Assessment" in sources:
                confidence_status = "Supported"
                confidence_score = max(65, (skill.confidence_score if skill else 0))
                is_verified = False
            else:
                confidence_status = "Claimed"
                confidence_score = max(55, (skill.confidence_score if skill else 0))
                is_verified = False

            calculated_pct = min(90, 55 + len(evidences) * 15)
            prof_percent = max(skill.proficiency_percent if skill else 0, calculated_pct)
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
                skill_db_map[norm_lower] = skill
            else:
                skill.skill_name = norm_name
                skill.normalized_name = norm_name
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

        # 7. Synchronize clean skills list into UserProfile.skills_matrix
        if user_prof:
            current_matrix = user_prof.skills_matrix or {}
            verified_list = [s.skill_name for s in skill_db_map.values() if s.is_verified or s.confidence_status == "Verified"]
            claimed_list = [s.skill_name for s in skill_db_map.values() if s.confidence_status in ("Claimed", "Supported")]
            current_matrix["verified_skills"] = verified_list
            current_matrix["supported_skills"] = claimed_list
            current_matrix["known_skills"] = [s.skill_name for s in skill_db_map.values()]
            current_matrix["total_skills"] = len(skill_db_map)
            user_prof.skills_matrix = current_matrix
            db.add(user_prof)

        await db.commit()

        # 8. Return all synchronized profile skills
        final_stmt = select(Skill).where(Skill.user_id == user_id)
        final_res = await db.execute(final_stmt)
        return final_res.scalars().all()

    def _fallback_categorize(self, name: str) -> str:
        nl = name.lower()
        if nl in ["c", "python", "javascript", "typescript", "java", "c++", "go", "rust", "c#", "php"]:
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
