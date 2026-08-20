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
    "ci/cd": "CI/CD Pipelines",
    "ci/cd pipelines": "CI/CD Pipelines",
    "oop": "OOP",
    "data structures": "Data Structures",
    "problem solving": "Problem Solving",
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
        clean_name = re.sub(r'[\s_]+', ' ', clean_name)
        
        # Direct lookup in alias dictionary
        if clean_name in SKILL_ALIASES:
            return SKILL_ALIASES[clean_name]
        
        # Capitalize words as fallback
        words = name.strip().split()
        return " ".join(w.capitalize() for w in words)
