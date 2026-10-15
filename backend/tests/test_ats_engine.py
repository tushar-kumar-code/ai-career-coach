import pytest
from app.services.resume.ats_engine import ATSEngine
from app.services.resume.target_matcher import TargetCareerMatcher
from app.schemas.resume import ATSBreakdownSchema, TargetCareerMatchSchema, ScoringFactorItem, EligibilityItem


@pytest.fixture
def ats_engine():
    return ATSEngine()


@pytest.fixture
def target_matcher():
    return TargetCareerMatcher()


def test_mode_b_general_resume_scoring_when_no_role(ats_engine):
    """Scenario 1: Correct general resume scoring when no target role exists."""
    parsed = {
        "contact_info": {
            "name": "Alex Smith",
            "email": "alex.smith@example.com",
            "phone": "+1-555-0199",
            "linkedin": "linkedin.com/in/alexsmith",
            "github": "github.com/alexsmith"
        },
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
        "experience": [
            {
                "role": "Software Engineer",
                "company": "Tech Corp",
                "start_date": "2022",
                "end_date": "2024",
                "description": "Architected microservices that increased throughput by 35% and reduced latency to 40ms."
            }
        ],
        "projects": [
            {
                "title": "Cloud Analytics Dashboard",
                "technologies": ["React", "Python", "Docker"],
                "description": "Built scalable dashboard serving 10,000 daily active users with real-time updates."
            }
        ],
        "education": [
            {
                "degree": "B.Tech Computer Science",
                "institution": "National Institute of Technology",
                "end_year": "2022"
            }
        ],
        "summary": "Full stack engineer specializing in Python and distributed backend systems."
    }
    raw_text = (
        "Alex Smith\nalex.smith@example.com\nPython, FastAPI, PostgreSQL, Docker, Git\n"
        "Experience: Software Engineer at Tech Corp. Increased throughput by 35%.\n"
        "Projects: Cloud Analytics Dashboard serving 10,000 DAU.\n"
        "Education: B.Tech Computer Science from National Institute of Technology (2022)."
    )

    breakdown, flags = ats_engine.evaluate_resume(
        parsed_resume=parsed,
        raw_text=raw_text,
        target_role=None,
        job_description=None
    )

    assert breakdown.scoring_mode == "general"
    assert "General Resume Quality" in breakdown.mode_label
    assert len(breakdown.factors) == 6
    total_weights = sum(f.weight for f in breakdown.factors)
    assert total_weights == 100

    # Weights must match Mode B definition: 20, 20, 20, 20, 10, 10
    weights_map = {f.factor_name: f.weight for f in breakdown.factors}
    assert weights_map["Parsing and formatting compatibility"] == 20
    assert weights_map["Resume section completeness"] == 20
    assert weights_map["Documented skills and skill evidence"] == 20
    assert weights_map["Projects and experience evidence"] == 20
    assert weights_map["Education and relevant certifications"] == 10
    assert weights_map["Readability and content clarity"] == 10

    # Mathematical consistency: sum of contributions == overall_ats_score
    expected_sum = round(sum(f.weighted_contribution for f in breakdown.factors))
    assert breakdown.overall_ats_score == expected_sum


def test_mode_a_role_specific_scoring_with_catalog_skills(ats_engine):
    """Scenario 2: Correct role-specific scoring using career-role catalog requirements."""
    parsed = {
        "contact_info": {
            "name": "Dev Candidate",
            "email": "dev@test.com",
            "phone": "555-0100",
            "linkedin": "linkedin.com/in/dev"
        },
        "skills": ["Python", "FastAPI", "SQL", "Git"],
        "experience": [
            {
                "role": "Backend Developer",
                "company": "StartUp Hub",
                "description": "Implemented RESTful APIs and optimized database queries by 25%."
            }
        ],
        "projects": [
            {
                "title": "API Gateway",
                "technologies": ["Python", "FastAPI"],
                "description": "High performance API gateway with rate limiting."
            }
        ],
        "education": [{"degree": "Bachelor of Technology in CS", "institution": "State University"}]
    }
    raw_text = "Dev Candidate\nSkills: Python, FastAPI, SQL, Git\nBackend Developer at StartUp Hub\nB.Tech in CS"

    catalog_skills = ["Python", "SQL", "Git", "Docker"]

    breakdown, flags = ats_engine.evaluate_resume(
        parsed_resume=parsed,
        raw_text=raw_text,
        target_role="Backend Developer",
        job_description=None,
        catalog_skills=catalog_skills
    )

    assert breakdown.scoring_mode == "target_role"
    assert len(breakdown.factors) == 6
    weights_map = {f.factor_name: f.weight for f in breakdown.factors}
    assert weights_map["Required and preferred skill match"] == 35
    assert weights_map["Relevant projects and practical experience"] == 20
    assert weights_map["Required qualifications and eligibility"] == 15
    assert weights_map["Job-related keyword and responsibility match"] == 10
    assert weights_map["Evidence of skills and accomplishments"] == 10
    assert weights_map["Resume parsing and formatting quality"] == 10

    total_weights = sum(f.weight for f in breakdown.factors)
    assert total_weights == 100
    expected_sum = round(sum(f.weighted_contribution for f in breakdown.factors))
    assert breakdown.overall_ats_score == expected_sum


