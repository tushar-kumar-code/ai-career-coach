import pytest
from tests.conftest import TestAsyncSessionLocal
from app.services.ai.chat_context import build_candidate_chat_dossier, format_chat_system_instruction

@pytest.mark.asyncio
async def test_candidate_chat_dossier_structure():
    async with TestAsyncSessionLocal() as session:
        dossier = await build_candidate_chat_dossier(session, "demo-user-12345")
        assert dossier is not None
        assert "target_career" in dossier
        assert "verified_skills" in dossier
        assert "archetype" in dossier

def test_format_chat_system_instruction():
    mock_dossier = {
        "user_id": "test-user-1",
        "name": "Alex Kumar",
        "email": "alex@example.com",
        "target_career": "Full Stack Engineer",
        "archetype": "The Architect",
        "readiness_score": 85,
        "has_resume": True,
        "resume_data": {
            "filename": "alex_cv.pdf",
            "ats_score": 88,
            "ats_breakdown": {
                "keyword_score": 90,
                "skills_score": 85,
                "experience_score": 80,
                "formatting_score": 95,
                "readability_score": 90
            },
            "target_career": "Full Stack Engineer",
            "target_match_pct": 82,
            "matching_skills": ["React", "Node.js", "TypeScript", "Python"],
            "missing_skills": ["Docker", "GraphQL", "Kubernetes"],
            "summary": "Passionate full-stack developer with 3 years building modern web applications.",
            "experience": [
                {
                    "role": "Frontend Developer",
                    "company": "Apex Softwares",
                    "start_date": "2023",
                    "end_date": "Present",
                    "description": "Led frontend architecture for SaaS dashboard.",
                    "key_achievements": ["Boosted performance by 40%"]
                }
            ],
            "projects": [
                {
                    "title": "Cloud Resume Matcher",
                    "technologies": ["Next.js", "FastAPI"],
                    "description": "Engineered automated resume parser."
                }
            ],
            "education": [
                {
                    "degree": "B.Tech in Computer Science",
                    "institution": "State Technical University",
                    "field_of_study": "Computer Science",
                    "grade": "8.8 CGPA"
                }
            ],
            "improvements": []
        },
        "has_assessment": True,
        "assessment_data": {
            "archetype": "The Architect",
            "role_recommendations": [{"role_name": "Full Stack Engineer", "match_percentage": 92}],
            "ai_analysis": {
                "key_strengths": ["System Design", "Frontend State Management"],
                "growth_areas": ["Container Orchestration", "Microservices"]
            },
            "selected_career": "Full Stack Engineer"
        },
        "verified_skills": [
            {"name": "React", "proficiency": 90, "category": "Frontend"},
            {"name": "Python", "proficiency": 85, "category": "Backend"}
        ],
        "skill_gaps": [
            {"name": "Docker", "priority": "High", "reason": "Target requirement"}
        ],
        "roadmap_data": {
            "target_role": "Full Stack Engineer",
            "level": "Intermediate",
            "progress_percent": 45,
            "hours_per_day": 2,
            "days_per_week": 5,
            "learning_style": "Hands-on",
            "total_weeks": 8,
            "completed_milestones": 3
        }
    }

    instruction = format_chat_system_instruction(mock_dossier, language="en")
    
    # Assert candidate identity is present
    assert "Alex Kumar" in instruction
    assert "alex@example.com" in instruction
    assert "Full Stack Engineer" in instruction
    assert "85/100" in instruction

    # Assert resume analysis signals are present
    assert "alex_cv.pdf" in instruction
    assert "88/100" in instruction
    assert "Apex Softwares" in instruction
    assert "Cloud Resume Matcher" in instruction
    assert "State Technical University" in instruction
    assert "Docker, GraphQL, Kubernetes" in instruction

    # Assert assessment analysis signals are present
    assert "System Design" in instruction
    assert "Container Orchestration" in instruction

    # Assert skill matrix & roadmap
    assert "React (90%)" in instruction
    assert "45% completed" in instruction
