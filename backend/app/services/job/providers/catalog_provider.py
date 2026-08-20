from typing import List, Optional, Dict, Any
from app.services.job.providers.base_provider import BaseJobProvider

CATALOG_JOB_POSTINGS: List[Dict[str, Any]] = [
    {
        "provider_id": "job_sd_01",
        "provider_name": "catalog",
        "title": "Software Developer - Core Systems",
        "company": "TechCorp Systems",
        "location": "Remote - US / Global",
        "is_remote": True,
        "employment_type": "Full-time",
        "experience_level": "Mid Level",
        "description": "We are seeking a talented Software Developer to build high-performance backend microservices and maintain core data pipelines. You will collaborate with cross-functional product teams to design clean APIs, write unit tests, and optimize database queries.",
        "required_skills": ["Python", "SQL", "Git", "REST APIs", "Unit Testing"],
        "preferred_skills": ["Docker", "PostgreSQL", "FastAPI"],
        "education_requirements": "Bachelor's degree in Computer Science or equivalent practical experience",
        "salary_min": 95000,
        "salary_max": 130000,
        "salary_currency": "USD",
        "source_url": "https://techcorp.example.com/careers/sd-01",
        "posted_date": "2026-08-15"
    },
    {
        "provider_id": "job_fe_01",
        "provider_name": "catalog",
        "title": "Frontend Engineer (React / Next.js)",
        "company": "Nexus Web Products",
        "location": "Remote",
        "is_remote": True,
        "employment_type": "Full-time",
        "experience_level": "Mid Level",
        "description": "Join our frontend engineering group building responsive web applications using React, TypeScript, and Next.js. You will implement sleek UI components, optimize web performance metrics, and integrate REST/GraphQL endpoints.",
        "required_skills": ["HTML/CSS", "JavaScript", "TypeScript", "React", "Next.js"],
        "preferred_skills": ["Tailwind CSS", "Git", "REST APIs"],
        "education_requirements": "Bachelor's degree or 2+ years equivalent frontend engineering experience",
        "salary_min": 100000,
        "salary_max": 140000,
        "salary_currency": "USD",
        "source_url": "https://nexus.example.com/jobs/fe-react",
        "posted_date": "2026-08-18"
    },
    {
        "provider_id": "job_be_01",
        "provider_name": "catalog",
        "title": "Backend Python / FastAPI Developer",
        "company": "CloudScale Data",
        "location": "San Francisco, CA (Hybrid)",
        "is_remote": False,
        "employment_type": "Full-time",
        "experience_level": "Mid Level",
        "description": "CloudScale is looking for a Backend Engineer proficient in Python, Async FastAPI, and PostgreSQL database architecture. You will design scalable data endpoints, deploy containerized Docker services, and manage CI/CD pipelines.",
        "required_skills": ["Python", "FastAPI", "SQL", "PostgreSQL", "REST APIs"],
        "preferred_skills": ["Docker", "Git", "CI/CD"],
        "education_requirements": "Bachelor's degree in CS/Software Engineering",
        "salary_min": 110000,
        "salary_max": 150000,
        "salary_currency": "USD",
        "source_url": "https://cloudscale.example.com/jobs/backend-fastapi",
        "posted_date": "2026-08-16"
    },
    {
        "provider_id": "job_fs_01",
        "provider_name": "catalog",
        "title": "Full Stack Engineer (Python & React)",
        "company": "Innovate Software",
        "location": "Remote",
        "is_remote": True,
        "employment_type": "Full-time",
        "experience_level": "Senior Level",
        "description": "Full Stack Engineer responsible for end-to-end web architecture. Must be strong in both frontend React interfaces and backend Python microservices with PostgreSQL databases.",
        "required_skills": ["Python", "React", "JavaScript", "FastAPI", "SQL", "Git"],
        "preferred_skills": ["TypeScript", "Docker", "REST APIs"],
        "education_requirements": "Bachelor's degree or equivalent technical experience",
        "salary_min": 120000,
        "salary_max": 165000,
        "salary_currency": "USD",
        "source_url": "https://innovate.example.com/jobs/fullstack-python-react",
        "posted_date": "2026-08-14"
    },
    {
        "provider_id": "job_da_01",
        "provider_name": "catalog",
        "title": "Data Analyst - Business Analytics",
        "company": "Insightful Data Group",
        "location": "Remote",
        "is_remote": True,
        "employment_type": "Full-time",
        "experience_level": "Entry Level / Mid",
        "description": "Analyze complex business datasets to uncover growth insights and operational metrics. Translate executive business questions into SQL queries, Pandas dataframes, and Power BI dashboards.",
        "required_skills": ["Excel", "SQL", "Python", "Pandas", "Power BI"],
        "preferred_skills": ["Data Visualization", "NumPy", "Statistics"],
        "education_requirements": "Bachelor's degree in Analytics, Statistics, CS, or Business",
        "salary_min": 75000,
        "salary_max": 105000,
        "salary_currency": "USD",
        "source_url": "https://insightful.example.com/careers/data-analyst",
        "posted_date": "2026-08-17"
    },
    {
        "provider_id": "job_ds_01",
        "provider_name": "catalog",
        "title": "Data Scientist - Machine Learning",
        "company": "DeepIntelligence AI",
        "location": "New York, NY (Hybrid)",
        "is_remote": False,
        "employment_type": "Full-time",
        "experience_level": "Mid Level",
        "description": "Develop predictive ML models, perform exploratory data analysis, and train deep neural networks on enterprise text and tabular datasets using Python, Pandas, and Machine Learning libraries.",
        "required_skills": ["Python", "Pandas", "NumPy", "Statistics", "Machine Learning"],
        "preferred_skills": ["Deep Learning", "SQL", "Data Visualization"],
        "education_requirements": "Master's or Bachelor's degree in CS, Math, Data Science, or related field",
        "salary_min": 125000,
        "salary_max": 170000,
        "salary_currency": "USD",
        "source_url": "https://deepintel.example.com/jobs/ds-ml",
        "posted_date": "2026-08-12"
    },
    {
        "provider_id": "job_devops_01",
        "provider_name": "catalog",
        "title": "DevOps / Infrastructure Engineer",
        "company": "ScaleOps Cloud",
        "location": "Remote",
        "is_remote": True,
        "employment_type": "Full-time",
        "experience_level": "Mid Level",
        "description": "Manage containerized infrastructure, build automated CI/CD deployment pipelines, and maintain Kubernetes cluster health across cloud environments.",
        "required_skills": ["Linux Basics", "Networking", "Git", "Docker", "Kubernetes"],
        "preferred_skills": ["CI/CD", "Python", "Security Fundamentals"],
        "education_requirements": "Bachelor's degree or 3+ years DevOps experience",
        "salary_min": 115000,
        "salary_max": 155000,
        "salary_currency": "USD",
        "source_url": "https://scaleops.example.com/jobs/devops-k8s",
        "posted_date": "2026-08-19"
    },
    {
        "provider_id": "job_sec_01",
        "provider_name": "catalog",
        "title": "Cybersecurity SOC Analyst",
        "company": "ShieldGuard Security",
        "location": "Remote",
        "is_remote": True,
        "employment_type": "Full-time",
        "experience_level": "Mid Level",
        "description": "Monitor SIEM security telemetry, investigate security incidents, perform threat triage, and audit system compliance across enterprise Linux and network infrastructure.",
        "required_skills": ["Networking", "Linux Basics", "Security Fundamentals", "Threat Analysis", "SIEM"],
        "preferred_skills": ["Python", "Ethical Hacking"],
        "education_requirements": "Bachelor's degree or Security+ / CISSP certification",
        "salary_min": 90000,
        "salary_max": 125000,
        "salary_currency": "USD",
        "source_url": "https://shieldguard.example.com/jobs/soc-analyst",
        "posted_date": "2026-08-13"
    },
    {
        "provider_id": "job_pm_01",
        "provider_name": "catalog",
        "title": "Technical Product Manager",
        "company": "Apex Agile Products",
        "location": "Remote",
        "is_remote": True,
        "employment_type": "Full-time",
        "experience_level": "Mid Level",
        "description": "Lead product lifecycle from discovery to launch. Partner with engineering to define user stories, prioritize backlog in Agile/Scrum, and analyze user retention metrics.",
        "required_skills": ["Agile/Scrum", "User Research", "Product Strategy", "Data-Driven Decisions"],
        "preferred_skills": ["SQL", "Excel"],
        "education_requirements": "Bachelor's degree in CS, Engineering, or Business",
        "salary_min": 110000,
        "salary_max": 150000,
        "salary_currency": "USD",
        "source_url": "https://apex.example.com/jobs/pm-tech",
        "posted_date": "2026-08-15"
    }
]


class CatalogJobProvider(BaseJobProvider):
    """Job search provider delivering standardized reference job postings matching career catalog roles."""

    @property
    def provider_name(self) -> str:
        return "catalog"

    async def search_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        remote_only: Optional[bool] = None,
        experience_level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        results = []
        q_lower = query.lower() if query else None
        loc_lower = location.lower() if location else None

        for job in CATALOG_JOB_POSTINGS:
            # Apply filters
            if q_lower:
                title_match = q_lower in job["title"].lower()
                desc_match = q_lower in job["description"].lower()
                skill_match = any(q_lower in s.lower() for s in job["required_skills"])
                if not (title_match or desc_match or skill_match):
                    continue

            if loc_lower and loc_lower not in job["location"].lower():
                continue

            if remote_only is True and not job["is_remote"]:
                continue

            results.append(job)

        return results[:limit]

    async def get_job_details(self, provider_job_id: str) -> Optional[Dict[str, Any]]:
        for job in CATALOG_JOB_POSTINGS:
            if job["provider_id"] == provider_job_id:
                return job
        return None
