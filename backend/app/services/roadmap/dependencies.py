import logging
from typing import List, Dict, Set
from app.services.skill.normalizer import SkillNormalizer

logger = logging.getLogger(__name__)

# Structured Skill Dependency Tree: skill_name -> list of direct prerequisite skills
SKILL_DEPENDENCY_TREE: Dict[str, List[str]] = {
    # Web & Frontend Development
    "CSS": ["HTML"],
    "JavaScript": ["HTML", "CSS"],
    "TypeScript": ["JavaScript"],
    "React": ["JavaScript", "HTML", "CSS"],
    "Next.js": ["React", "TypeScript"],
    "Tailwind CSS": ["CSS", "HTML"],
    "Web Performance": ["JavaScript", "HTML", "CSS"],

    # Mobile Development
    "Flutter": ["Dart", "Programming Fundamentals & Logic"],
    "React Native": ["React", "JavaScript"],
    "Dart": ["Programming Fundamentals & Logic"],
    "Android Development": ["Java", "OOP"],
    "iOS Development": ["Swift", "OOP"],

    # Backend & API Engineering
    "FastAPI": ["Python", "REST APIs"],
    "Node.js": ["JavaScript"],
    "Express.js": ["Node.js", "JavaScript"],
    "PostgreSQL": ["SQL"],
    "MongoDB": ["Databases"],
    "Redis": ["PostgreSQL", "SQL"],
    "Async Programming": ["Python"],
    "Microservices": ["FastAPI", "Docker", "REST APIs"],
    "Java": ["Programming Fundamentals & Logic"],
    "Spring Boot": ["Java", "OOP", "REST APIs", "SQL"],
    "Django": ["Python", "SQL", "REST APIs"],
    "Flask": ["Python", "REST APIs"],
    "C#": ["OOP", "Programming Fundamentals & Logic"],
    ".NET": ["C#", "OOP", "SQL"],
    "C++": ["Programming Fundamentals & Logic"],
    "Go": ["Programming Fundamentals & Logic"],
    "Rust": ["Programming Fundamentals & Logic"],
    "GraphQL": ["REST APIs", "JavaScript"],
    "SQL": ["Databases"],

    # Data Analytics & Science
    "Pandas": ["Python"],
    "NumPy": ["Python"],
    "Data Visualization": ["SQL", "Pandas"],
    "Tableau": ["Data Visualization", "SQL"],
    "PowerBI": ["Data Visualization", "SQL"],
    "Statistics": ["Python"],
    "Scikit-Learn": ["Python", "Pandas", "NumPy"],
    "Airflow": ["Python", "SQL", "Docker"],
    "Kafka": ["Docker", "Distributed Systems"],

    # AI & ML Engineering
    "Machine Learning": ["Python", "NumPy", "Statistics"],
    "Deep Learning": ["Machine Learning", "PyTorch"],
    "PyTorch": ["Python", "NumPy", "Statistics"],
    "TensorFlow": ["Python", "NumPy"],
    "LLMs": ["Python", "Deep Learning"],
    "Vector Databases": ["Python"],
    "MLOps": ["Docker", "Python", "Machine Learning"],

    # Generative AI & AI Agents
    "Prompt Engineering": ["LLMs"],
    "Embeddings & Vector Search": ["Python", "Vector Databases"],
    "Retrieval-Augmented Generation (RAG)": ["Prompt Engineering", "Embeddings & Vector Search"],
    "Advanced RAG": ["Retrieval-Augmented Generation (RAG)"],
    "Function Calling & Tool Use": ["Prompt Engineering", "REST APIs"],
    "AI Agents": ["Retrieval-Augmented Generation (RAG)", "Function Calling & Tool Use", "Python"],
    "LangGraph": ["AI Agents", "Python"],
    "Multi-Agent Systems": ["AI Agents", "LangGraph"],
    "Agent Evaluation & Guardrails": ["Multi-Agent Systems", "AI Agents"],

    # Cloud & DevOps
    "AWS": ["Linux", "Networking Protocols"],
    "GCP": ["Linux", "Networking Protocols"],
    "Azure": ["Linux", "Networking Protocols"],
    "Docker": ["Linux"],
    "Kubernetes": ["Docker", "Linux"],
    "Terraform": ["AWS", "Cloud"],
    "CI/CD Pipelines": ["Git", "Docker"],
    "Linux": ["Developer Setup & Git Basics"],
    "Git": ["Developer Setup & Git Basics"],

    # Software Engineering & CS Fundamentals
    "OOP": ["Data Structures"],
    "REST APIs": ["OOP", "Git"],
    "Testing": ["JavaScript", "Python"],
    "Unit Testing": ["Python", "JavaScript"],
    "Integration Testing": ["Unit Testing", "REST APIs"],
    "System Design": ["REST APIs", "SQL", "PostgreSQL"],
    "Distributed Systems": ["System Design", "Microservices"],
    "Data Structures": ["Programming Fundamentals & Logic"],
    "Algorithms": ["Data Structures"],
    "Problem Solving": ["Data Structures", "Programming Fundamentals & Logic"],
    "Clean Code": ["OOP", "Programming Fundamentals & Logic"],

    # Cybersecurity & AI Security
    "Cybersecurity Fundamentals": ["Linux", "Networking Protocols"],
    "AI Threat Modeling": ["Cybersecurity Fundamentals", "LLMs"],
    "OWASP LLM Top 10": ["AI Threat Modeling", "Application Security"],
    "Prompt Injection & Defense": ["Prompt Engineering", "OWASP LLM Top 10"],
    "Data Poisoning & Model Privacy": ["Machine Learning", "Cybersecurity Fundamentals"],
    "AI Red Teaming & Guardrails": ["Prompt Injection & Defense", "AI Threat Modeling"],
    "AI Security Auditing": ["AI Red Teaming & Guardrails", "OWASP LLM Top 10"],
    "Vulnerability Testing": ["Linux", "Networking Protocols", "Cybersecurity Fundamentals"],
    "Incident Response": ["Networking Protocols", "Linux"],
    "Penetration Testing": ["Linux", "Networking Protocols", "Cybersecurity Fundamentals"],
    "Application Security": ["REST APIs", "Web Performance"]
}

