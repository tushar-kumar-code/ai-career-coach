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
        certifications = self._parse_certifications(sections.get("certifications", ""))
        achievements = self._parse_achievements(sections.get("achievements", ""))
        languages = self._parse_languages(sections.get("languages", ""))
        publications = self._parse_publications(sections.get("publications", ""))
        extracurriculars = self._parse_extracurriculars(sections.get("extracurriculars", ""))

        return {
            "contact_info": contact_info,
            "summary": sections.get("summary", ""),
            "skills": skills,
            "experience": experience,
            "education": education,
            "projects": projects,
            "certifications": certifications,
            "achievements": achievements,
            "languages": languages,
            "publications": publications,
            "extracurriculars": extracurriculars
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
            "summary": r'(?:summary|profile|about me|objective|professional summary|career objective)',
            "experience": r'(?:experience|work history|employment|experience history|professional experience|internships?|work experience)',
            "education": r'(?:education|academic background|qualifications|academic history|educational details|academics)',
            "projects": r'(?:projects|personal projects|key projects|academic projects|capstone projects?|major projects?|mini projects?|coursework projects?|selected projects)',
            "skills": r'(?:skills|technical skills|technologies|core competencies|key skills|it skills|technical expertise|skills & abilities|technical proficiencies)',
            "certifications": r'(?:certifications|licenses|courses|certificates|certifications & licenses|trainings? & certifications?|certifications & courses)',
            "achievements": r'(?:achievements|honors|awards|key achievements|honors & awards|accomplishments|hackathons|recognitions)',
            "languages": r'(?:languages|languages known|languages spoken)',
            "publications": r'(?:publications|research papers?|patents?|papers? published|journals)',
            "extracurriculars": r'(?:extracurricular(?:s| activities)?|co-curricular(?: activities)?|leadership(?: & activities)?|volunteering|volunteer work|activities)'
        }

        # Simple section splitter based on common headers
        lines = text.splitlines()
        current_section = "summary"
        sections: Dict[str, List[str]] = {s: [] for s in section_patterns.keys()}

        for line in lines:
            line_clean = line.strip().lower()
            # Strip trailing decorative punctuation, dashes, colons
            line_clean = re.sub(r'[\-_=*#:\s]+$', '', line_clean).strip()
            found = False
            for s_key, s_pat in section_patterns.items():
                if re.match(f'^{s_pat}$', line_clean):
                    current_section = s_key
                    found = True
                    break
            if not found and current_section:
                sections[current_section].append(line)

        return {k: "\n".join(v).strip() for k, v in sections.items()}

    def _is_invalid_skill(self, text: str) -> bool:
        """Reject non-skill tokens such as degrees, colleges, locations, date ranges, and sentence fragments."""
        if not text or not text.strip():
            return True
        t_clean = text.strip()
        t_lower = t_clean.lower()

        # 1. Reject education keywords, degrees, grades
        degree_patterns = [
            r'\b(?:b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?|bca|mca|b\.?sc|m\.?sc|bba|mba|phd)\b',
            r'\b(?:10th|12th|matric|intermediate|diploma|bachelor|master|degree|cbse|icse)\b',
            r'\b(?:school|college|institute|university|vidyalaya|academy|board|govt)\b',
            r'\(?\d{1,2}(?:\.\d+)?%\)?',  # e.g. (70.4%), 81.66%
            r'\b(?:cgpa|gpa|percentage|marks|grade)\b'
        ]
        for pat in degree_patterns:
            if re.search(pat, t_lower):
                return True

        # 2. Reject dates, years, ranges (e.g., 2025--2029, 2024-25, 2022-23)
        if re.search(r'\b(?:19|20)\d{2}\b', t_lower):
            return True

        # 3. Reject location / geographic words
        location_words = [
            'raipur', 'chhattisgarh', 'dhamtari', 'bhilai', 'delhi', 'mumbai', 'bangalore',
            'hyderabad', 'pune', 'chennai', 'kolkata', 'india', 'district', 'state', 'pin', 'road', 'nagar'
        ]
        if any(w in t_lower for w in location_words):
            return True

        # 4. Reject long sentence fragments or generic action phrases
        action_phrases = [
            'strengthen', 'seeking', 'motivated', 'eager to', 'responsible for', 'working on',
            'problem-solving', 'interest in', 'experience in', 'opportunity', 'internship', 'student'
        ]
        if any(w in t_lower for w in action_phrases):
            return True

        # 5. Length checks: single characters (except C or R) or excessively long phrases
        if len(t_clean) < 2 and t_lower not in ['c', 'r']:
            return True
        if len(t_clean) > 40:
            return True

        return False

    def _extract_skills(self, full_text: str, skills_text: str) -> List[str]:
        """Extract exact skills as written by the user in the resume's skills section without modification."""
        exact_skills = []
        if skills_text and skills_text.strip():
            lines = skills_text.strip().splitlines()
            header_words = ['language', 'skill', 'technolog', 'tool', 'framework', 'database', 'frontend', 'backend', 'core', 'technical', 'other', 'platform']

            for line in lines:
                line_clean = line.strip()
                if not line_clean:
                    continue

                # Handle categorized lines like "Languages: Python Basic, C Basic"
                parts = re.split(r'[:\-–]\s*', line_clean, maxsplit=1)
                if len(parts) > 1 and len(parts[0].split()) <= 3 and any(w in parts[0].lower() for w in header_words):
                    text_to_split = parts[1]
                else:
                    text_to_split = line_clean

                # Split by commas, pipes, semicolons, and bullet characters
                tokens = re.split(r'[,|;•·*▪►]+', text_to_split)
                for token in tokens:
                    item = token.strip()
                    # Strip leading numbering or bullet dashes like "1.", "-"
                    item = re.sub(r'^[0-9]+[\.\)]\s*', '', item).strip()
                    item = re.sub(r'^[-\s]+', '', item).strip()
                    if item and not self._is_invalid_skill(item) and not re.match(r'^(and|etc\.?|skills?)$', item, re.IGNORECASE):
                        if item not in exact_skills:
                            exact_skills.append(item)

        if exact_skills:
            return exact_skills

        # Fallback only if no explicit skills section existed in the document
        common_tech_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "FastAPI",
            "Express", "HTML", "CSS", "Tailwind CSS", "SQL", "PostgreSQL", "MongoDB",
            "Docker", "Kubernetes", "AWS", "GCP", "Git", "GitHub", "CI/CD", "REST APIs",
            "GraphQL", "Pandas", "NumPy", "Scikit-Learn", "PyTorch", "TensorFlow",
            "Tableau", "PowerBI", "Figma", "Agile", "Scrum", "Jira", "Linux"
        ]

        found_skills = set()
        search_target = full_text.lower()

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
            parts = title.split(" - ") if " - " in title else title.split(" at ")
            role = parts[0].strip() if parts else title
            company = parts[1].strip() if len(parts) > 1 else ""
            exp_list.append({
                "title": title,
                "role": role,
                "company": company,
                "description": "\n".join(lines[1:]) if len(lines) > 1 else block
            })
        return exp_list

    def _parse_education(self, edu_text: str) -> List[Dict[str, Any]]:
        if not edu_text:
            return []
        lines = [line.strip() for line in edu_text.splitlines() if line.strip()]
        edu_list = []
        for line in lines[:5]:
            parts = line.split(" - ") if " - " in line else line.split(" from ")
            degree = parts[0].strip() if parts else line
            inst = parts[1].strip() if len(parts) > 1 else ""
            edu_list.append({
                "degree": degree,
                "institution": inst
            })
        return edu_list

    def _parse_projects(self, proj_text: str) -> List[Dict[str, Any]]:
        if not proj_text or not proj_text.strip():
            return []
        
        # Split by double newlines first
        blocks = [b.strip() for b in proj_text.split("\n\n") if b.strip()]
        
        # If single block but multiple lines, look for bullet or numbered project headers
        if len(blocks) <= 1:
            raw_lines = [l.strip() for l in proj_text.splitlines() if l.strip()]
            candidate_blocks = []
            current_b = []
            for line in raw_lines:
                # Detect project header: numbered like "1. ", "Project 1:", or bullet followed by title/tech
                is_header = (
                    re.match(r'^(?:[0-9]+[\.\)]|•|\*|▪|-)\s+[A-Z0-9]', line) or
                    re.search(r'\(.*?(?:React|Python|Java|Node|Flutter|HTML|CSS|AWS|SQL|AI|ML).*?\)', line, re.IGNORECASE) or
                    re.match(r'^(?:project|title)\s*:\s*', line, re.IGNORECASE)
                )
                if is_header and current_b and len(current_b) >= 2:
                    candidate_blocks.append("\n".join(current_b))
                    current_b = [line]
                else:
                    current_b.append(line)
            if current_b:
                candidate_blocks.append("\n".join(current_b))
            if len(candidate_blocks) > 1:
                blocks = candidate_blocks

        proj_list = []
        for block in blocks[:8]:
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            if not lines:
                continue
            first_line = lines[0]
            # Strip leading bullet/numbering
            clean_title = re.sub(r'^(?:[0-9]+[\.\)]|•|\*|▪|-)\s*', '', first_line).strip()
            
            # Extract technologies from parentheses or brackets e.g., "AI Chatbot (React, FastAPI, Gemini)"
            tech_match = re.search(r'[\(\[]([^\)\]]+)[\)\]]', clean_title)
            techs = []
            if tech_match:
                tech_str = tech_match.group(1)
                techs = [t.strip() for t in re.split(r'[,|/]', tech_str) if len(t.strip()) < 30]
                clean_title = re.sub(r'\s*[\(\[][^\)\]]+[\)\]]', '', clean_title).strip()
            
            # Extract link if in block
            link_match = re.search(r'https?://[^\s\)]+', block)
            proj_link = link_match.group(0) if link_match else ""

            proj_list.append({
                "title": clean_title if clean_title else "Project",
                "name": clean_title if clean_title else "Project",
                "role": "Developer",
                "technologies": techs,
                "description": "\n".join(lines[1:]) if len(lines) > 1 else clean_title,
                "link": proj_link
            })
        return proj_list

    def _parse_certifications(self, cert_text: str) -> List[Dict[str, Any]]:
        if not cert_text or not cert_text.strip():
            return []
        lines = [l.strip() for l in cert_text.splitlines() if l.strip()]
        cert_list = []
        for line in lines[:8]:
            clean_line = re.sub(r'^(?:[0-9]+[\.\)]|•|\*|▪|-)\s*', '', line).strip()
            if not clean_line or len(clean_line) < 3:
                continue
            parts = re.split(r'\s*[-–|]\s*|\s+by\s+|\s+from\s+', clean_line, maxsplit=2)
            name = parts[0].strip() if parts else clean_line
            issuer = parts[1].strip() if len(parts) > 1 else ""
            date_match = re.search(r'\b(?:19|20)\d{2}\b', clean_line)
            issue_date = date_match.group(0) if date_match else ""
            link_match = re.search(r'https?://[^\s\)]+', clean_line)
            
            cert_list.append({
                "name": name,
                "issuer": issuer,
                "issue_date": issue_date,
                "credential_id_or_url": link_match.group(0) if link_match else ""
            })
        return cert_list

    def _parse_achievements(self, ach_text: str) -> List[Dict[str, Any]]:
        if not ach_text or not ach_text.strip():
            return []
        lines = [l.strip() for l in ach_text.splitlines() if l.strip()]
        ach_list = []
        for line in lines[:8]:
            clean_line = re.sub(r'^(?:[0-9]+[\.\)]|•|\*|▪|-)\s*', '', line).strip()
            if not clean_line or len(clean_line) < 4:
                continue
            year_match = re.search(r'\b(?:19|20)\d{2}\b', clean_line)
            ach_list.append({
                "title": clean_line[:80].strip(),
                "issuer_or_event": "",
                "year": year_match.group(0) if year_match else "",
                "description": clean_line
            })
        return ach_list

    def _parse_languages(self, lang_text: str) -> List[Dict[str, Any]]:
        if not lang_text or not lang_text.strip():
            return []
        tokens = re.split(r'[,|;\n•·*▪►]+', lang_text)
        known_langs = ["english", "hindi", "spanish", "french", "german", "mandarin", "japanese", "bengali", "marathi", "tamil", "telugu", "gujarati", "kannada", "punjabi", "urdu", "russian", "arabic"]
        lang_list = []
        for t in tokens:
            item = re.sub(r'^(?:[0-9]+[\.\)]|•|\*|▪|-)\s*', '', t).strip()
            if not item:
                continue
            # Extract proficiency if in brackets, e.g. "English (Fluent)"
            prof_match = re.search(r'\((.*?)\)', item)
            prof = prof_match.group(1).strip() if prof_match else "Proficient"
            clean_l = re.sub(r'\(.*?\)', '', item).strip()
            if clean_l and (clean_l.lower() in known_langs or len(clean_l.split()) <= 2):
                lang_list.append({
                    "language": clean_l.capitalize(),
                    "proficiency": prof
                })
        return lang_list

    def _parse_publications(self, pub_text: str) -> List[Dict[str, Any]]:
        if not pub_text or not pub_text.strip():
            return []
        lines = [l.strip() for l in pub_text.splitlines() if l.strip()]
        pub_list = []
        for line in lines[:5]:
            clean_line = re.sub(r'^(?:[0-9]+[\.\)]|•|\*|▪|-)\s*', '', line).strip()
            if not clean_line:
                continue
            date_match = re.search(r'\b(?:19|20)\d{2}\b', clean_line)
            link_match = re.search(r'https?://[^\s\)]+', clean_line)
            pub_list.append({
                "title": clean_line[:100],
                "authors_or_journal": "",
                "date_or_year": date_match.group(0) if date_match else "",
                "url_or_doi": link_match.group(0) if link_match else "",
                "description": clean_line
            })
        return pub_list

    def _parse_extracurriculars(self, extra_text: str) -> List[Dict[str, Any]]:
        if not extra_text or not extra_text.strip():
            return []
        lines = [l.strip() for l in extra_text.splitlines() if l.strip()]
        extra_list = []
        for line in lines[:5]:
            clean_line = re.sub(r'^(?:[0-9]+[\.\)]|•|\*|▪|-)\s*', '', line).strip()
            if not clean_line or len(clean_line) < 4:
                continue
            date_match = re.search(r'\b(?:19|20)\d{2}\b', clean_line)
            extra_list.append({
                "role": clean_line[:60],
                "organization": "",
                "duration": date_match.group(0) if date_match else "",
                "description": clean_line
            })
        return extra_list
