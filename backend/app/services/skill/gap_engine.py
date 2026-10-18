import logging
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.skill import Skill
from app.models.profile import UserProfile
from app.models.career_catalog import CareerRole
from app.schemas.skill import SkillGapSchema, UserSkillSchema
from app.services.skill.normalizer import SkillNormalizer

logger = logging.getLogger(__name__)


class SkillGapEngine:
    """Evaluates User Skill Profile against Target Career Requirements to compute gaps, proficiencies, and learning priorities."""

    def _get_domain_default_skills(self, domain: str) -> Tuple[List[str], List[str], List[str]]:
        """Provides domain-specific required, important, and optional skills for any uncatalogued domain."""
        d_lower = (domain or "").lower()
        if any(k in d_lower for k in ["devops", "cloud", "sre", "infrastructure", "platform"]):
            return (
                ["Linux", "Docker", "Kubernetes", "Git", "CI/CD"],
                ["Terraform", "AWS", "Bash", "Prometheus"],
                ["Ansible", "Helm", "Grafana"]
            )
        elif any(k in d_lower for k in ["data science", "data scientist", "machine learning", "ml", "ai engineer", "deep learning"]):
            return (
                ["Python", "SQL", "Pandas", "Machine Learning", "Mathematics & Statistics"],
                ["Scikit-Learn", "Data Visualization", "Deep Learning", "Git"],
                ["PyTorch", "FastAPI", "MLOps", "Docker"]
            )
        elif any(k in d_lower for k in ["data analyst", "business intelligence", "bi analyst"]):
            return (
                ["SQL", "Excel", "Python", "Data Visualization", "Business Analytics"],
                ["Power BI", "Tableau", "Pandas", "Statistics"],
                ["A/B Testing", "Git", "ETL Pipelines"]
            )
        elif any(k in d_lower for k in ["frontend", "front-end", "ui developer", "react developer", "web developer"]):
            return (
                ["HTML/CSS", "JavaScript", "React", "Git", "TypeScript"],
                ["Next.js", "Tailwind CSS", "Responsive Design", "State Management"],
                ["Testing (Jest/Playwright)", "GraphQL", "Performance Optimization"]
            )
        elif any(k in d_lower for k in ["backend", "back-end", "api developer"]):
            return (
                ["Python", "REST APIs", "SQL", "Databases", "Git"],
                ["Docker", "Authentication & Security", "FastAPI", "ORM"],
                ["Redis", "Microservices", "System Design", "Message Queues"]
            )
        elif any(k in d_lower for k in ["cyber", "security", "infosec", "penetration", "soc"]):
            return (
                ["Networking", "Linux", "Cybersecurity Fundamentals", "Threat Analysis", "Python"],
                ["OWASP Top 10", "Vulnerability Assessment", "Cryptography", "Wireshark"],
                ["Burp Suite", "SIEM", "Incident Response", "Penetration Testing"]
            )
        elif any(k in d_lower for k in ["mobile", "android", "ios", "flutter", "react native"]):
            return (
                ["Mobile App Development", "Git", "UI Layouts", "REST APIs", "State Management"],
                ["Flutter", "Dart", "Local Storage", "App Architecture"],
                ["Firebase", "Push Notifications", "App Store Deployment"]
            )
        elif any(k in d_lower for k in ["qa", "testing", "automation", "test engineer"]):
            return (
                ["Software Testing", "Test Automation", "Python", "Git", "API Testing"],
                ["Selenium / Playwright", "Postman", "Test Planning", "Bug Reporting"],
                ["CI/CD Pipelines", "Performance Testing", "BDD / Cucumber"]
            )
        elif any(k in d_lower for k in ["ui/ux", "product design", "designer"]):
            return (
                ["Figma", "UI Design", "UX Research", "Wireframing", "Prototyping"],
                ["Design Systems", "Usability Testing", "Information Architecture", "Visual Design"],
                ["Interaction Design", "User Personas", "Design Handoff"]
            )
        else:
            return (
                [f"{domain} Foundations", f"{domain} Core Principles", "Problem Solving", "Git"],
                [f"{domain} Frameworks & Tools", "Applied Practical Workflows", "Industry Standards"],
                [f"{domain} Capstone Portfolio", "Testing & Verification"]
            )

    async def calculate_skill_gaps(
        self,
        db: AsyncSession,
        user_id: str,
        user_skills: List[Skill],
        target_role_override: Optional[str] = None
    ) -> Tuple[str, List[UserSkillSchema], List[UserSkillSchema], List[SkillGapSchema], List[UserSkillSchema]]:
        normalizer = SkillNormalizer()

        # 1. Get Target Career Title from Override or User Profile
        if target_role_override:
            target_title = target_role_override
        else:
            p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
            p_res = await db.execute(p_stmt)
            user_profile = p_res.scalars().first()
            target_title = user_profile.target_career if (user_profile and user_profile.target_career) else "Software Developer"

        # 2. Get Target Role catalog requirements
        c_stmt = select(CareerRole).where(CareerRole.title == target_title)
        c_res = await db.execute(c_stmt)
        target_role = c_res.scalars().first()

        if not target_role:
            c_stmt = select(CareerRole).where(CareerRole.slug.ilike(f"%{target_title.lower().replace(' ', '-')}%"))
            c_res = await db.execute(c_stmt)
            target_role = c_res.scalars().first()

        if target_role:
            raw_req = target_role.required_skills or ["Python", "JavaScript", "SQL"]
            raw_imp = (target_role.important_skills if target_role.important_skills else (target_role.preferred_strengths or ["React", "Git"]))
            raw_opt = target_role.optional_skills or []
            rec_prof_map = target_role.recommended_proficiency or {}
        else:
            raw_req, raw_imp, raw_opt = self._get_domain_default_skills(target_title)
            rec_prof_map = {}

        required_skills = [normalizer.normalize(s) for s in raw_req if s]
        important_skills = [normalizer.normalize(s) for s in raw_imp if s]
        optional_skills = [normalizer.normalize(s) for s in raw_opt if s]

        # Map user skills by normalized name and lower
        user_skill_map: Dict[str, Skill] = {}
        for s in user_skills:
            if s.normalized_name:
                user_skill_map[s.normalized_name.strip().lower()] = s
            if s.skill_name:
                user_skill_map[s.skill_name.strip().lower()] = s

        strong_skills: List[UserSkillSchema] = []
        skills_to_improve: List[UserSkillSchema] = []
        missing_gaps: List[SkillGapSchema] = []
        recommended_next: List[UserSkillSchema] = []

        # Process user's existing skills
        for sk in user_skills:
            sk_norm = normalizer.normalize(sk.normalized_name or sk.skill_name or "")
            sk_lower = sk_norm.lower()

            pct = sk.proficiency_percent or 50
            calc_level = "Advanced" if pct >= 80 else ("Intermediate" if pct >= 60 else "Beginner")
            sk.proficiency_level = calc_level

            is_req = any(sk_lower == r.lower() or (r.lower() == "git" and sk_lower == "github") for r in required_skills)
            is_imp = any(sk_lower == i.lower() for i in important_skills)

            if is_req:
                target_req = "Required"
            elif is_imp:
                target_req = "Important"
            else:
                target_req = "Optional"

            req_level = rec_prof_map.get(sk_norm, rec_prof_map.get(sk_lower, "Intermediate"))

            # Determine gap status & priority based on level & confidence
            if target_req in ["Required", "Important"]:
                if (pct >= 60 and (sk.confidence_score or 40) >= 40) or sk.confidence_status in ["Verified", "Supported"]:
                    gap_status = "Matched"
                    priority = "Low"
                    p_reason = f"Matched prerequisite ({calc_level}) with {sk.confidence_status} confidence."
                elif pct >= 45:
                    gap_status = "Partially Matched"
                    priority = "High" if target_req == "Required" else "Medium"
                    p_reason = f"Current level is {calc_level}; target role '{target_title}' requires {req_level} proficiency."
                else:
                    gap_status = "Weak"
                    priority = "High"
                    p_reason = f"Weak proficiency ({calc_level}, {pct}%) for core {target_req} skill in {target_title}."
            else:
                if pct >= 60 or sk.confidence_status == "Verified":
                    gap_status = "Matched"
                    priority = "Low"
                    p_reason = f"Demonstrated {calc_level} proficiency ({pct}%)."
                else:
                    gap_status = "In Progress"
                    priority = "Low"
                    p_reason = f"Developing profile skill ({calc_level})."

            sk.target_required_level = target_req
            sk.gap_status = gap_status
            sk.priority = priority
            sk.priority_reason = p_reason
            db.add(sk)

            schema_item = UserSkillSchema(
                id=sk.id,
                skill_name=sk.skill_name or sk_norm,
                normalized_name=sk.normalized_name or sk_norm,
                category=sk.category,
                proficiency_percent=sk.proficiency_percent,
                proficiency_level=sk.proficiency_level,
                confidence_score=sk.confidence_score,
                confidence_status=sk.confidence_status,
                target_required_level=target_req,
                gap_status=gap_status,
                priority=priority,
                priority_reason=p_reason,
                evidence_sources=sk.evidence_sources or [],
                last_evaluated_at=sk.last_evaluated_at.isoformat() if sk.last_evaluated_at else None
            )

            if gap_status == "Matched":
                strong_skills.append(schema_item)
            else:
                skills_to_improve.append(schema_item)
                if priority in ["High", "Medium"]:
                    recommended_next.append(schema_item)

        # Identify missing target skills (Required + Important)
        all_target_skills = [(r, "Required") for r in required_skills] + [(i, "Important") for i in important_skills]
        seen_missing = set()

        for req_name, req_type in all_target_skills:
            req_norm = normalizer.normalize(req_name)
            req_lower = req_name.lower()
            req_norm_lower = req_norm.lower()

            has_skill = (
                req_lower in user_skill_map or 
                req_norm_lower in user_skill_map or
                (req_lower == "git" and "github" in user_skill_map) or
                any(req_norm_lower in k or k in req_norm_lower for k in user_skill_map.keys())
            )

            if not has_skill and req_norm_lower not in seen_missing:
                seen_missing.add(req_norm_lower)
                is_req = (req_type == "Required")
                priority = "High" if is_req else "Medium"
                rec_level = rec_prof_map.get(req_name, rec_prof_map.get(req_lower, "Intermediate" if is_req else "Beginner"))
                reason = f"Essential {req_type.lower()} skill for '{target_title}' missing from your evidence profile."

                missing_gaps.append(
                    SkillGapSchema(
                        skill_name=req_norm or req_name,
                        category="Technical",
                        current_proficiency="None",
                        required_proficiency=rec_level,
                        gap_status="Missing",
                        priority=priority,
                        priority_reason=reason
                    )
                )

        await db.commit()

        return target_title, strong_skills, skills_to_improve, missing_gaps, recommended_next