_DEPENDENCY_LOOKUP: Dict[str, List[str]] = {
    k.strip().lower(): v for k, v in SKILL_DEPENDENCY_TREE.items()
}


class SkillDependencyEngine:
    """Enforces deterministic skill dependency ordering so prerequisites are learned before advanced skills."""

    def __init__(self):
        self.normalizer = SkillNormalizer()

    def get_prerequisites(self, skill_name: str) -> List[str]:
        """Recursively collects all prerequisites for a skill."""
        norm_name = self.normalizer.normalize(skill_name)
        visited: Set[str] = set()

        def _traverse(s: str):
            s_clean = s.strip().lower()
            direct_prereqs = _DEPENDENCY_LOOKUP.get(s_clean, SKILL_DEPENDENCY_TREE.get(s, []))
            for p in direct_prereqs:
                norm_p = self.normalizer.normalize(p)
                if norm_p not in visited and norm_p.lower() != norm_name.lower():
                    visited.add(norm_p)
                    _traverse(norm_p)

        _traverse(norm_name)
        return list(visited)

    def sort_by_dependencies(self, skill_names: List[str]) -> List[str]:
        """Topologically sorts skill names ensuring prerequisites appear before dependent skills."""
        norm_skills = [self.normalizer.normalize(s) for s in skill_names if s]
        unique_skills = list(dict.fromkeys(norm_skills))

        # Build in-degree map and adjacency list for requested skills
        in_degree: Dict[str, int] = {s: 0 for s in unique_skills}
        adj: Dict[str, List[str]] = {s: [] for s in unique_skills}

        for s in unique_skills:
            prereqs = _DEPENDENCY_LOOKUP.get(s.strip().lower(), SKILL_DEPENDENCY_TREE.get(s, []))
            for p in prereqs:
                norm_p = self.normalizer.normalize(p)
                if norm_p in in_degree and norm_p != s:
                    adj[norm_p].append(s)
                    in_degree[s] += 1

        # Kahn's algorithm for topological sorting
        queue = [s for s in unique_skills if in_degree[s] == 0]
        sorted_list: List[str] = []

        while queue:
            node = queue.pop(0)
            sorted_list.append(node)
            for neighbor in adj.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Add any remaining nodes if cycles existed (fallback)
        for s in unique_skills:
            if s not in sorted_list:
                sorted_list.append(s)

        return sorted_list

    def can_learn_skill(self, skill_name: str, user_known_skills: List[str]) -> bool:
        """Returns True if all prerequisites of skill_name are already in user_known_skills."""
        norm_skill = self.normalizer.normalize(skill_name)
        norm_known = {self.normalizer.normalize(k).lower() for k in user_known_skills}

        prereqs = self.get_prerequisites(norm_skill)
        for p in prereqs:
            if p.lower() not in norm_known:
                return False
        return True
