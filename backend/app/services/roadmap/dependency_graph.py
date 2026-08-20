from typing import List, Dict, Set


# Core skill dependency map (prerequisites -> skill)
SKILL_DEPENDENCIES: Dict[str, List[str]] = {
    # Web & Software Development
    "Git": ["Programming Fundamentals"],
    "HTML/CSS": [],
    "JavaScript": ["HTML/CSS"],
    "TypeScript": ["JavaScript"],
    "React": ["JavaScript", "HTML/CSS"],
    "Next.js": ["React", "TypeScript"],
    "Node.js": ["JavaScript"],
    "Express.js": ["Node.js"],
    "Python": [],
    "FastAPI": ["Python"],
    "Django": ["Python"],
    "SQL": [],
    "PostgreSQL": ["SQL"],
    "MongoDB": [],
    "REST APIs": ["HTTP Fundamentals"],
    "GraphQL": ["REST APIs"],
    "Docker": ["Linux Basics"],
    "Kubernetes": ["Docker"],
    "CI/CD": ["Git"],
    "Unit Testing": ["Programming Fundamentals"],
    "Integration Testing": ["Unit Testing"],

    # Data Science & Analytics
    "Excel": [],
    "Power BI": ["Excel", "SQL"],
    "Tableau": ["Excel", "SQL"],
    "Pandas": ["Python"],
    "NumPy": ["Python"],
    "Data Visualization": ["Python", "Excel"],
    "Statistics": [],
    "Machine Learning": ["Python", "Pandas", "Statistics"],
    "Deep Learning": ["Machine Learning"],
    "NLP": ["Machine Learning", "Python"],
    "Computer Vision": ["Deep Learning"],

    # Security & Systems
    "Linux Basics": [],
    "Networking": [],
    "Security Fundamentals": ["Networking", "Linux Basics"],
    "Ethical Hacking": ["Security Fundamentals"],
    "Threat Analysis": ["Security Fundamentals"],
    "SIEM": ["Threat Analysis"],

    # Product & Management
    "Agile/Scrum": [],
    "Product Strategy": ["Agile/Scrum"],
    "User Research": [],
    "Data-Driven Decisions": ["Excel", "Statistics"]
}


def get_skill_prerequisites(skill_name: str) -> List[str]:
    """Return immediate prerequisites for a given skill."""
    # Normalize comparison case
    for key, prereqs in SKILL_DEPENDENCIES.items():
        if key.lower() == skill_name.lower():
            return prereqs
    return []


def topological_sort_skills(skills: List[str]) -> List[str]:
    """Sort a list of skills respecting dependency graph rules."""
    skill_set = set(skills)
    skill_lower_map = {s.lower(): s for s in skills}

    visited: Set[str] = set()
    result: List[str] = []

    def visit(s_name: str):
        s_lower = s_name.lower()
        if s_lower in visited:
            return
        visited.add(s_lower)

        # Get prerequisites
        prereqs = get_skill_prerequisites(s_name)
        for p in prereqs:
            # If prerequisite is in requested skills, visit it first
            if p.lower() in skill_lower_map:
                visit(skill_lower_map[p.lower()])

        if s_lower in skill_lower_map:
            actual_name = skill_lower_map[s_lower]
            if actual_name not in result:
                result.append(actual_name)

    for skill in skills:
        visit(skill)

    return result