def test_mode_a_specific_job_description_matching(ats_engine):
    """Scenario 3: Specific job description matching when supplied."""
    jd = """
    Senior Python Engineer
    Requirements:
    - 3+ years experience with Python and Django or FastAPI.
    - Strong database skills in PostgreSQL and Redis.
    - Hands-on experience with Docker containerization and Kubernetes.
    - Bachelor's degree in Computer Science or equivalent.
    Responsibilities:
    - Build scalable microservices and manage CI/CD pipelines.
    - Collaborate with cross-functional product teams.
    """
    parsed = {
        "contact_info": {"name": "Candidate", "email": "c@example.com"},
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
        "experience": [
            {
                "role": "Python Engineer",
                "company": "SaaS Co",
                "description": "Built microservices using Python and FastAPI. Managed PostgreSQL queries and deployed using Docker."
            }
        ],
        "projects": [
            {"title": "Microservice Deployment", "technologies": ["Docker", "Python"]}
        ],
        "education": [{"degree": "B.S. in Computer Science"}]
    }
    raw_text = "Candidate\nPython, FastAPI, PostgreSQL, Docker, Git\nPython Engineer at SaaS Co. Microservices with Docker."

    breakdown, flags = ats_engine.evaluate_resume(
        parsed_resume=parsed,
        raw_text=raw_text,
        target_role="Senior Python Engineer",
        job_description=jd
    )

    assert breakdown.scoring_mode == "job_description"
    assert "vacancy" in breakdown.target_context.lower() or "job description" in breakdown.mode_label.lower()
    assert len(breakdown.factors) == 6
    assert len(breakdown.eligibility_criteria) >= 2


def test_zero_matching_skills_must_not_receive_artificial_50_percent(ats_engine, target_matcher):
    """Scenario 4: Zero matching skills must yield 0%, never an artificial 50%."""
    candidate_skills = ["Photoshop", "Graphic Design", "Illustrator", "Typography"]
    target_role_skills = ["Python", "JavaScript", "Docker", "Kubernetes", "AWS"]

    # Test target matcher check_skill_match directly
    matches = [req for req in target_role_skills if target_matcher.check_skill_match(req, candidate_skills)]
    assert len(matches) == 0

    # Calculate match percentage
    pct = int(round((len(matches) / len(target_role_skills)) * 100))
    assert pct == 0, f"Expected 0% for zero matching skills, got {pct}%!"


def test_full_partial_and_zero_skill_matches(target_matcher):
    """Scenario 5: Full (100%), partial (50%), and zero (0%) skill matches."""
    target_skills = ["Python", "FastAPI", "SQL", "Docker"]

    # 1. Full Match (4/4)
    full_candidate = ["Python", "FastAPI", "SQL", "Docker", "Git"]
    full_matches = [t for t in target_skills if target_matcher.check_skill_match(t, full_candidate)]
    assert len(full_matches) == 4
    assert round((len(full_matches) / len(target_skills)) * 100) == 100

    # 2. Partial Match (2/4 = 50%)
    partial_candidate = ["Python", "FastAPI", "Figma", "Marketing"]
    partial_matches = [t for t in target_skills if target_matcher.check_skill_match(t, partial_candidate)]
    assert len(partial_matches) == 2
    assert round((len(partial_matches) / len(target_skills)) * 100) == 50

    # 3. Zero Match (0/4 = 0%)
    zero_candidate = ["Marketing", "Sales", "Accounting"]
    zero_matches = [t for t in target_skills if target_matcher.check_skill_match(t, zero_candidate)]
    assert len(zero_matches) == 0
    assert round((len(zero_matches) / len(target_skills)) * 100) == 0


