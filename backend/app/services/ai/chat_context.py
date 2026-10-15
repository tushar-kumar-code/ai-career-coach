import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.assessment import AssessmentResponse
from app.models.skill import Skill
from app.models.roadmap import Roadmap
from app.models.interview import InterviewSession
from app.models.digital_twin import CareerDigitalTwin
from app.services.roadmap.roadmap_engine import RoadmapEngine
from app.services.firestore.user_repo import UserRepository
from app.services.firestore.resume_repo import ResumeRepository
from app.services.firestore.assessment_repo import AssessmentRepository
from app.services.firestore.skills_repo import SkillsRepository

logger = logging.getLogger(__name__)


async def build_candidate_chat_dossier(
    db: AsyncSession,
    user_id: str,
    target_role_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Gathers all analyzed intelligence about the user from SQLite and Firestore:
    - Personal Identity (Name, Email)
    - User Profile & Digital Twin (Target Career, Archetype, Readiness Score, Breakdown)
    - Resume Analysis (ATS score, Breakdown, Missing Skills, Experience, Projects, Education)
    - Assessment Results (Top Career Matches, Strengths, Growth Areas)
    - Live Skills Matrix (Verified, Supported, Gaps)
    - Active Roadmap, Live Progress, Recently Learned Skills & Today's Focus
    - Mock Interview Evaluation (Scores, Weak Areas, Category breakdown)
    """
    dossier: Dict[str, Any] = {
        "user_id": user_id,
        "name": "Candidate",
        "email": "",
        "target_career": target_role_override or "Software Developer",
        "archetype": "The Builder",
        "readiness_score": 0,
        "readiness_label": "Not Started",
        "readiness_breakdown": {},
        "has_resume": False,
        "resume_data": None,
        "has_assessment": False,
        "assessment_data": None,
        "verified_skills": [],
        "supported_skills": [],
        "skill_gaps": [],
        "recent_learned_skills": [],
        "roadmap_data": None,
        "today_focus": None,
        "recent_interview": None,
        "evidence_points": [],
    }

    # 1. Fetch User Identity (SQLite & Firestore)
    try:
        u_stmt = select(User).where(User.id == user_id)
        u_res = await db.execute(u_stmt)
        user = u_res.scalar_one_or_none()
        if user:
            dossier["name"] = user.full_name or user.email.split("@")[0].capitalize()
            dossier["email"] = user.email

        # Firestore fallback for name/email
        if not user or not user.full_name:
            fs_u = await UserRepository.get_user(user_id)
            if fs_u:
                dossier["name"] = fs_u.get("full_name") or fs_u.get("displayName") or dossier["name"]
                dossier["email"] = fs_u.get("email") or dossier["email"]
    except Exception as e:
        logger.warning(f"Notice on user identity retrieval for chat context: {e}")

    # 2. Fetch User Profile & Digital Twin
    try:
        p_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        p_res = await db.execute(p_stmt)
        profile = p_res.scalar_one_or_none()
        if profile:
            if profile.target_career and not target_role_override:
                dossier["target_career"] = profile.target_career
            if profile.primary_archetype:
                dossier["archetype"] = profile.primary_archetype
            if profile.job_readiness_score:
                dossier["readiness_score"] = profile.job_readiness_score

            matrix = profile.skills_matrix or {}
            dossier["readiness_breakdown"] = matrix.get("readiness_breakdown", {})
            dossier["recent_learned_skills"] = matrix.get("recent_learned", [])
            dossier["evidence_points"] = list(profile.evidence_points or [])

        # Check CareerDigitalTwin for refined readiness metrics
        dt_stmt = select(CareerDigitalTwin).where(CareerDigitalTwin.user_id == user_id)
        dt_res = await db.execute(dt_stmt)
        digital_twin = dt_res.scalar_one_or_none()
        if digital_twin:
            dossier["readiness_score"] = digital_twin.overall_readiness_score or dossier["readiness_score"]
            dossier["readiness_label"] = digital_twin.readiness_label or "In Progress"
            if not dossier["readiness_breakdown"]:
                dossier["readiness_breakdown"] = {
                    "skill_readiness": digital_twin.skill_readiness,
                    "roadmap_progress": digital_twin.roadmap_progress,
                    "resume_readiness": digital_twin.resume_readiness,
                    "interview_readiness": digital_twin.interview_readiness,
                    "job_match_readiness": digital_twin.job_match_readiness,
                }
    except Exception as e:
        logger.warning(f"Notice on user profile retrieval for chat context: {e}")

    # 3. Fetch Resume Analysis (SQLite & Firestore)
    try:
        r_stmt = select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
        r_res = await db.execute(r_stmt)
        resume = r_res.scalars().first()

        # If not in SQLite, check Firestore
        fs_resume = None
        if not resume:
            fs_resume = await ResumeRepository.get_latest_resume(user_id)

        if resume or fs_resume:
            dossier["has_resume"] = True
            ats_score = resume.overall_ats_score if resume else fs_resume.get("overall_ats_score", 0)
            target_career_name = (
                (resume.target_career_name if resume else fs_resume.get("target_career_name"))
                or dossier["target_career"]
            )
            target_match_pct = (
                (resume.target_match_percentage if resume else fs_resume.get("target_match_percentage"))
                or 0
            )
            matching_skills = (
                (resume.matching_skills if resume else fs_resume.get("matching_skills"))
                or []
            )
            missing_skills = (
                (resume.missing_skills if resume else fs_resume.get("missing_skills"))
                or []
            )

            # Contact & Summary
            contact = (
                (resume.parsed_contact_info if resume else (fs_resume.get("about_user") or fs_resume.get("parsed_contact_info")))
                or {}
            )
            if contact.get("name") and dossier["name"] == "Candidate":
                dossier["name"] = contact.get("name")

            # Skills
            parsed_skills = (
                (resume.parsed_skills if resume else fs_resume.get("parsed_skills"))
                or []
            )

            # Experience
            parsed_exp = (
                (resume.parsed_experience if resume else fs_resume.get("parsed_experience"))
                or []
            )

            # Projects
            parsed_proj = (
                (resume.parsed_projects if resume else fs_resume.get("parsed_projects"))
                or []
            )

            # Education
            parsed_edu = (
                (resume.parsed_education if resume else fs_resume.get("parsed_education"))
                or []
            )

            # Improvements
            improvements = (
                (resume.improvement_suggestions if resume else fs_resume.get("improvement_suggestions"))
                or []
            )

            # ATS Breakdown
            ats_breakdown = (
                (resume.ats_breakdown_json if resume else fs_resume.get("ats_breakdown_json"))
                or {}
            )

            dossier["resume_data"] = {
                "filename": resume.filename if resume else fs_resume.get("filename", "resume.pdf"),
                "ats_score": ats_score,
                "ats_breakdown": ats_breakdown,
                "target_career": target_career_name,
                "target_match_pct": target_match_pct,
                "matching_skills": matching_skills,
                "missing_skills": missing_skills,
                "summary": contact.get("summary") or "",
                "skills": parsed_skills,
                "experience": parsed_exp,
                "projects": parsed_proj,
                "education": parsed_edu,
                "improvements": improvements,
            }
            if not target_role_override and target_career_name:
                dossier["target_career"] = target_career_name
    except Exception as e:
        logger.warning(f"Notice on resume retrieval for chat context: {e}")

    # 4. Fetch Assessment Analysis (SQLite & Firestore)
    try:
        a_stmt = select(AssessmentResponse).where(
            AssessmentResponse.user_id == user_id,
            AssessmentResponse.status == "COMPLETED"
        ).order_by(AssessmentResponse.updated_at.desc())
        a_res = await db.execute(a_stmt)
        assessment = a_res.scalars().first()

        fs_assessment = None
        if not assessment:
            fs_assessment = await AssessmentRepository.get_latest_assessment(user_id)

        if assessment or fs_assessment:
            dossier["has_assessment"] = True
            computed_arch = (
                (assessment.computed_archetype if assessment else fs_assessment.get("computed_archetype"))
                or dossier["archetype"]
            )
            dossier["archetype"] = computed_arch

            ai_json = (
                (assessment.ai_analysis_json if assessment else fs_assessment.get("ai_analysis_json"))
                or {}
            )
            role_recs = (
                (assessment.role_recommendations if assessment else fs_assessment.get("role_recommendations"))
                or []
            )
            selected_target = (
                (assessment.selected_target_career if assessment else fs_assessment.get("selected_target_career"))
                or dossier["target_career"]
            )
            if selected_target and not target_role_override:
                dossier["target_career"] = selected_target

            dossier["assessment_data"] = {
                "archetype": computed_arch,
                "role_recommendations": role_recs,
                "ai_analysis": ai_json,
                "selected_career": selected_target
            }
    except Exception as e:
        logger.warning(f"Notice on assessment retrieval for chat context: {e}")

    # 5. Fetch Skills Matrix & High-Priority Gaps
    try:
        s_stmt = select(Skill).where(Skill.user_id == user_id)
        s_res = await db.execute(s_stmt)
        skills = s_res.scalars().all()
        for s in skills:
            if s.is_gap or s.gap_status == "Missing":
                dossier["skill_gaps"].append({
                    "name": s.skill_name,
                    "priority": s.priority or "Medium",
                    "reason": s.priority_reason or ""
                })
            elif s.confidence_status == "Verified":
                dossier["verified_skills"].append({
                    "name": s.skill_name,
                    "proficiency": s.proficiency_percent or 75,
                    "category": s.category or "Technical"
                })
            else:
                dossier["supported_skills"].append({
                    "name": s.skill_name,
                    "proficiency": s.proficiency_percent or 60,
                    "category": s.category or "Technical",
                    "status": s.confidence_status or "Supported"
                })
    except Exception as e:
        logger.warning(f"Notice on skills retrieval for chat context: {e}")

    # 6. Fetch Roadmap Progress & Today's Focus
    try:
        rm_stmt = select(Roadmap).where(Roadmap.user_id == user_id).order_by(Roadmap.created_at.desc())
        rm_res = await db.execute(rm_stmt)
        roadmap = rm_res.scalars().first()
        if roadmap:
            roadmap_engine = RoadmapEngine()
            focus_tasks_dict = roadmap_engine.get_today_focus_tasks(roadmap)

            dossier["roadmap_data"] = {
                "target_role": roadmap.target_role,
                "level": roadmap.user_level,
                "progress_percent": roadmap.overall_progress_percent,
                "hours_per_day": roadmap.hours_per_day,
                "days_per_week": roadmap.days_per_week,
                "learning_style": roadmap.preferred_learning_style,
                "total_weeks": roadmap.total_estimated_weeks,
                "completed_tasks": len(roadmap.completed_task_ids or []),
                "completed_milestones": len(roadmap.completed_milestone_ids or []),
                "completed_projects": len(roadmap.completed_project_ids or []),
            }
            dossier["today_focus"] = {
                "title": focus_tasks_dict.get("today_focus_title"),
                "phase_title": focus_tasks_dict.get("current_phase_title"),
                "tasks": [
                    {
                        "id": t.get("id"),
                        "title": t.get("title"),
                        "estimated_minutes": t.get("estimated_minutes", 30),
                        "why_it_matters": t.get("why_it_matters"),
                        "is_completed": t.get("is_completed", False)
                    }
                    for t in focus_tasks_dict.get("today_tasks", [])[:3]
                ],
                "recommended_minutes": focus_tasks_dict.get("recommended_minutes", 30)
            }
    except Exception as e:
        logger.warning(f"Notice on roadmap retrieval for chat context: {e}")

    # 7. Fetch Recent Mock Interview Evaluation Analysis
    try:
        iv_stmt = (
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id, InterviewSession.is_completed == True)
            .order_by(InterviewSession.created_at.desc())
            .limit(1)
        )
        iv_res = await db.execute(iv_stmt)
        recent_iv = iv_res.scalars().first()
        if recent_iv:
            dossier["recent_interview"] = {
                "target_role": recent_iv.target_role,
                "mode": recent_iv.mode,
                "overall_score": recent_iv.overall_score,
                "readiness_status": recent_iv.readiness_status,
                "weak_areas": recent_iv.weak_areas or [],
                "category_scores": recent_iv.category_scores or {},
            }
    except Exception as e:
        logger.warning(f"Notice on interview retrieval for chat context: {e}")

    return dossier


def format_chat_system_instruction(dossier: Dict[str, Any], language: str = "en") -> str:
    """
    Constructs an ultra-rich, production-grade system instruction for Groq AI
    containing all analyzed candidate data so the AI conversation feels deeply
    personal, interactive, accurate, and contextually grounded.
    """
    name = dossier.get("name") or "Candidate"
    target_career = dossier.get("target_career") or "Software Developer"
    archetype = dossier.get("archetype") or "The Builder"
    readiness = dossier.get("readiness_score") or 0
    readiness_label = dossier.get("readiness_label") or "In Progress"
    readiness_breakdown = dossier.get("readiness_breakdown") or {}

    # Format Readiness Subscores
    readiness_summary = f"{readiness}/100 ({readiness_label})"
    if readiness_breakdown:
        sk_r = readiness_breakdown.get("skill_readiness", 0)
        rm_r = readiness_breakdown.get("roadmap_progress", 0)
        res_r = readiness_breakdown.get("resume_readiness", 0)
        iv_r = readiness_breakdown.get("interview_readiness", 0)
        readiness_summary += f"\n  • Sub-scores: Skill Readiness: {sk_r}%, Roadmap: {rm_r}%, Resume: {res_r}%, Mock Interview: {iv_r}%"

    # 1. Format Resume Section
    resume_section = "Resume Status: Not yet uploaded."
    if dossier.get("has_resume") and dossier.get("resume_data"):
        r = dossier["resume_data"]
        ats = r.get("ats_score", 0)
        breakdown = r.get("ats_breakdown") or {}
        kw = breakdown.get("keyword_score", 0)
        sk_score = breakdown.get("skills_score", 0)
        exp_score = breakdown.get("experience_score", 0)
        fmt_score = breakdown.get("formatting_score", 0)
        rd_score = breakdown.get("readability_score", 0)

        # Experience
        exp_lines = []
        for exp in (r.get("experience") or [])[:3]:
            role = exp.get("role", "Engineer")
            company = exp.get("company", "Company")
            dates = f"{exp.get('start_date', '')} - {exp.get('end_date', '')}".strip(" -")
            desc = exp.get("description", "")
            achievements = exp.get("key_achievements", [])
            ach_str = f" | Achievements: {', '.join(achievements[:2])}" if achievements else ""
            exp_lines.append(f"  • {role} at {company} ({dates}): {desc[:150]}{ach_str}")
        exp_str = "\n".join(exp_lines) if exp_lines else "  • No prior work experience specified"

        # Projects
        proj_lines = []
        for p in (r.get("projects") or [])[:3]:
            title = p.get("title", "Project")
            techs = ", ".join(p.get("technologies") or [])
            tech_str = f" [Tech: {techs}]" if techs else ""
            desc = p.get("description", "")
            proj_lines.append(f"  • {title}{tech_str}: {desc[:140]}")
        proj_str = "\n".join(proj_lines) if proj_lines else "  • None listed"

        # Education
        edu_lines = []
        for ed in (r.get("education") or [])[:2]:
            degree = ed.get("degree", "Degree")
            inst = ed.get("institution", "University")
            field = ed.get("field_of_study", "")
            grade = f" (Grade: {ed.get('grade')})" if ed.get("grade") else ""
            edu_lines.append(f"  • {degree} in {field} from {inst}{grade}")
        edu_str = "\n".join(edu_lines) if edu_lines else "  • Technical Background"

        # Missing skills
        missing = r.get("missing_skills") or []
        missing_str = ", ".join(missing[:8]) if missing else "None identified"

        # Matching skills
        matching = r.get("matching_skills") or []
        matching_str = ", ".join(matching[:10]) if matching else "Standard technical skills"

        # Improvements
        improvements = []
        for imp in (r.get("improvements") or [])[:3]:
            curr = imp.get("current_bullet", "")
            impr = imp.get("improved_bullet", "")
            if curr and impr:
                improvements.append(f"  • Needs improvement: '{curr[:90]}' -> Suggested: '{impr[:90]}'")
        imp_str = "\n".join(improvements) if improvements else "  • Standard bullet phrasing"

        resume_section = f"""- **Uploaded File**: {r.get('filename')}
- **Overall ATS Score**: {ats}/100 (Keywords: {kw}%, Skills: {sk_score}%, Experience: {exp_score}%, Readability: {rd_score}%, Formatting: {fmt_score}%)
- **Match with Target Role ({r.get('target_career')})**: {r.get('target_match_pct')}%
- **Skills Found on Resume**: {matching_str}
- **Missing Skills for Target Role**: {missing_str}
- **Key Experience**:
{exp_str}
- **Key Projects**:
{proj_str}
- **Education**:
{edu_str}
- **Resume Suggestions Identified**:
{imp_str}"""

    # 2. Format Assessment Section
    assessment_section = "Assessment Status: Not yet taken."
    if dossier.get("has_assessment") and dossier.get("assessment_data"):
        a = dossier["assessment_data"]
        ai_json = a.get("ai_analysis") or {}

        # Roles
        recs = a.get("role_recommendations") or ai_json.get("career_recommendations") or []
        rec_list = []
        for rec in recs[:3]:
            if isinstance(rec, dict):
                rec_list.append(f"{rec.get('role_name') or rec.get('career_name')} ({rec.get('match_percentage', 80)}%)")
            elif isinstance(rec, str):
                rec_list.append(rec)
        rec_str = ", ".join(rec_list) if rec_list else "Target Career Selected"

        # Strengths
        strengths = ai_json.get("key_strengths") or ai_json.get("strengths") or []
        strengths_str = ", ".join(strengths[:5]) if strengths else "Analytical problem solving, eager learner"

        # Gaps
        gaps = ai_json.get("growth_areas") or ai_json.get("skill_gaps") or []
        gaps_str = ", ".join(gaps[:5]) if gaps else "Domain framework mastery"

        assessment_section = f"""- **Assessment Status**: Completed
- **Primary Career Archetype**: {a.get('archetype')}
- **Top Matched Roles**: {rec_str}
- **Assessed Strengths**: {strengths_str}
- **Identified Growth Gaps**: {gaps_str}"""

    # 3. Format Skill Matrix
    verified_list = [f"{s['name']} ({s['proficiency']}%)" for s in (dossier.get("verified_skills") or [])[:10]]
    verified_str = ", ".join(verified_list) if verified_list else "Ingestion in progress"

    supported_list = [s['name'] for s in (dossier.get("supported_skills") or [])[:8]]
    supported_str = ", ".join(supported_list) if supported_list else "None yet"

    gap_list = [f"{g['name']} [Priority: {g['priority']}]" for g in (dossier.get("skill_gaps") or [])[:6]]
    gaps_str = ", ".join(gap_list) if gap_list else "None critical"

    # Recently learned skills from roadmap
    recent_learned_entries = []
    for item in (dossier.get("recent_learned_skills") or [])[:5]:
        t_title = item.get("task_title", "Milestone")
        t_skills = ", ".join(item.get("skills", []))
        sk_part = f" (Skills learned: {t_skills})" if t_skills else ""
        recent_learned_entries.append(f"  • Completed: {t_title}{sk_part}")
    recent_learned_str = "\n".join(recent_learned_entries) if recent_learned_entries else "  • Starting initial roadmap milestones."

    # 4. Format Roadmap & Today's Focus
    roadmap_section = "Roadmap Status: Default progression."
    if dossier.get("roadmap_data"):
        rm = dossier["roadmap_data"]
        tf = dossier.get("today_focus") or {}
        tf_tasks = tf.get("tasks") or []
        tf_task_str = ""
        if tf_tasks:
            t_first = tf_tasks[0]
            tf_task_str = f"\n- **Today's Active Focus**: '{t_first.get('title')}' ({t_first.get('estimated_minutes')} mins) - {t_first.get('why_it_matters')}"

        roadmap_section = f"""- **Roadmap Track**: {rm.get('target_role')} ({rm.get('level')} level)
- **Live Progress**: {rm.get('progress_percent')}% completed ({rm.get('completed_tasks')} tasks, {rm.get('completed_milestones')} milestones finished)
- **Schedule**: {rm.get('hours_per_day')} hrs/day, {rm.get('days_per_week')} days/week ({rm.get('learning_style')} style){tf_task_str}
- **Recently Completed Milestones**:
{recent_learned_str}"""

    # 5. Format Mock Interview Analysis Section
    interview_section = "Mock Interview Status: No completed sessions yet."
    if dossier.get("recent_interview"):
        iv = dossier["recent_interview"]
        weak_list = ", ".join(iv.get("weak_areas", [])[:4]) or "None flagged"
        cat_scores = iv.get("category_scores", {})
        cat_str = ", ".join([f"{k.capitalize()}: {v}%" for k, v in cat_scores.items()]) if cat_scores else "Evaluated"
        interview_section = f"""- **Latest Mock Interview Score**: {iv.get('overall_score')}% ({iv.get('mode')} Interview - Status: {iv.get('readiness_status')})
- **Detected Weak Areas for Practice**: {weak_list}
- **Category Performance**: {cat_str}"""

    language_instruction = ""
    if language == "hi":
        language_instruction = "\n- **Language**: The candidate preference is Hindi. Respond in clear, engaging Hindi with standard English tech terms."

    missing_skills_info = ", ".join((dossier.get("resume_data") or {}).get("missing_skills", [])) or "identified gap skills"

    prompt = f"""You are an elite, hyper-contextual AI Career Coach for university candidates and software engineers.
You are powered by Groq's ultra-fast LLM.

════════════════════════════════════════════════════════════════════════════════
⭐ CANDIDATE COMPLETE ANALYZED PROFILE & LIVE AI DOSSIER:
════════════════════════════════════════════════════════════════════════════════
• Candidate Name: {name}
• Email: {dossier.get('email')}
• Target Career Goal: {target_career}
• Career Archetype: {archetype}
• Job Readiness Score: {readiness_summary}

🗺️ REAL-TIME LEARNING ROADMAP & SKILL VELOCITY:
{roadmap_section}

🛠️ LIVE VERIFIED SKILL MATRIX & GAPS:
• Verified Skills (High Confidence): {verified_str}
• Supported / Learning Skills: {supported_str}
• Top Priority Skill Gaps to Close: {gaps_str}

🎤 RECENT MOCK INTERVIEW EVALUATION:
{interview_section}

📄 RESUME AUDIT & EXTRACTED PROFILE:
{resume_section}

🧭 DISCOVERY ASSESSMENT INSIGHTS:
{assessment_section}
════════════════════════════════════════════════════════════════════════════════

CONVERSATIONAL RULES & DIRECTIVES:
1. **DEEP RELEVANCE & CONTINUOUS MEMORY**:
   - You ALREADY KNOW this candidate thoroughly. Greet them by name ({name}) when appropriate.
   - You have REAL-TIME access to their learning journey. As they follow the roadmap and learn skills, you know their newly completed milestones and current "Today's Focus" task!
   - Acknowledge their recent progress! (e.g., if they recently completed a roadmap milestone or improved their readiness score, celebrate that momentum).
   - If they ask about projects, refer to their real projects and newly learned skills.
   - If they ask what to study next, guide them directly to their active "Today's Focus" task or highest-priority skill gaps ({missing_skills_info}).
   - If they ask about interview preparation, address the specific weak areas flagged in their recent mock interview or missing resume skills.
   - Never ask generic discovery questions that you already know the answer to (e.g. do not ask "What is your target job?" because you already know it is {target_career}).

2. **LANGUAGE & TONE**:
   - If the candidate speaks in **Hinglish** (e.g., "Mujhe interview me kya puchha jayega?"), answer in natural, motivating, and smart **Hinglish** with English tech terms.
   - If the candidate speaks in **English**, answer in fluent, encouraging, top-tier **English**.
   - If the candidate speaks in **Hindi** script, answer in **Hindi**.{language_instruction}

3. **RESPONSE STRUCTURE & FORMATTING**:
   - Use clean Markdown with headers (`### 🎯 Focus`, `### 💡 Pro Tip`), concise bullet points, and **bold** keywords.
   - Never generate overwhelming walls of text. Be punchy, actionable, and structured.
   - Include code snippets or architecture tables when explaining technical questions.
   - Always conclude with ONE clear next action step or a motivating follow-up question.
"""
    return prompt
