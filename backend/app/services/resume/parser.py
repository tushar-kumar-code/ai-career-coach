import re
from typing import Dict, Any, List


class ResumeParser:
    """Rule-based structured parser extracting contact info, sections, and items from raw resume text."""

    def parse(self, text: str) -> Dict[str, Any]:
        contact_info = self._extract_contact_info(text)
        sections = self._segment_sections(text)
        skills = self._extract_skills(text, sections.get("skills", ""))
        experience = self._parse_experience(sections.get("experience", ""))
        education = self._parse_education(sections.get("education", ""))
        projects = self._parse_projects(sections.get("projects", ""))

        return {
            "contact_info": contact_info,
            "summary": sections.get("summary", ""),
            "skills": skills,
            "experience": experience,
            "education": education,
            "projects": projects,
            "certifications": sections.get("certifications", []),
            "achievements": sections.get("achievements", [])
        }

    def _extract_contact_info(self, text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        name = lines[0] if lines else "Candidate"
        if len(name) > 50 or "@" in name or "http" in name:
            name = "Candidate"

        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text, re.IGNORECASE)
        github_match = re.search(r'github\.com/[\w-]+', text, re.IGNORECASE)
        portfolio_match = re.search(r'https?://(?:www\.)?[\w-]+\.(?:com|io|dev|me)', text, re.IGNORECASE)

        return {
            "name": name,
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
            "linkedin": f"https://{linkedin_match.group(0)}" if linkedin_match else "",
            "github": f"https://{github_match.group(0)}" if github_match else "",
            "portfolio": portfolio_match.group(0) if portfolio_match else ""
        }

    def _segment_sections(self, text: str) -> Dict[str, Any]:
        section_patterns = {
            "summary": r'(?:summary|profile|about me|objective)',
            "experience": r'(?:experience|work history|employment|experience history)',
            "education": r'(?:education|academic background|qualifications)',
            "projects": r'(?:projects|personal projects|key projects)',
            "skills": r'(?:skills|technical skills|technologies|core competencies)',
            "certifications": r'(?:certifications|licenses|courses)',
            "achievements": r'(?:achievements|honors|awards)'
        }

        # Simple section splitter based on common headers
        lines = text.splitlines()
        current_section = "summary"
        sections: Dict[str, List[str]] = {s: [] for s in section_patterns.keys()}

        for line in lines:
            line_clean = line.strip().lower()
            found = False
            for s_key, s_pat in section_patterns.items():
                if re.match(f'^{s_pat}:?$', line_clean):
                    current_section = s_key
                    found = True
                    break
            if not found and current_section:
                sections[current_section].append(line)

        return {k: "\n".join(v).strip() for k, v in sections.items()}

    def _extract_skills(self, full_text: str, skills_text: str) -> List[str]:
        common_tech_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "FastAPI",
            "Express", "HTML", "CSS", "Tailwind CSS", "SQL", "PostgreSQL", "MongoDB",
            "Docker", "Kubernetes", "AWS", "GCP", "Git", "GitHub", "CI/CD", "REST APIs",
            "GraphQL", "Pandas", "NumPy", "Scikit-Learn", "PyTorch", "TensorFlow",
            "Tableau", "PowerBI", "Figma", "Agile", "Scrum", "Jira", "Linux"
        ]

        found_skills = set()
        search_target = (skills_text + "\n" + full_text).lower()

        for skill in common_tech_skills:
            pattern = rf'\b{re.escape(skill.lower())}\b'
            if re.search(pattern, search_target):
                found_skills.add(skill)

        return sorted(list(found_skills))

    def _parse_experience(self, exp_text: str) -> List[Dict[str, Any]]:
        if not exp_text:
            return []
        blocks = [b.strip() for b in exp_text.split("\n\n") if b.strip()]
        exp_list = []
        for block in blocks[:5]:
            lines = block.splitlines()
            title = lines[0] if lines else "Role"
            exp_list.append({
                "title": title,
                "description": "\n".join(lines[1:]) if len(lines) > 1 else block
            })
        return exp_list

    def _parse_education(self, edu_text: str) -> List[Dict[str, Any]]:
        if not edu_text:
            return []
        lines = [line.strip() for line in edu_text.splitlines() if line.strip()]
        return [{"degree": line} for line in lines[:3]]

    def _parse_projects(self, proj_text: str) -> List[Dict[str, Any]]:
        if not proj_text:
            return []
        blocks = [b.strip() for b in proj_text.split("\n\n") if b.strip()]
        proj_list = []
        for block in blocks[:5]:
            lines = block.splitlines()
            proj_list.append({
                "name": lines[0] if lines else "Project",
                "description": "\n".join(lines[1:]) if len(lines) > 1 else block
            })
        return proj_list