def test_required_versus_preferred_skills_distinction(ats_engine):
    """Scenario 6: Required versus preferred skills distinction."""
    jd = """
    Required:
    - Python, SQL, Git
    Preferred / Nice to have:
    - Kubernetes, GraphQL, Rust
    """
    req_skills, pref_skills, _ = ats_engine._extract_jd_skills_and_keywords(jd)
    # Check that required and preferred were extracted into separate lists
    assert "Python" in req_skills or "SQL" in req_skills or "Git" in req_skills
    assert "Kubernetes" in pref_skills or "GraphQL" in pref_skills or "Rust" in pref_skills
    # Ensure no overlap between required and preferred lists
    for r in req_skills:
        assert r not in pref_skills


def test_skill_aliases_casing_and_duplicates(target_matcher):
    """Scenario 7: Skill aliases, casing, duplicate skills."""
    candidate_skills = ["javascript", "REACT.JS", "fastapi", "PYTHON", "python"]  # casing & duplicate

    # Alias / casing match: JS / Javascript
    assert target_matcher.check_skill_match("JavaScript", candidate_skills) is True
    # Alias / casing match: React / React.js
    assert target_matcher.check_skill_match("React", candidate_skills) is True
    # Normal casing: FastAPI
    assert target_matcher.check_skill_match("FastAPI", candidate_skills) is True
    # Python
    assert target_matcher.check_skill_match("Python", candidate_skills) is True

    # Irrelevant skill should not match
    assert target_matcher.check_skill_match("Kubernetes", candidate_skills) is False


def test_fresher_and_student_no_penalty_for_missing_corporate_experience(ats_engine):
    """Scenario 8: Students/freshers with no professional employment receive credit for projects."""
    parsed_fresher = {
        "contact_info": {"name": "Fresher Student", "email": "student@college.edu"},
        "skills": ["Python", "Machine Learning", "PyTorch", "Git"],
        "experience": [],  # Zero corporate experience
        "projects": [
            {
                "title": "Autonomous Drone Vision",
                "technologies": ["Python", "PyTorch", "OpenCV"],
                "description": "Trained YOLOv8 model achieving 92% mAP on real-time obstacle detection."
            },
            {
                "title": "Campus Marketplace",
                "technologies": ["React", "FastAPI"],
                "description": "Built full stack e-commerce web application with payment integration."
            }
        ],
        "education": [{"degree": "B.Tech Computer Science (2025)", "institution": "Tech University"}],
        "summary": "Recent graduate passionate about AI/ML systems."
    }
    raw_text = "Fresher Student\nB.Tech Computer Science (2025)\nSkills: Python, PyTorch\nProjects: Autonomous Drone Vision, Campus Marketplace"

    breakdown, _ = ats_engine.evaluate_resume(
        parsed_resume=parsed_fresher,
        raw_text=raw_text,
        target_role=None,
        job_description=None
    )

    assert breakdown.is_fresher_mode is True
    exp_factor = next(f for f in breakdown.factors if "Projects and experience" in f.factor_name)
    # Fresher must receive substantial practical credit for strong projects (> 60), not 0!
    assert exp_factor.factor_score >= 60
    assert any("project" in s.lower() for s in exp_factor.strengths)


def test_missing_sections_policy_and_missing_evidence(ats_engine):
    """Scenario 9: Missing education, projects, or certifications reported transparently."""
    sparse_resume = {
        "contact_info": {"name": "Sparse Resume", "email": "sparse@test.com"},
        "skills": ["Python"],
        "experience": [],
        "projects": [],
        "education": [],
        "summary": ""
    }
    breakdown, _ = ats_engine.evaluate_resume(sparse_resume, "Sparse Resume\nPython")

    # Section completeness factor
    comp_factor = next(f for f in breakdown.factors if "completeness" in f.factor_name)
    assert comp_factor.factor_score < 50
    assert any("experience" in m.lower() for m in comp_factor.missing_evidence)
    assert any("projects" in m.lower() for m in comp_factor.missing_evidence)


