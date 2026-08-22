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

    # Backend & API Engineering
    "FastAPI": ["Python", "REST APIs"],
    "Node.js": ["JavaScript"],
    "Express.js": ["Node.js", "JavaScript"],
    "PostgreSQL": ["SQL"],
    "MongoDB": ["Databases"],
    "Redis": ["PostgreSQL", "SQL"],
    "Async Programming": ["Python"],
    "Microservices": ["FastAPI", "Docker", "REST APIs"],

    # Data Analytics & Science
    "Pandas": ["Python"],
    "NumPy": ["Python"],
    "Data Visualization": ["SQL", "Pandas"],
    "Tableau": ["Data Visualization", "SQL"],
    "PowerBI": ["Data Visualization", "SQL"],
    "Statistics": ["Python"],
    "Scikit-Learn": ["Python", "Pandas", "NumPy"],

    # AI & ML Engineering
    "PyTorch": ["Python", "NumPy", "Statistics"],
    "TensorFlow": ["Python", "NumPy"],
    "LLMs": ["Python", "PyTorch"],
    "Vector Databases": ["LLMs", "Python"],
    "MLOps": ["Docker", "Python", "PyTorch"],

    # Cloud & DevOps
    "AWS": ["Linux", "Networking Protocols"],
    "GCP": ["Linux", "Networking Protocols"],
    "Docker": ["Linux"],
    "Kubernetes": ["Docker", "Linux"],
    "Terraform": ["AWS", "Cloud"],
    "CI/CD Pipelines": ["Git", "Docker"],

    # Software Engineering & CS Fundamentals
    "OOP": ["Data Structures"],
    "REST APIs": ["OOP", "Git"],
    "Testing": ["JavaScript", "Python"],
    "System Design": ["REST APIs", "SQL", "PostgreSQL"],

    # Cybersecurity
    "Vulnerability Testing": ["Linux", "Networking Protocols"],
    "Incident Response": ["Networking Protocols", "Linux"]
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
            direct_prereqs = SKILL_DEPENDENCY_TREE.get(s, [])
            for p in direct_prereqs:
                norm_p = self.normalizer.normalize(p)
                if norm_p not in visited and norm_p != norm_name:
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
            prereqs = SKILL_DEPENDENCY_TREE.get(s, [])
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
