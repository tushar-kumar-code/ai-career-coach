import re
from typing import Dict

# Common alias mapping dictionary for skill normalization
SKILL_ALIASES: Dict[str, str] = {
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "next": "Next.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "python": "Python",
    "python3": "Python",
    "py": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "fastapi": "FastAPI",
    "python/fastapi": "FastAPI",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node.js/fastapi": "Node.js",
    "express": "Express.js",
    "express.js": "Express.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "postgres sql": "PostgreSQL",
    "sql": "SQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "aws/gcp": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "git": "Git",
    "github": "GitHub",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "html": "HTML",
    "html5": "HTML",
    "html/css": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "figma": "Figma",
    "tableau": "Tableau",
    "tableau/powerbi": "Tableau",
    "powerbi": "PowerBI",
    "power bi": "PowerBI",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "pytorch": "PyTorch",
    "pytorch/tensorflow": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    "transformers/llms": "LLMs",
    "llms": "LLMs",
    "llm": "LLMs",
    "vector dbs": "Vector Databases",
    "vector databases": "Vector Databases",
    "jira": "Jira",
    "jira/confluence": "Jira",
    "agile": "Agile/Scrum",
    "scrum": "Agile/Scrum",
    "agile/scrum": "Agile/Scrum",
    "linux": "Linux",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful apis": "REST APIs",
    "c/c++": "C++",
    "c and c++": "C++",
    "c & c++": "C++",
    "git/github": "GitHub",
    "git & github": "GitHub",
    "git and github": "GitHub",
    "ci/cd": "CI/CD Pipelines",
    "ci/cd pipelines": "CI/CD Pipelines",
    "c": "C",
    "c++": "C++",
    "cpp": "C++",
    "c plus plus": "C++",
    "java": "Java",
    "oop": "OOP",
    "oops": "OOP",
    "object oriented programming": "OOP",
    "object-oriented programming": "OOP",
    "oop (object-oriented programming)": "OOP",
    "data structures": "Data Structures",
    "dsa": "Data Structures",
    "data structures and algorithms": "Data Structures",
    "data structures & algorithms": "Data Structures",
    "data structures and algorithms (dsa)": "Data Structures",
    "problem solving": "Problem Solving",
    "problem-solving": "Problem Solving",
    "strengthen problem-solving skills": "Problem Solving",
    "analytical problem solving": "Problem Solving",
    "analytical thinking": "Analytical Thinking",
    "logical reasoning": "Logical Reasoning",
    "systems thinking": "Systems Thinking",
    "communication": "Communication",
    "stakeholder communication": "Stakeholder Communication",
    "leadership": "Leadership",
    "data visualization": "Data Visualization",
    "vulnerability testing": "Vulnerability Testing",
    "networking protocols": "Networking Protocols",
    "terraform": "Terraform"
}


class SkillNormalizer:
    """Normalizes raw skill names to standard canonical names to avoid duplicate variations."""

    @staticmethod
    def normalize(name: str) -> str:
        if not name:
            return ""
        clean_name = name.strip().lower()
        
        # Remove proficiency level indicators if surrounded by space or boundaries
        subbed = re.sub(r'\s*\b(basic|intermediate|advanced|proficient|beginner)\b', '', clean_name, flags=re.IGNORECASE).strip()
        if subbed:
            clean_name = subbed

        clean_name = re.sub(r'[\s_]+', ' ', clean_name)
        
        # Direct lookup in alias dictionary
        if clean_name in SKILL_ALIASES:
            return SKILL_ALIASES[clean_name]
        
        # Capitalize words as fallback
        words = clean_name.strip().split()
        return " ".join(w.capitalize() for w in words)