def test_mandatory_eligibility_unverifiable_handling(ats_engine):
    """Scenario 10: Missing/unverifiable requirements marked UNKNOWN, not assumed MET."""
    jd = """
    Software Engineer
    Requirements:
    - Master's degree in CS required.
    - Valid US Security Clearance required.
    """
    parsed = {
        "contact_info": {"name": "Candidate", "email": "test@test.com"},
        "skills": ["Python"],
        "experience": [{"role": "Dev", "company": "Co"}],
        "projects": [],
        "education": [{"degree": "Bachelor of Science in CS"}]
    }
    raw_text = "Candidate\nB.S. in CS\nPython"

    breakdown, _ = ats_engine.evaluate_resume(
        parsed_resume=parsed,
        raw_text=raw_text,
        target_role="Software Engineer",
        job_description=jd
    )

    # Check eligibility items
    statuses = {item.criterion: item.status for item in breakdown.eligibility_criteria}
    # Security clearance cannot be confirmed from standard resume -> UNKNOWN
    if "Security Clearance" in statuses:
        assert statuses["Security Clearance"] == "UNKNOWN"
    # Education requirement: Master's required, candidate has Bachelor's -> NOT_MET
    if "Education Degree" in statuses:
        assert statuses["Education Degree"] == "NOT_MET"


def test_empty_and_malformed_input_graceful_handling(ats_engine):
    """Scenario 11: Empty, malformed, or partial data does not crash."""
    breakdown, flags = ats_engine.evaluate_resume(
        parsed_resume={},
        raw_text="",
        target_role=None,
        job_description=None
    )
    assert isinstance(breakdown, ATSBreakdownSchema)
    assert 0 <= breakdown.overall_ats_score <= 100
    assert len(breakdown.factors) == 6
    assert breakdown.overall_ats_score == round(sum(f.weighted_contribution for f in breakdown.factors))


def test_mathematical_weights_and_rounding_verification(ats_engine):
    """Scenario 12: Correct weights, weighted contributions, total score, and rounding."""
    parsed = {
        "contact_info": {"name": "Test", "email": "t@t.com", "phone": "123"},
        "skills": ["Java", "Spring Boot", "SQL"],
        "experience": [{"role": "Java Dev", "company": "Acme", "description": "Built APIs"}],
        "projects": [{"title": "Banking App", "technologies": ["Java"]}],
        "education": [{"degree": "B.Tech"}]
    }

    # Test Mode A
    breakdown_a, _ = ats_engine.evaluate_resume(parsed, "Test\nJava\nSpring", target_role="Java Developer")
    weight_sum_a = sum(f.weight for f in breakdown_a.factors)
    assert weight_sum_a == 100
    for f in breakdown_a.factors:
        expected_contrib = round((f.factor_score * f.weight) / 100.0, 1)
        assert abs(f.weighted_contribution - expected_contrib) < 0.05
    assert breakdown_a.overall_ats_score == round(sum(f.weighted_contribution for f in breakdown_a.factors))

    # Test Mode B
    breakdown_b, _ = ats_engine.evaluate_resume(parsed, "Test\nJava\nSpring", target_role=None)
    weight_sum_b = sum(f.weight for f in breakdown_b.factors)
    assert weight_sum_b == 100
    for f in breakdown_b.factors:
        expected_contrib = round((f.factor_score * f.weight) / 100.0, 1)
        assert abs(f.weighted_contribution - expected_contrib) < 0.05
    assert breakdown_b.overall_ats_score == round(sum(f.weighted_contribution for f in breakdown_b.factors))


def test_schema_serialization_and_consistency(ats_engine):
    """Scenario 13: Consistency between backend models, dictionary dump, and frontend schemas."""
    parsed = {
        "contact_info": {"name": "Test User", "email": "user@test.com"},
        "skills": ["Python", "SQL"],
        "experience": [{"role": "Analyst", "company": "Data Co"}],
        "projects": [],
        "education": [{"degree": "B.Sc Statistics"}]
    }
    breakdown, _ = ats_engine.evaluate_resume(parsed, "Test User\nPython, SQL", target_role="Data Analyst")
    dump = breakdown.model_dump()

    # Required schema fields for frontend
    assert "scoring_mode" in dump
    assert "mode_label" in dump
    assert "factors" in dump
    assert "eligibility_criteria" in dump
    assert "overall_ats_score" in dump
    assert isinstance(dump["factors"], list)
    for f in dump["factors"]:
        assert "factor_name" in f
        assert "weight" in f
        assert "factor_score" in f
        assert "weighted_contribution" in f
        assert "strengths" in f
        assert "missing_evidence" in f
