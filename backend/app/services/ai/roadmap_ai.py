import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from app.services.ai.client import AIService

logger = logging.getLogger(__name__)



class AIRoadmapTaskContent(BaseModel):
    title: str = Field(description="Actionable title of topic/module to learn")
    description: str = Field(description="Clear overview of what this topic covers and why it fits here")
    estimated_minutes: int = Field(description="Estimated study & practice time in minutes (e.g. 30-60)")
    task_type: str = Field(description="Task category: Learn, Practice, Project, or Review")
    why_it_matters: str = Field(description="Personalized rationale explaining importance for target role")
    # Topic-wise syllabus & guidance fields (tells user WHAT to learn)
    topics_to_learn: List[str] = Field(
        default_factory=list,
        description="Detailed list of 4-6 specific subtopics, concepts, keywords, or syntax rules the student must cover"
    )
    learning_focus: str = Field(
        default="",
        description="Clear advice on what to prioritize or watch out for while studying this topic"
    )
    practice_goal: str = Field(
        default="",
        description="Specific hands-on coding task, exercise, or mini-program to build to verify understanding"
    )
    expected_outcome: str = Field(
        default="",
        description="Concrete deliverable, working script, or working output expected from completing this task"
    )
    verification_method: str = Field(
        default="",
        description="Concrete verification criteria: e.g. Pass conceptual quiz, run test suite, check output against expected spec"
    )
    recommended_resources: List[str] = Field(
        default_factory=list,
        description="Recommended standard documentation topics, tutorials, or search queries (e.g. 'MDN - JS Functions', 'Official Docs')"
    )
    difficulty_level: str = Field(
        default="Beginner",
        description="Difficulty tier: Scratch, Beginner, Intermediate, or Advanced"
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Key prerequisites required before tackling this topic"
    )
    # Teacher guidance: explanation snippet & clear next step
    concept_explanation: str = Field(default="", description="Teacher-like intuitive mental model or small example")
    next_step: str = Field(default="", description="Clear actionable next step after completing this task")
    practice_exercise: str = Field(default="")
    check_quiz_question: str = Field(default="")
    check_quiz_options: List[str] = Field(default_factory=list)
    check_quiz_answer: str = Field(default="")


class AIProjectIdea(BaseModel):
    title: str = Field(description="Hands-on portfolio project title")
    objective: str = Field(description="Core project objective and scope")
    skills_practiced: List[str] = Field(default_factory=list, description="Skills reinforced in project")
    difficulty: str = Field(description="Difficulty level: Scratch, Beginner, Intermediate, or Advanced")
    expected_outcome: str = Field(description="Concrete deliverable (e.g., Working REST API, Interactive UI Dashboard)")
    resume_relevance: str = Field(description="How this project strengthens candidate's resume for target role")


class AIRoadmapPhaseContent(BaseModel):
    phase_title: str = Field(description="Descriptive title of roadmap phase")
    learning_objectives: List[str] = Field(default_factory=list, description="Core phase learning objectives")
    milestone_title: str = Field(description="Milestone title for this phase")
    milestone_criteria: str = Field(description="Concrete criteria to verify milestone completion")
    tasks: List[AIRoadmapTaskContent] = Field(default_factory=list, description="Structured actionable tasks")
    project: Optional[AIProjectIdea] = Field(default=None, description="Hands-on phase project recommendation")


class AIRoadmapPhaseOutline(BaseModel):
    phase_number: int = Field(description="1-indexed phase number")
    title: str = Field(description="Domain-tailored level title representing the milestone/tier (e.g. 'Linux, Shell & Infrastructure Foundations')")
    phase_type: str = Field(description="Phase classification e.g. Foundations, Core Logic, Domain Frameworks, Architecture, Production Capstone")
    skills: List[str] = Field(default_factory=list, description="3-5 specific domain skills, tools, or libraries for this level")
    level_objective: str = Field(default="", description="Clear 1-sentence learning objective of what the student will master in this level")
    milestone_title: str = Field(default="", description="Practical milestone title to verify completion of this level")


class AIRoadmapStructure(BaseModel):
    target_domain: str = Field(description="Target career/domain name")
    recommended_level_count: int = Field(description="Total number of levels designed (flexible, e.g. 2 to 8)")
    domain_overview: str = Field(default="", description="Brief overview of the curriculum designed for this domain")
    phases: List[AIRoadmapPhaseOutline] = Field(default_factory=list, description="Ordered list of sequential learning levels")


class RoadmapAIService:
    """Dedicated AI Service generating personalized learning objectives, task content, and project ideas."""

    def __init__(self, provider=None):
        self.provider = provider or AIService.get_provider("groq")

    def _fallback_domain_structure(
        self,
        target_career: str,
        user_level: str = "Beginner",
        target_phases_count: Optional[int] = None,
        track_pace: Optional[str] = None,
        career_goal: str = "Entry-level Job",
        hours_per_day: int = 1,
        known_skills: Optional[List[str]] = None,
        weak_areas: Optional[List[str]] = None,
        domain_requirement: Optional[str] = None,
        **kwargs
    ) -> AIRoadmapStructure:
        """Dynamic domain-aware fallback generator producing flexible levels tailored to any domain and user level."""
        is_scratch_beginner = (user_level.lower() in ["beginner", "scratch"] or not known_skills)
        d_lower = (target_career or "").lower()

        # 1. Determine flexible number of levels
        if target_phases_count and 2 <= target_phases_count <= 9:
            num_levels = target_phases_count
        elif track_pace == "Express":
            num_levels = 3
        elif track_pace == "Comprehensive":
            num_levels = 6
        elif user_level.lower() == "advanced":
            num_levels = 3
        elif user_level.lower() == "intermediate":
            num_levels = 4
        else:
            num_levels = 5

        # 2. Domain-tailored phase templates
        if any(k in d_lower for k in ["generative ai", "genai", "ai agent", "agentic", "llm", "prompt engineering"]):
            # Scenario B: Generative AI & AI Agents
            # If user already knows Python (e.g. intermediate), do not repeat basic Python syntax!
            knows_python = known_skills and any("python" in s.lower() for s in known_skills)
            tiers = [
                {
                    "title": f"{target_career}: Python & API Foundations for GenAI" if (is_scratch_beginner and not knows_python) else f"{target_career}: LLM Foundations & Prompt Engineering",
                    "type": "Foundations from Scratch" if (is_scratch_beginner and not knows_python) else "Core LLM Logic & Orchestration",
                    "skills": ["Python for AI", "API Integrations", "Environment Setup", "Git"] if (is_scratch_beginner and not knows_python) else ["Prompt Engineering", "OpenAI / Open-Source LLMs", "Few-Shot & Chain-of-Thought", "Structured JSON Outputs"],
                    "milestone": "Foundational Python & API Setup Milestone" if (is_scratch_beginner and not knows_python) else "Deterministic Prompt & Output Engineering Milestone"
                },
                {
                    "title": f"{target_career}: Semantic Search, Embeddings & Vector Databases",
                    "type": "Vector Retrieval & Indexing",
                    "skills": ["Embeddings & Vector Search", "Vector Databases", "Semantic Search", "Chunking Strategies", "Hybrid Search"],
                    "milestone": "Vector Indexing & Semantic Retrieval Milestone"
                },
                {
                    "title": f"{target_career}: Retrieval-Augmented Generation (RAG) Architecture",
                    "type": "Knowledge-Augmented Systems",
                    "skills": ["Retrieval-Augmented Generation (RAG)", "Advanced RAG", "Document Chunking", "RAG Evaluation (RAGAS)", "Hallucination Mitigation"],
                    "milestone": "Production Enterprise RAG System Milestone"
                },
                {
                    "title": f"{target_career}: Function Calling & External Tool Execution",
                    "type": "Action-Augmented Systems",
                    "skills": ["Function Calling & Tool Use", "API Tool Execution", "Schema Definition & Validation", "Error Recovery in Tool Calls"],
                    "milestone": "Autonomous Tool-Augmented LLM Milestone"
                },
                {
                    "title": f"{target_career}: Autonomous AI Agents & Multi-Agent Systems",
                    "type": "Autonomous Agent Systems",
                    "skills": ["AI Agents", "LangGraph", "Multi-Agent Systems", "Stateful Agent Memory & Planning", "Human-in-the-Loop Workflows"],
                    "milestone": "Autonomous Multi-Agent Workflow Milestone"
                },
                {
                    "title": f"{target_career}: Agent Evaluation, Guardrails & Production Capstone",
                    "type": f"{career_goal} Technical Verification & Portfolio Capstone",
                    "skills": ["Agent Evaluation & Guardrails", "NeMo Guardrails / Llama Guard", "FastAPI Agent Serving", f"{target_career} Portfolio Showcase"],
                    "milestone": "Production-Grade AI Agent Capstone Milestone"
                }
            ]
        elif any(k in d_lower for k in ["ai security", "llm security", "ai safety", "adversarial ml"]):
            # Scenario C: AI Security & AI Cybersecurity
            tiers = [
                {
                    "title": f"{target_career}: Linux, Python Scripting & Security Bedrock",
                    "type": "Foundations from Scratch" if is_scratch_beginner else "Security Foundations",
                    "skills": ["Cybersecurity Fundamentals", "Linux", "Python", "Networking Protocols", "Git"],
                    "milestone": "Security Environment & Scripting Foundations Milestone"
                },
                {
                    "title": f"{target_career}: Modern AI Architecture & Threat Landscape",
                    "type": "AI Threat Identification",
                    "skills": ["AI Threat Modeling", "OWASP LLM Top 10", "LLMs", "Application Security"],
                    "milestone": "AI System Threat Identification Milestone"
                },
                {
                    "title": f"{target_career}: Prompt Injection, Jailbreaking & Defensive Hardening",
                    "type": "Adversarial Prompt Security",
                    "skills": ["Prompt Injection & Defense", "Prompt Engineering", "Input Sanitization", "Dual-LLM Defense"],
                    "milestone": "Prompt Injection Exploitation & Defense Milestone"
                },
                {
                    "title": f"{target_career}: Data Poisoning, Model Extraction & Privacy Attacks",
                    "type": "Model & Data Integrity",
                    "skills": ["Data Poisoning & Model Privacy", "Machine Learning", "Model Inversion", "PII Redaction & Privacy"],
                    "milestone": "Model Privacy & Data Integrity Verification Milestone"
                },
                {
                    "title": f"{target_career}: Adversarial ML, Red Teaming & Guardrails",
                    "type": "Offensive & Defensive Testing",
                    "skills": ["AI Red Teaming & Guardrails", "Adversarial Perturbations", "Automated Red Teaming", "Evasion Detection"],
                    "milestone": "Automated Red-Teaming & Guardrail Hardening Milestone"
                },
                {
                    "title": f"{target_career}: AI Governance, Auditing & Production Capstone",
                    "type": f"{career_goal} Technical Verification & Portfolio Capstone",
                    "skills": ["AI Security Auditing", "NIST AI Risk Management", "Secure Agent Tool Sandboxing", f"{target_career} Defense Portfolio"],
                    "milestone": "Enterprise AI Security Audit & Defense Capstone Milestone"
                }
            ]
        elif any(k in d_lower for k in ["devops", "cloud", "sre", "infrastructure", "platform"]):
            tiers = [
                {
                    "title": f"{target_career}: Linux, Shell & Infrastructure Foundations",
                    "type": "Foundations from Scratch" if is_scratch_beginner else "Core Systems & Infrastructure",
                    "skills": ["Linux", "Bash Scripting", "Git", "Networking & TCP/IP"],
                    "milestone": "Command-Line & System Administration Mastery"
                },
                {
                    "title": f"{target_career}: Containerization with Docker & Podman",
                    "type": "Core Domain Tooling",
                    "skills": ["Docker", "Multi-stage Builds", "Container Security", "Docker Compose"],
                    "milestone": "Production Containerized Services Milestone"
                },
                {
                    "title": f"{target_career}: Orchestration with Kubernetes & Helm",
                    "type": "Clustering & Scale",
                    "skills": ["Kubernetes", "Helm", "ConfigMaps & Secrets", "Ingress Controllers"],
                    "milestone": "Resilient Cluster Orchestration Milestone"
                },
                {
                    "title": f"{target_career}: CI/CD Pipelines & GitOps Automation",
                    "type": "Applied Automation",
                    "skills": ["CI/CD Pipelines", "GitHub Actions", "ArgoCD", "Automated Testing"],
                    "milestone": "Zero-Touch Continuous Delivery Milestone"
                },
                {
                    "title": f"{target_career}: Infrastructure as Code & Cloud Architecture",
                    "type": "Cloud Architecture",
                    "skills": ["Terraform", "AWS / Cloud Platforms", "Cloud Security & IAM", "VPC & Networking"],
                    "milestone": "Multi-Environment Cloud Architecture Milestone"
                },
                {
                    "title": f"{target_career}: Observability, SRE & Production Capstone",
                    "type": f"{career_goal} Technical Verification & Portfolio Capstone",
                    "skills": ["Prometheus", "Grafana", "Distributed Tracing", "SRE Best Practices", "Disaster Recovery"],
                    "milestone": "High-Availability Production Capstone Milestone"
                }
            ]
        elif any(k in d_lower for k in ["data science", "data scientist", "machine learning", "ml", "ai engineer", "deep learning"]):
            # Scenario A: AI & Machine Learning
            tiers = [
                {
                    "title": f"{target_career}: Python, Math & Data Foundations",
                    "type": "Foundations from Scratch" if is_scratch_beginner else "Mathematical & Programming Bedrock",
                    "skills": ["Python for Data Science", "Linear Algebra & Vectors", "Calculus & Probability", "NumPy & Numerical Computing", "Git & Jupyter"],
                    "milestone": "Scientific Computing & Math Foundations Milestone"
                },
                {
                    "title": f"{target_career}: Data Wrangling, Exploration & SQL",
                    "type": "Data Engineering & Exploration",
                    "skills": ["Pandas", "SQL for Data Science", "Exploratory Data Analysis (EDA)", "Data Cleaning & Imputation", "Matplotlib & Seaborn"],
                    "milestone": "Exploratory Insights & Feature Engineering Milestone"
                },
                {
                    "title": f"{target_career}: Classical Machine Learning Algorithms",
                    "type": "Applied Machine Learning",
                    "skills": ["Scikit-Learn", "Supervised Learning (Regression & Trees)", "Unsupervised Learning (K-Means/PCA)", "Cross-Validation & Grid Search", "Evaluation Metrics (ROC-AUC/F1)"],
                    "milestone": "Supervised & Unsupervised Machine Learning Milestone"
                },
                {
                    "title": f"{target_career}: Deep Learning & Neural Architectures",
                    "type": "Deep Learning & Neural Networks",
                    "skills": ["PyTorch Foundations", "Tensors & Autograd", "Neural Network Architectures (MLP/CNN)", "Loss Functions & Optimizers", "Model Overfitting & Regularization"],
                    "milestone": "Deep Learning & PyTorch Model Implementation Milestone"
                },
                {
                    "title": f"{target_career}: Model Deployment & Practical Engineering",
                    "type": "Engineering & MLOps",
                    "skills": ["FastAPI Model Serving", "Docker for ML", "Model Evaluation & Benchmarking", "Data Pipeline Validation", "Git Best Practices"],
                    "milestone": "End-to-End Model Serving & API Milestone"
                },
                {
                    "title": f"{target_career}: Internship Portfolio Capstone & Technical Interview Prep" if career_goal == "Internship" else f"{target_career}: Production ML Capstone & Technical Verification",
                    "type": f"{career_goal} Technical Verification & Portfolio Capstone",
                    "skills": [f"{target_career} Portfolio Project", "Reproducible ML Pipeline", "ML Technical Interview Problems", "Resume & Project Presentation"],
                    "milestone": "Internship-Ready Machine Learning Portfolio Milestone" if career_goal == "Internship" else "Production Machine Learning Capstone Milestone"
                }
            ]
        elif any(k in d_lower for k in ["frontend", "front-end", "ui developer", "react developer", "web developer"]):
            tiers = [
                {
                    "title": f"{target_career}: Modern Web Core & JavaScript Mastery",
                    "type": "Foundations from Scratch" if is_scratch_beginner else "Core Logic & Web Foundations",
                    "skills": ["HTML/CSS", "JavaScript ES6+", "DOM & Events", "Developer Setup & Git Basics"],
                    "milestone": "Modern Web & Dynamic JavaScript Milestone"
                },
                {
                    "title": f"{target_career}: Modern Component Architecture & React",
                    "type": "Component Frameworks",
                    "skills": ["React", "Component Patterns", "Hooks & Lifecycle", "Tailwind CSS"],
                    "milestone": "Interactive Single-Page Application Milestone"
                },
                {
                    "title": f"{target_career}: Full-Stack React & Next.js Architecture",
                    "type": "Modern Web Frameworks",
                    "skills": ["Next.js", "Server Components", "State Management", "REST & GraphQL APIs"],
                    "milestone": "Production Full-Stack Web App Milestone"
                },
                {
                    "title": f"{target_career}: Web Performance, Testing & Security",
                    "type": "Enterprise Quality",
                    "skills": ["Vitest / Jest", "Playwright", "Web Vitals Optimization", "Accessibility (a11y)"],
                    "milestone": "High-Performance Tested Application Milestone"
                },
                {
                    "title": f"{target_career}: Design Systems & Scalable Architecture",
                    "type": "Scalable Systems",
                    "skills": ["TypeScript", "Design Systems", "Microfrontends", "CI/CD & Cloud Deployment"],
                    "milestone": "Enterprise Frontend Architecture Milestone"
                },
                {
                    "title": f"{target_career}: Production Capstone & Job Readiness",
                    "type": f"{career_goal} Technical Verification & Portfolio Capstone",
                    "skills": [f"{target_career} Capstone Project", "Technical Interview Prep", "Resume & Portfolio Optimization"],
                    "milestone": "Production Capstone & Placement Verification Milestone"
                }
            ]
        elif any(k in d_lower for k in ["backend", "back-end", "api developer"]):
            tiers = [
                {
                    "title": f"{target_career}: Core Programming & Logic Foundations",
                    "type": "Foundations from Scratch" if is_scratch_beginner else "Core Logic & Syntax",
                    "skills": ["Programming Fundamentals & Logic", "Developer Setup & Git Basics", "OOP & Data Structures"],
                    "milestone": "Clean Modular Backend Coding Milestone"
                },
                {
                    "title": f"{target_career}: Database Design & Persistence",
                    "type": "Data Persistence",
                    "skills": ["SQL & Relational Databases", "PostgreSQL", "Database Indexing", "Transactions & ACID", "ORM Patterns"],
                    "milestone": "High-Performance Data Storage Milestone"
                },
                {
                    "title": f"{target_career}: RESTful Services & API Security",
                    "type": "Service Architecture",
                    "skills": ["FastAPI / Express", "RESTful Architecture", "Authentication (JWT/OAuth)", "Input Validation & Middleware"],
                    "milestone": "Secure Production REST API Milestone"
                },
                {
                    "title": f"{target_career}: Caching, Message Queues & System Design",
                    "type": "Distributed Systems",
                    "skills": ["Redis Caching", "RabbitMQ / Kafka", "Microservices Patterns", "High-Availability System Design"],
                    "milestone": "High-Concurrency Scalable Architecture Milestone"
                },
                {
                    "title": f"{target_career}: Cloud Deployment & DevOps Integration",
                    "type": "Production Operations",
                    "skills": ["Docker", "CI/CD Automation", "Cloud Platforms (AWS)", "Monitoring & Logging"],
                    "milestone": "Cloud-Native Deployable Service Milestone"
                },
                {
                    "title": f"{target_career}: Production Capstone & Technical Readiness",
                    "type": f"{career_goal} Technical Verification & Portfolio Capstone",
                    "skills": [f"{target_career} Capstone Project", "Backend System Design Interview", "Portfolio Optimization"],
                    "milestone": "Enterprise Backend Capstone Milestone"
                }
            ]
        elif any(k in d_lower for k in ["cyber", "security", "infosec", "penetration", "soc"]):
            tiers = [
                {
                    "title": f"{target_career}: Networking & Operating System Foundations",
                    "type": "Foundations from Scratch" if is_scratch_beginner else "System Security Foundations",
                    "skills": ["Networking & Protocols (TCP/IP)", "Linux Security Fundamentals", "Command Line Administration", "Git"],
                    "milestone": "System Administration & Networking Security Milestone"
                },
                {
                    "title": f"{target_career}: Security Principles & Cryptography",
                    "type": "Core Security Logic",
                    "skills": ["Cryptography & PKI", "Threat Modeling", "Authentication Protocols", "Security Standards"],
                    "milestone": "Cryptographic Protection & Threat Modeling Milestone"
                },
                {
                    "title": f"{target_career}: Vulnerability Assessment & Web Security",
                    "type": "Vulnerability Analysis",
                    "skills": ["OWASP Top 10", "Vulnerability Scanning", "Burp Suite", "Web Security Testing"],
                    "milestone": "Application Security & Assessment Milestone"
                },
                {
                    "title": f"{target_career}: Defensive Security, SIEM & Incident Response",
                    "type": "Security Operations",
                    "skills": ["SIEM & Log Analysis", "Wireshark", "Incident Handling", "Firewalls & IDS/IPS"],
                    "milestone": "Active Defense & Incident Response Milestone"
                },
                {
                    "title": f"{target_career}: Penetration Testing & Ethical Hacking",
                    "type": "Offensive Security",
                    "skills": ["Penetration Testing Methodologies", "Nmap", "Metasploit", "Exploit Analysis"],
                    "milestone": "Hands-On Penetration Testing Milestone"
                },
                {
                    "title": f"{target_career}: Enterprise Security Audit & Capstone",
                    "type": f"{career_goal} Technical Verification & Portfolio Capstone",
                    "skills": ["Security Auditing", "Compliance (SOC2/ISO)", "Portfolio Defense Project", "Interview Readiness"],
                    "milestone": "Enterprise Security Capstone Milestone"
                }
            ]
        elif any(k in d_lower for k in ["mobile", "android", "ios", "flutter", "react native"]):
            tiers = [
                {
                    "title": f"{target_career}: Mobile UI & Language Foundations",
                    "type": "Foundations from Scratch" if is_scratch_beginner else "Mobile Foundations",
                    "skills": ["Programming Fundamentals & Logic", "Dart / TypeScript", "Mobile UI Layouts", "Git"],
                    "milestone": "Interactive Mobile Layout Milestone"
                },
                {
                    "title": f"{target_career}: State Management & Navigation Systems",
                    "type": "Application Architecture",
                    "skills": ["State Management (Bloc/Provider/Redux)", "Screen Navigation", "Component Reusability", "Responsive UI"],
                    "milestone": "Structured Multi-Screen App Milestone"
                },
                {
                    "title": f"{target_career}: Local Storage, Offline Sync & REST APIs",
                    "type": "Data & Network Integration",
                    "skills": ["REST API Integration", "Local Storage (SQLite/Hive)", "Offline First Architecture", "Authentication"],
                    "milestone": "Full-Featured Connected Mobile App Milestone"
                },
                {
                    "title": f"{target_career}: Native Device Capabilities & Animations",
                    "type": "Device Hardware & UX",
                    "skills": ["Camera & Geolocation", "Push Notifications", "Smooth Micro-Animations", "Performance Profiling"],
                    "milestone": "Hardware-Integrated App Milestone"
                },
                {
                    "title": f"{target_career}: App Security, Testing & CI/CD",
                    "type": "Production Engineering",
                    "skills": ["Mobile Security", "Unit & Widget Testing", "CI/CD for Mobile", "Automated Builds"],
                    "milestone": "Production-Tested App Milestone"
                },
                {
                    "title": f"{target_career}: Production App Store Release & Capstone",
                    "type": f"{career_goal} Technical Verification & Portfolio Capstone",
                    "skills": ["Store Deployment (Play Store / App Store)", "Portfolio Showcase App", "Mobile Interview Prep"],
                    "milestone": "Published Mobile App Capstone Milestone"
                }
            ]
        else:
            # Universal dynamic domain mapping
            tiers = [
                {
                    "title": f"{target_career}: Core Fundamentals & Tooling",
                    "type": "Foundations from Scratch" if is_scratch_beginner else "Domain Foundations",
                    "skills": ["Programming Fundamentals & Logic", f"{target_career} Environment Setup", "Core Syntax & Logic", "Git Basics"],
                    "milestone": f"{target_career} Foundations Milestone"
                },
                {
                    "title": f"{target_career}: Applied Core Workflows & Patterns",
                    "type": "Core Domain Workflows",
                    "skills": [f"{target_career} Core Tools", "Data Structures & Flow", "Practical Problem Solving", "Modular Architecture"],
                    "milestone": f"{target_career} Core Competence Milestone"
                },
                {
                    "title": f"{target_career}: Modern Frameworks & Industry Standards",
                    "type": "Industry Frameworks",
                    "skills": [f"{target_career} Industry Standards", "API & Systems Integration", "Testing & Debugging", "Performance Optimization"],
                    "milestone": f"{target_career} Production Standards Milestone"
                },
                {
                    "title": f"{target_career}: Advanced Architecture & Systems",
                    "type": "Advanced Engineering",
                    "skills": [f"{target_career} Advanced Architecture", "System Design", "Scalability & Robustness", "Security Best Practices"],
                    "milestone": f"{target_career} Advanced Systems Milestone"
                },
                {
                    "title": f"{target_career}: Quality Engineering & Deployment",
                    "type": "Quality & Operations",
                    "skills": ["Automated Testing", "CI/CD & Deployment", "Monitoring & Logging", "Code Review Standards"],
                    "milestone": f"{target_career} Enterprise Polish Milestone"
                },
                {
                    "title": f"{target_career}: Capstone Portfolio & Job Readiness",
                    "type": f"{career_goal} Technical Verification & Portfolio Capstone",
                    "skills": [f"{target_career} Capstone Project", "Technical Interview Prep", "Resume & Portfolio Optimization"],
                    "milestone": f"{target_career} Career Readiness Capstone Milestone"
                }
            ]

        # Adapt career goal in final tier
        if career_goal == "Internship":
            tiers[-1]["type"] = "Internship Technical Readiness & Portfolio Capstone"
            tiers[-1]["title"] = f"{target_career}: Internship Portfolio & Technical Interview Prep"
        elif career_goal == "Certification":
            tiers[-1]["type"] = "Certification Exam Readiness & Verification"
            tiers[-1]["title"] = f"{target_career}: Certification Exam Blueprints & Verification Drills"
            if len(tiers) > 1:
                tiers[0]["type"] = "Exam Blueprint Core Fundamentals"
        elif career_goal == "Career Transition":
            tiers[-1]["type"] = "Career Transition Capstone & Portfolio"

        # Inject weak areas into intermediate tiers if specified
        if weak_areas:
            for w in weak_areas:
                if len(tiers) > 1 and w not in tiers[1]["skills"]:
                    tiers[1]["skills"].append(w)

        # 3. Select exact num_levels from tiers
        if num_levels == 2:
            selected_indices = [0, len(tiers) - 1]
        elif num_levels == 3:
            selected_indices = [0, max(1, len(tiers) // 2), len(tiers) - 1]
        elif num_levels == 4:
            selected_indices = [0, 1, max(2, len(tiers) - 2), len(tiers) - 1]
        elif num_levels == 5:
            selected_indices = [0, 1, 2, max(3, len(tiers) - 2), len(tiers) - 1]
        elif num_levels == 6:
            selected_indices = list(range(min(6, len(tiers))))
        else:
            selected_indices = list(range(len(tiers)))
            while len(selected_indices) < num_levels:
                extra_idx = len(selected_indices)
                tiers.insert(len(tiers) - 1, {
                    "title": f"{target_career}: Advanced Specialization Level {extra_idx}",
                    "type": "Deep Specialization",
                    "skills": [f"{target_career} Advanced Concepts", f"{target_career} Scale & Performance"],
                    "milestone": f"{target_career} Deep Specialization Milestone"
                })
                selected_indices.append(len(selected_indices))

        chosen_tiers = [tiers[i] for i in selected_indices[:num_levels]]

        phases = []
        for idx, t in enumerate(chosen_tiers, start=1):
            phases.append(AIRoadmapPhaseOutline(
                phase_number=idx,
                title=t["title"],
                phase_type=t["type"],
                skills=t["skills"],
                level_objective=f"Master key concepts and build practical competence in {', '.join(t['skills'][:3])}.",
                milestone_title=t["milestone"]
            ))

        return AIRoadmapStructure(
            target_domain=target_career,
            recommended_level_count=len(phases),
            domain_overview=f"Personalized, flexible curriculum tailored for {target_career} ({user_level} level, {career_goal}).",
            phases=phases
        )

    async def generate_domain_roadmap_structure(
        self,
        target_career: str,
        user_level: str = "Beginner",
        target_phases_count: Optional[int] = None,
        track_pace: Optional[str] = None,
        career_goal: str = "Entry-level Job",
        hours_per_day: int = 1,
        known_skills: Optional[List[str]] = None,
        weak_areas: Optional[List[str]] = None,
        domain_requirement: Optional[str] = None
    ) -> AIRoadmapStructure:
        """Designs a flexible, domain-tailored roadmap structure using Groq AI."""
        level_req_clause = ""
        if target_phases_count and 2 <= target_phases_count <= 9:
            level_req_clause = f"MANDATORY LEVEL COUNT: The user explicitly requested EXACTLY {target_phases_count} levels. You MUST produce exactly {target_phases_count} phases."
        elif track_pace == "Express":
            level_req_clause = "MANDATORY LEVEL COUNT: The user requested an Express Track. Generate exactly 3 focused, high-impact levels."
        elif track_pace == "Comprehensive":
            level_req_clause = "MANDATORY LEVEL COUNT: The user requested a Comprehensive In-Depth Track. Generate 6 to 8 comprehensive levels."
        else:
            level_req_clause = (
                f"FLEXIBLE LEVEL COUNT: The number of levels MUST NOT be fixed to 5 arbitrarily. "
                f"Analyze the scope of the domain '{target_career}', user level '{user_level}', and goals. "
                f"Choose the optimal number of levels (typically between 3 to 7 levels) that best suits this learner."
            )

        prompt = f"""You are a World-Class Curriculum Director & Technical Architect.
Your task is to design a personalized, flexible learning roadmap structure specifically tailored for the domain: '{target_career}'.

STUDENT PROFILE:
- Target Domain: {target_career}
- Experience Level: {user_level}
- Career Goal: {career_goal}
- Study Commitment: {hours_per_day} hour(s)/day
- Known Verified Skills: {', '.join(known_skills) if known_skills else 'None (Starting from scratch)'}
- Weakness Areas / Specific Gaps: {', '.join(weak_areas) if weak_areas else 'None'}
- Special Requirement / Focus Request: {domain_requirement or 'Standard industry competence'}

{level_req_clause}

CRITICAL RULES:
1. 100% DOMAIN-SPECIFIC: Every phase title and skill list MUST reflect the actual technologies, tools, and methodologies of '{target_career}'.
2. FLEXIBILITY: Levels should be appropriately sized. If starting from scratch, begin with foundational concepts of {target_career}. If intermediate, bridge gaps and advance quickly.
3. CONCRETE SKILLS: List 3-5 real-world skills, libraries, or tools per level (e.g. Docker, PyTorch, React, Terraform, etc.).
4. CLEAR MILESTONES: Give each level an inspiring, practical milestone name.
"""
        try:
            res = await self.provider.generate_structured(
                prompt=prompt,
                output_schema=AIRoadmapStructure,
                system_instruction="You are a Principal Curriculum Architect creating flexible, domain-tailored learning roadmaps powered by Groq AI."
            )
            if res and res.phases and len(res.phases) >= 2:
                for i, p in enumerate(res.phases, start=1):
                    p.phase_number = i
                return res
        except Exception as e:
            logger.warning(f"Groq AI domain roadmap structure call fallback ({e})")

        return self._fallback_domain_structure(
            target_career=target_career,
            user_level=user_level,
            target_phases_count=target_phases_count,
            track_pace=track_pace,
            career_goal=career_goal,
            known_skills=known_skills,
            weak_areas=weak_areas
        )

    def _validate_and_sanitize_phase_content(
        self,
        content: AIRoadmapPhaseContent,
        target_career: str,
        is_beginner: bool,
        hours_per_day: int
    ) -> AIRoadmapPhaseContent:
        """Validates AI response, sanitizes tasks, ensures non-empty actionable fields and clamped durations."""
        if not content.tasks or len(content.tasks) < 2:
            raise ValueError("AI returned insufficient tasks (< 2) for phase")

        sanitized_tasks: List[AIRoadmapTaskContent] = []
        for t in content.tasks:
            # 1. Clamp estimated minutes realistically to user budget (15-180)
            mins = t.estimated_minutes or 45
            if mins < 15:
                mins = 20
            elif mins > 180:
                mins = min(120, max(45, hours_per_day * 60))
            t.estimated_minutes = mins

            # 2. Avoid vague titles
            title = (t.title or "").strip()
            if not title or len(title) < 5 or title.lower() in ["learn python", "study ml", "task"]:
                title = f"{target_career} Applied Practice: {title or 'Core Skills'}"
            t.title = title

            # 3. Ensure topics_to_learn is non-empty
            if not t.topics_to_learn:
                t.topics_to_learn = [
                    f"Core syntax and semantics for {t.title}",
                    "Implementation patterns and best practices",
                    "Debugging, edge cases, and unit validation"
                ]

            # 4. Ensure expected_outcome is actionable
            if not t.expected_outcome or len(t.expected_outcome.strip()) < 5:
                t.expected_outcome = t.practice_goal or f"Working implementation demonstrating mastery of {t.title} without errors."

            # 5. Ensure verification_method is actionable
            if not t.verification_method or len(t.verification_method.strip()) < 5:
                t.verification_method = "Execute implementation locally and verify functional correctness against test cases."

            # 6. Sanitize resources to avoid fabricated URLs
            clean_resources = []
            for r in (t.recommended_resources or []):
                r_clean = r.strip()
                if r_clean.startswith("http://") or r_clean.startswith("https://"):
                    # Only keep trusted doc domains or convert to name
                    if "mdn" in r_clean.lower():
                        clean_resources.append("MDN Web Docs")
                    elif "python.org" in r_clean.lower():
                        clean_resources.append("Official Python Documentation")
                    elif "react.dev" in r_clean.lower():
                        clean_resources.append("React Official Documentation")
                    else:
                        clean_resources.append(r_clean.split("/")[2] if "/" in r_clean[8:] else r_clean)
                elif r_clean:
                    clean_resources.append(r_clean)
            t.recommended_resources = clean_resources or [f"Official {target_career} Documentation"]

            # 7. Ensure concept_explanation & next_step are populated
            if not getattr(t, "concept_explanation", "") or len(t.concept_explanation.strip()) < 5:
                t.concept_explanation = f"{t.title} provides the core patterns and mental models required for {target_career} development."
            if not getattr(t, "next_step", "") or len(t.next_step.strip()) < 5:
                t.next_step = "Complete the practice exercise and proceed to the next module."
            if not getattr(t, "prerequisites", None):
                t.prerequisites = ["None - Starts from Scratch"] if is_beginner else ["Core fundamentals"]

            sanitized_tasks.append(t)

        content.tasks = sanitized_tasks
        return content

    def _build_adaptive_fallback_tasks(
        self,
        phase_number: int,
        phase_type: str,
        target_career: str,
        phase_skills: List[str],
        is_beginner: bool,
        hours_per_day: int,
        career_goal: str
    ) -> List[AIRoadmapTaskContent]:
        """Generates domain-aware and phase-type-aware fallback learning tasks with teacher guidance."""
        p_lower = (phase_type or "").lower()
        skills_lower = [s.lower() for s in phase_skills]
        target_lower = (target_career or "").lower()
        mins = min(60, max(30, hours_per_day * 40))
        diff = "Scratch" if is_beginner and phase_number == 1 else ("Beginner" if is_beginner else "Intermediate")

        # 1. GenAI / Prompt Engineering / RAG / AI Agents
        if any(k in p_lower or any(k in s for s in skills_lower) for k in ["prompt engineering", "llm", "rag", "vector", "agent", "retrieval", "langgraph"]):
            if any("agent" in s or "langgraph" in s or "multi-agent" in s for s in skills_lower):
                return [
                    AIRoadmapTaskContent(
                        title="Autonomous Agent Architecture: State, Memory & ReAct Loops",
                        description="Understand the anatomy of an AI Agent: decision cycles, state graphs, working memory, and tool invocation.",
                        estimated_minutes=mins,
                        task_type="Learn",
                        why_it_matters=f"Autonomous agents are the core engine for modern {target_career} agentic workflows.",
                        topics_to_learn=[
                            "ReAct (Reason + Act) prompting loops",
                            "Stateful conversation memory & scratchpads",
                            "Defining agent stopping conditions & cycle limits",
                            "Handling observation feedback from tools"
                        ],
                        learning_focus="Focus on preventing infinite loops by implementing explicit iteration bounds and error checkpoints.",
                        practice_goal="Implement a basic Python class running a 3-turn ReAct reasoning loop that inspects an input and decides whether to invoke a helper function.",
                        expected_outcome="Working Python agent loop that parses thoughts, issues actions, and synthesizes a final answer.",
                        verification_method="Run test cases with deterministic simulated tool responses and assert loop terminates with correct output.",
                        recommended_resources=["LangChain & LangGraph Conceptual Docs", "ReAct Research Paper & Implementation Guide"],
                        difficulty_level=diff,
                        prerequisites=["Function Calling & REST APIs"],
                        concept_explanation="An AI Agent is a model prompted in a loop: it Reasons about the current state, selects an Action (tool), observes the Result, and decides if the goal is achieved.",
                        next_step="Move to building multi-tool agents and coordinating multi-agent workflows."
                    ),
                    AIRoadmapTaskContent(
                        title="Multi-Tool Integration & Dynamic Function Calling",
                        description="Equip your AI Agent with external calculators, web search APIs, and database lookup tools.",
                        estimated_minutes=mins,
                        task_type="Practice",
                        why_it_matters=f"Real-world {target_career} tasks require interacting with production databases, APIs, and external services.",
                        topics_to_learn=[
                            "JSON schema tool definitions (name, description, parameters)",
                            "Dynamic tool dispatcher pattern",
                            "Validating tool arguments with Pydantic",
                            "Graceful handling of tool execution errors and retries"
                        ],
                        learning_focus="Ensure tool descriptions are unambiguous so the model reliably picks the correct tool.",
                        practice_goal="Define 2 tools (a mock database lookup and a unit calculator) and build an agent that invokes them based on natural language queries.",
                        expected_outcome="Working tool-calling pipeline correctly executing local functions and passing outputs back to LLM.",
                        verification_method="Verify agent executes correct tool and produces combined synthesized answer.",
                        recommended_resources=["OpenAI Tool Calling Guide", "Anthropic Tool Use Documentation"],
                        difficulty_level=diff,
                        prerequisites=["Autonomous Agent Architecture"],
                        concept_explanation="Tool calling lets the LLM output a structured JSON command (e.g. {'tool': 'lookup_user', 'id': 42}) instead of guessing facts, grounding outputs in reality.",
                        next_step="Advance to multi-agent collaboration with LangGraph or CrewAI."
                    ),
                    AIRoadmapTaskContent(
                        title="Multi-Agent Orchestration & Human-in-the-Loop Validation",
                        description="Coordinate specialized agents (e.g. Researcher, Coder, Critic) with approval gates for safety.",
                        estimated_minutes=mins,
                        task_type="Project",
                        why_it_matters=f"Enterprise {target_career} solutions split complex tasks across collaborating agents with human oversight.",
                        topics_to_learn=[
                            "Hierarchical supervisor vs peer-to-peer agent patterns",
                            "Shared state management across agent handoffs",
                            "Human-in-the-loop interruption and approval triggers",
                            "Evaluating multi-agent latency and token costs"
                        ],
                        learning_focus="Focus on clean state passing between agents so context isn't lost during handoffs.",
                        practice_goal="Build a 2-agent system where Agent A drafts a summary and Agent B reviews it for accuracy, pausing for user approval before final submission.",
                        expected_outcome="Functional multi-agent workflow with state persistence and human approval interrupt.",
                        verification_method="Trigger workflow and verify approval gate halts execution until confirmed.",
                        recommended_resources=["LangGraph Architecture Tutorials", "Multi-Agent System Design Patterns"],
                        difficulty_level=diff,
                        prerequisites=["Multi-Tool Integration"],
                        concept_explanation="Multi-agent architectures assign distinct personas and tools to separate agents, avoiding prompt bloat and improving accuracy through peer critique.",
                        next_step="Take the Level Advancement Test to verify your Agentic AI mastery."
                    )
                ]
            elif any("rag" in s or "vector" in s or "embedding" in s for s in skills_lower):
                return [
                    AIRoadmapTaskContent(
                        title="Embeddings, Chunking & Vector Search Fundamentals",
                        description="Master text vectorization, semantic similarity metrics, and document chunking strategies.",
                        estimated_minutes=mins,
                        task_type="Learn",
                        why_it_matters=f"Vector search powers modern contextual retrieval and RAG for {target_career}.",
                        topics_to_learn=[
                            "Cosine similarity, Euclidean distance, and dot product",
                            "Generating dense vector embeddings with embedding models",
                            "Chunking tradeoffs: fixed-size vs recursive character vs semantic",
                            "Chunk overlap to preserve boundary context"
                        ],
                        learning_focus="Focus on chunk size: small chunks improve precision; large chunks provide broad context.",
                        practice_goal="Write a script that chunks a 5-page document, computes embeddings, and finds the top-3 most similar chunks to a user query.",
                        expected_outcome="Working semantic search script returning relevant document excerpts with similarity scores.",
                        verification_method="Verify that semantic queries match relevant passages even with zero shared keywords.",
                        recommended_resources=["Chroma DB Getting Started", "Sentence-Transformers Official Docs"],
                        difficulty_level=diff,
                        prerequisites=["Python Basics & Environment Setup"],
                        concept_explanation="Embeddings convert words into numerical coordinates where texts with similar meanings cluster close together in geometric space.",
                        next_step="Advance to vector database indexing and metadata filtering."
                    ),
                    AIRoadmapTaskContent(
                        title="Vector Database Indexing & Hybrid Search with Chroma/FAISS",
                        description="Store, index, and query embeddings efficiently with metadata filtering in vector databases.",
                        estimated_minutes=mins,
                        task_type="Practice",
                        why_it_matters=f"Production {target_career} systems require fast vector retrieval across thousands of documents.",
                        topics_to_learn=[
                            "In-memory vs persistent vector storage (Chroma / FAISS)",
                            "Metadata tagging (source, author, date) and metadata filtering",
                            "Hybrid search: combining BM25 keyword search with dense vector search",
                            "HNSW (Hierarchical Navigable Small World) indexing intuition"
                        ],
                        learning_focus="Use metadata filters to prune searches before vector comparison for speed and security.",
                        practice_goal="Create a persistent Chroma collection, insert 20 documents with category metadata, and execute a filtered vector query.",
                        expected_outcome="Configured vector store returning filtered semantic search results in <50ms.",
                        verification_method="Execute query with category filter and verify only matching categories are returned.",
                        recommended_resources=["Chroma Documentation", "Vector DB Benchmark Comparison"],
                        difficulty_level=diff,
                        prerequisites=["Embeddings & Chunking Fundamentals"],
                        concept_explanation="A Vector Database is optimized for high-dimensional nearest-neighbor search, letting you retrieve relevant data from millions of records in milliseconds.",
                        next_step="Connect your vector database to an LLM for full RAG generation."
                    ),
                    AIRoadmapTaskContent(
                        title="End-to-End RAG Pipeline & Hallucination Guardrails",
                        description="Assemble complete document retrieval, prompt augmentation, citation generation, and RAG evaluation.",
                        estimated_minutes=mins,
                        task_type="Project",
                        why_it_matters=f"RAG is the primary technique for giving LLMs private enterprise knowledge in {target_career}.",
                        topics_to_learn=[
                            "Retrieval augmentation prompt templates with strict citation constraints",
                            "Reranking retrieved passages (Cross-Encoders/Cohere Rerank)",
                            "Hallucination mitigation: answering 'I do not have enough information' when facts are absent",
                            "RAG evaluation metrics: Faithfulness, Answer Relevance, and Context Recall (RAGAS)"
                        ],
                        learning_focus="Instruct the LLM to only answer based on provided context and cite specific chunk IDs.",
                        practice_goal="Build an interactive Q&A assistant over a technical manual that answers queries with citations and admits when information is missing.",
                        expected_outcome="Working RAG CLI or web service giving verified grounded answers with citations.",
                        verification_method="Ask questions both present in and absent from documents to verify grounding and admission of unknown facts.",
                        recommended_resources=["RAG Evaluation with RAGAS Guide", "LangChain RAG Architecture Tutorial"],
                        difficulty_level=diff,
                        prerequisites=["Vector Database Indexing"],
                        concept_explanation="RAG fetches relevant documents for a user question and injects them into the LLM's prompt as reference context, eliminating hallucinations.",
                        next_step="Take the Level Advancement Test to unlock Autonomous Agent engineering."
                    )
                ]
            else:
                return [
                    AIRoadmapTaskContent(
                        title="Prompt Engineering Foundations: Few-Shot & Chain-of-Thought",
                        description="Master prompt structure, system personas, few-shot demonstrations, and step-by-step reasoning.",
                        estimated_minutes=mins,
                        task_type="Learn",
                        why_it_matters=f"Precise prompting is the foundational interface for all {target_career} applications.",
                        topics_to_learn=[
                            "System vs User vs Assistant message roles",
                            "Few-Shot in-context learning with diverse examples",
                            "Chain-of-Thought (CoT) prompting for multi-step reasoning",
                            "Controlling temperature, top_p, and stop tokens"
                        ],
                        learning_focus="Focus on few-shot formatting: consistent input-output formatting dramatically improves model reliability.",
                        practice_goal="Write a prompt template that classifies customer feedback into sentiment and urgency with 3 few-shot examples and CoT justification.",
                        expected_outcome="Working prompt pipeline producing accurate, consistent classifications across 10 test scenarios.",
                        verification_method="Run test inputs through the prompt and verify 100% adherence to classification categories.",
                        recommended_resources=["OpenAI Prompt Engineering Guide", "Anthropic Interactive Prompt Tutorial"],
                        difficulty_level=diff,
                        prerequisites=["Python Basics & Environment Setup"],
                        concept_explanation="Prompt engineering is giving clear instructions, constraints, and examples to guide an LLM to produce reliable, high-quality answers.",
                        next_step="Learn how to force LLMs to output strict structured JSON schemas."
                    ),
                    AIRoadmapTaskContent(
                        title="Structured Outputs: Enforcing JSON Schemas with Pydantic",
                        description="Guarantee deterministic, valid JSON outputs from LLMs for downstream backend consumption.",
                        estimated_minutes=mins,
                        task_type="Practice",
                        why_it_matters=f"Production {target_career} software requires structured data, not unpredictable free-form text.",
                        topics_to_learn=[
                            "JSON Schema specification for LLM generation",
                            "Validating LLM responses with Pydantic BaseModel",
                            "Handling schema validation errors and bounded self-repair retries",
                            "Pydantic Field descriptions as prompt hints"
                        ],
                        learning_focus="Use descriptive Pydantic Field descriptions; LLMs read them as instructions on how to populate fields.",
                        practice_goal="Create a Pydantic model for extracting resume work history (company, role, dates, achievements) and parse messy text into structured objects.",
                        expected_outcome="Python script reliably converting unformatted raw text into validated Pydantic model instances.",
                        verification_method="Assert parsed output is a valid Pydantic instance without missing fields.",
                        recommended_resources=["Pydantic V2 Documentation", "Structured Outputs API Documentation"],
                        difficulty_level=diff,
                        prerequisites=["Prompt Engineering Foundations"],
                        concept_explanation="Structured outputs constrain the LLM's token generation to follow an exact JSON schema so your code never crashes on malformed data.",
                        next_step="Advance to vector embeddings and semantic search."
                    ),
                    AIRoadmapTaskContent(
                        title="LLM API Client Engineering & Resilient Error Handling",
                        description="Build a production-grade LLM client with exponential backoff, rate limit handling, and token tracking.",
                        estimated_minutes=mins,
                        task_type="Practice",
                        why_it_matters=f"Production applications must handle provider rate limits, timeouts, and outages gracefully.",
                        topics_to_learn=[
                            "Async LLM client calls and concurrent batching",
                            "Exponential backoff with jitter for HTTP 429 rate limits",
                            "Token usage tracking and cost calculation per request",
                            "Provider fallback patterns (e.g. primary to secondary provider)"
                        ],
                        learning_focus="Always implement request timeouts and exponential backoff to avoid hanging applications.",
                        practice_goal="Implement an async wrapper function that retries transient LLM errors up to 3 times with exponential backoff.",
                        expected_outcome="Robust async function handling timeouts and rate limits cleanly without crashing.",
                        verification_method="Simulate network failures and verify retry behavior logs warnings and completes successfully.",
                        recommended_resources=["Tenacity Python Retry Library Docs", "Building Resilient AI Systems Guide"],
                        difficulty_level=diff,
                        prerequisites=["Structured Outputs"],
                        concept_explanation="A resilient AI client wraps raw API calls with retries, timeouts, and fallback logic so your users never see raw provider errors.",
                        next_step="Take the Level Advancement Test to unlock Vector Search & RAG."
                    )
                ]

        # 2. AI Security & Cybersecurity
        if any(k in p_lower or any(k in s for s in skills_lower) for k in ["security", "injection", "jailbreak", "poisoning", "red team", "threat", "audit"]):
            return [
                AIRoadmapTaskContent(
                    title="AI Threat Modeling & OWASP Top 10 for LLMs",
                    description="Understand attack surfaces, STRIDE for AI, and the critical security vulnerabilities specific to LLMs.",
                    estimated_minutes=mins,
                    task_type="Learn",
                    why_it_matters=f"Security analysis for {target_career} requires identifying threats before deploying AI models.",
                    topics_to_learn=[
                        "OWASP Top 10 for LLM Applications (LLM01-LLM10)",
                        "Direct vs Indirect prompt injection vectors",
                        "Data poisoning and training data exfiltration",
                        "Insecure output handling and remote code execution risks"
                    ],
                    learning_focus="Focus on Indirect Prompt Injection: untrusted data (emails, web pages) can hijack model execution.",
                    practice_goal="Analyze an AI customer support bot architecture and write a threat model document identifying 3 critical vulnerabilities.",
                    expected_outcome="Structured threat model identifying attack vectors, impact, and mitigation strategies.",
                    verification_method="Review threat model against OWASP Top 10 criteria for completeness.",
                    recommended_resources=["OWASP Top 10 for LLM Applications", "NIST AI Risk Management Framework"],
                    difficulty_level=diff,
                    prerequisites=["Cybersecurity Fundamentals & Python"],
                    concept_explanation="AI threat modeling maps out how attackers can manipulate model inputs, corrupt training data, or exploit tool-calling privileges.",
                    next_step="Practice hands-on prompt injection and defense hardening."
                ),
                AIRoadmapTaskContent(
                    title="Prompt Injection Exploitation & Defensive Hardening",
                    description="Demonstrate prompt injection attacks and build dual-LLM defense & input sanitization boundaries.",
                    estimated_minutes=mins,
                    task_type="Practice",
                    why_it_matters=f"Prompt injection is the #1 vulnerability in AI applications. Defense is a core {target_career} competency.",
                    topics_to_learn=[
                        "Delimiter isolation and XML tag framing",
                        "Input classification: detecting adversarial instructions before LLM execution",
                        "Dual-LLM pattern: separating untrusted data processing from privileged actions",
                        "Sanitizing outputs to prevent Cross-Site Scripting (XSS) and SSRF"
                    ],
                    learning_focus="Never trust system prompt instructions alone to stop injection; use architectural guardrails.",
                    practice_goal="Build a defense middleware that scans incoming prompts for injection patterns and sanitizes inputs before passing to target model.",
                    expected_outcome="Python security filter blocking common jailbreak and injection payloads while allowing normal queries.",
                    verification_method="Test filter with a suite of 10 known injection payloads and verify 90%+ catch rate.",
                    recommended_resources=["Simon Willison Prompt Injection Reference", "LLM Guard Security Toolkit"],
                    difficulty_level=diff,
                    prerequisites=["AI Threat Modeling"],
                    concept_explanation="Prompt injection occurs when user input tricks the LLM into ignoring its original instructions. Defensive hardening isolates instructions from data.",
                    next_step="Advance to data privacy, model extraction, and red-teaming harnesses."
                ),
                AIRoadmapTaskContent(
                    title="Automated AI Red Teaming & Guardrail Enforcement",
                    description="Implement automated adversarial testing using NeMo Guardrails or Garak and establish security benchmarks.",
                    estimated_minutes=mins,
                    task_type="Project",
                    why_it_matters=f"Continuous security testing ensures models do not regress or leak sensitive information.",
                    topics_to_learn=[
                        "Automated red-teaming scanners (Garak / PyRIT)",
                        "Implementing input/output rail policies with NeMo Guardrails",
                        "PII detection, masking, and differential privacy principles",
                        "Logging security incidents and establishing audit trails"
                    ],
                    learning_focus="Focus on output rails: inspect model responses before returning them to users to block secret leaks.",
                    practice_goal="Set up an automated test harness that runs 20 adversarial probes against an API endpoint and generates a vulnerability report.",
                    expected_outcome="Executable red-teaming report detailing passed/failed security probes and policy violations.",
                    verification_method="Run test harness and verify all policy violations are caught and logged.",
                    recommended_resources=["NeMo Guardrails Documentation", "Garak LLM Vulnerability Scanner Docs"],
                    difficulty_level=diff,
                    prerequisites=["Prompt Injection Defense"],
                    concept_explanation="Red teaming actively attacks your own AI system to discover security weaknesses before real attackers can find them.",
                    next_step="Take the Level Advancement Test to verify your AI Security competence."
                )
            ]

        # 3. Data Wrangling & Analysis
        if any(k in p_lower or any(k in s for s in skills_lower) for k in ["wrangling", "pandas", "sql", "analysis", "eda", "cleaning"]):
            return [
                AIRoadmapTaskContent(
                    title="Data Ingestion, Inspection & Cleaning with Pandas",
                    description="Load raw CSV/JSON datasets, handle missing values, correct data types, and remove anomalies.",
                    estimated_minutes=mins,
                    task_type="Practice",
                    why_it_matters=f"80% of data science in {target_career} is cleaning and preparing raw real-world data.",
                    topics_to_learn=[
                        "Loading datasets with read_csv, read_json, and memory optimization",
                        "Identifying missing data (isna, null values) and imputation strategies",
                        "Data type casting, datetime parsing, and categorical encoding",
                        "Filtering duplicates and identifying statistical outliers"
                    ],
                    learning_focus="Check data distributions before imputing missing values (mean vs median).",
                    practice_goal="Clean a messy real-world dataset (e.g. housing or sales data) containing missing values, incorrect formats, and duplicates.",
                    expected_outcome="Cleaned Pandas DataFrame saved to CSV with zero missing values and correct column types.",
                    verification_method="Verify df.info() shows 0 nulls and correct datatypes across all columns.",
                    recommended_resources=["Pandas Official Getting Started", "Data Cleaning Best Practices Guide"],
                    difficulty_level=diff,
                    prerequisites=["Python Foundations"],
                    concept_explanation="Data cleaning transforms raw, messy data into structured, accurate formats ready for statistical analysis and machine learning.",
                    next_step="Learn analytical SQL queries and aggregations."
                ),
                AIRoadmapTaskContent(
                    title="Analytical SQL & Grouped Aggregations for Insights",
                    description="Query relational tables with joins, group by aggregations, window functions, and subqueries.",
                    estimated_minutes=mins,
                    task_type="Practice",
                    why_it_matters=f"SQL is the universal language for extracting business and engineering datasets in {target_career}.",
                    topics_to_learn=[
                        "SELECT, WHERE, ORDER BY, and LIMIT filtering",
                        "INNER, LEFT, and FULL OUTER joins across related tables",
                        "GROUP BY and HAVING aggregate calculations (COUNT, SUM, AVG)",
                        "Basic window functions (ROW_NUMBER, RANK) for ranking"
                    ],
                    learning_focus="Understand join keys: ensure foreign keys match primary keys to prevent duplicate rows.",
                    practice_goal="Write 5 SQL queries answering business questions (e.g. top revenue customers, monthly active users) on a SQLite database.",
                    expected_outcome="SQL script executing queries and returning correct analytical summary tables.",
                    verification_method="Verify query results match expected statistical counts.",
                    recommended_resources=["Mode Analytics SQL Tutorial", "SQLBolt Interactive Lessons"],
                    difficulty_level=diff,
                    prerequisites=["Data Ingestion with Pandas"],
                    concept_explanation="SQL lets you ask questions of relational databases to filter, combine, and summarize millions of records quickly.",
                    next_step="Advance to Exploratory Data Analysis and data visualization."
                ),
                AIRoadmapTaskContent(
                    title="Exploratory Data Analysis (EDA) & Feature Insights",
                    description="Uncover patterns, correlations, and feature distributions using statistical summaries and visualization.",
                    estimated_minutes=mins,
                    task_type="Project",
                    why_it_matters=f"EDA reveals which features will be predictive for machine learning models.",
                    topics_to_learn=[
                        "Correlation matrices and multicollinearity analysis",
                        "Distribution plots (histograms, box plots, KDE) with Seaborn/Matplotlib",
                        "Categorical vs target variable relationships",
                        "Synthesizing key insights into a clear narrative"
                    ],
                    learning_focus="Look for skewed distributions and outliers that could distort machine learning models.",
                    practice_goal="Create a Jupyter notebook performing an end-to-end EDA on a public dataset with 5 visual plots and written insights.",
                    expected_outcome="Complete EDA Jupyter Notebook with annotated plots and feature summary.",
                    verification_method="Run all cells top-to-bottom without errors and review plot clarity.",
                    recommended_resources=["Seaborn Data Visualization Tutorial", "EDA Case Studies on Kaggle"],
                    difficulty_level=diff,
                    prerequisites=["Analytical SQL"],
                    concept_explanation="EDA is detective work: you explore data visually and statistically to understand what story it tells before building models.",
                    next_step="Take the Level Advancement Test to unlock Classical Machine Learning."
                )
            ]

        # 4. Classical Machine Learning
        if any(k in p_lower or any(k in s for s in skills_lower) for k in ["machine learning", "scikit", "classical", "modeling", "supervised", "unsupervised"]):
            return [
                AIRoadmapTaskContent(
                    title="Supervised Learning: Regression & Classification with Scikit-Learn",
                    description="Train linear models, decision trees, and random forests using Scikit-Learn.",
                    estimated_minutes=mins,
                    task_type="Learn",
                    why_it_matters=f"Supervised algorithms form the core modeling toolkit for {target_career}.",
                    topics_to_learn=[
                        "Train/test splitting to prevent data leakage",
                        "Feature scaling (StandardScaler, MinMaxScaler)",
                        "Linear & Logistic Regression intuition and training",
                        "Tree-based models (Decision Trees, Random Forests)"
                    ],
                    learning_focus="Fit scalers ONLY on training data, then transform both train and test to prevent data leakage.",
                    practice_goal="Train a Random Forest classifier on a tabular dataset and evaluate accuracy on a held-out test set.",
                    expected_outcome="Trained model pipeline achieving >80% accuracy on held-out test data.",
                    verification_method="Evaluate test set performance and compare against baseline naive predictor.",
                    recommended_resources=["Scikit-Learn Official User Guide", "Hands-on ML with Scikit-Learn & PyTorch Book"],
                    difficulty_level=diff,
                    prerequisites=["Exploratory Data Analysis with Pandas"],
                    concept_explanation="Supervised learning trains a mathematical model on historical examples with known answers so it can predict outcomes on new, unseen data.",
                    next_step="Learn model validation, hyperparameter tuning, and cross-validation."
                ),
                AIRoadmapTaskContent(
                    title="Model Validation, Hyperparameter Tuning & Cross-Validation",
                    description="Prevent overfitting and optimize model hyperparameters using K-Fold cross-validation.",
                    estimated_minutes=mins,
                    task_type="Practice",
                    why_it_matters=f"Ensures models generalize reliably to real-world production data in {target_career}.",
                    topics_to_learn=[
                        "K-Fold Cross-Validation vs simple holdout validation",
                        "GridSearchCV and RandomizedSearchCV for hyperparameter tuning",
                        "Diagnosing bias vs variance (underfitting vs overfitting)",
                        "Evaluation metrics: Precision, Recall, F1-Score, and ROC-AUC"
                    ],
                    learning_focus="Choose F1-Score or ROC-AUC over simple accuracy when dealing with imbalanced datasets.",
                    practice_goal="Optimize hyperparameters of a classifier using 5-fold cross-validation and generate a classification report.",
                    expected_outcome="Optimized model parameters with cross-validation scores and confusion matrix visualization.",
                    verification_method="Verify model achieves higher cross-validation score than default baseline.",
                    recommended_resources=["Scikit-Learn Model Evaluation Guide", "Cross-Validation Demystified"],
                    difficulty_level=diff,
                    prerequisites=["Supervised Learning with Scikit-Learn"],
                    concept_explanation="Cross-validation tests your model on multiple different partitions of data so you know it didn't just get lucky on one split.",
                    next_step="Learn model deployment and evaluation in production."
                ),
                AIRoadmapTaskContent(
                    title="Model Evaluation, Benchmarking & Production Packaging",
                    description="Export trained models, build an inference function, and benchmark predictions.",
                    estimated_minutes=mins,
                    task_type="Project",
                    why_it_matters=f"Models must be packaged and tested so engineering teams can deploy them.",
                    topics_to_learn=[
                        "Exporting model artifacts with joblib or pickle",
                        "Building an end-to-end inference pipeline function with input validation",
                        "Evaluating inference latency (milliseconds per prediction)",
                        "Documenting model assumptions and failure modes"
                    ],
                    learning_focus="Bundle feature preprocessing into a single Scikit-Learn Pipeline object for atomic deployment.",
                    practice_goal="Package a trained pipeline into a reusable Python module that accepts new JSON records and returns predictions.",
                    expected_outcome="Serialized pipeline (.joblib) with an inference test script running predictions.",
                    verification_method="Load exported pipeline in a separate script and verify predictions match test assertions.",
                    recommended_resources=["Scikit-Learn Pipeline Documentation", "ML Model Packaging Guide"],
                    difficulty_level=diff,
                    prerequisites=["Model Validation & Hyperparameter Tuning"],
                    concept_explanation="Packaging turns an experimental notebook model into clean, deployable software that can take new requests and return predictions.",
                    next_step="Take the Level Advancement Test to unlock Deep Learning & Neural Networks."
                )
            ]

        # 5. Default Universal Adaptive Fallback
        skill_0 = phase_skills[0] if phase_skills else target_career
        return [
            AIRoadmapTaskContent(
                title=f"{skill_0}: Core Mental Model & Foundations",
                description=f"Understand the fundamental architecture, key terminology, and mental models of {skill_0}.",
                estimated_minutes=mins,
                task_type="Learn",
                why_it_matters=f"Builds the necessary bedrock for all subsequent {target_career} topics.",
                topics_to_learn=[
                    f"Core principles and purpose of {skill_0}",
                    "Essential terminology and conceptual architecture",
                    "Development environment and tooling setup",
                    "Common conventions and best practices"
                ],
                learning_focus="Focus on understanding WHY this tool/skill exists and what problem it solves.",
                practice_goal=f"Complete a guided setup and run a verification script demonstrating {skill_0} fundamentals.",
                expected_outcome=f"Working standalone demonstration of {skill_0} executing cleanly without errors.",
                verification_method="Run verification checks locally and inspect results against expected output.",
                recommended_resources=[f"Official {skill_0} Documentation", f"{skill_0} Getting Started Guide"],
                difficulty_level=diff,
                prerequisites=["None - Starts from Scratch"] if is_beginner else ["General logic foundations"],
                concept_explanation=f"{skill_0} provides the essential building blocks used by industry professionals in {target_career}.",
                next_step="Practice applying these core concepts in hands-on workflows."
            ),
            AIRoadmapTaskContent(
                title=f"{skill_0}: Hands-On Implementation & Practical Workflows",
                description=f"Apply {skill_0} to solve concrete challenges and build modular components.",
                estimated_minutes=mins,
                task_type="Practice",
                why_it_matters=f"Direct hands-on fluency in {skill_0} is required for {target_career} technical roles.",
                topics_to_learn=[
                    "Core workflow execution and implementation patterns",
                    "Input validation, edge case handling, and error recovery",
                    "Modular structure and clean code practices",
                    "Testing and validating functional correctness"
                ],
                learning_focus="Break implementation into small testable units rather than writing one large block.",
                practice_goal=f"Build a practical exercise implementing core {skill_0} patterns with error handling.",
                expected_outcome=f"Working practical implementation with error handling and test assertions.",
                verification_method="Execute implementation against edge-case test inputs and verify expected behavior.",
                recommended_resources=[f"Practical {skill_0} Guide", "Industry Best Practices Documentation"],
                difficulty_level=diff,
                prerequisites=[f"{skill_0} Mental Model & Foundations"],
                concept_explanation=f"Practicing {skill_0} builds muscle memory, helping you write clean, error-free code naturally.",
                next_step="Integrate this implementation into a portfolio project."
            ),
            AIRoadmapTaskContent(
                title=f"{skill_0}: Integration, Polish & Milestone Verification",
                description=f"Test, optimize, and document your {skill_0} implementation for milestone completion.",
                estimated_minutes=mins,
                task_type="Project",
                why_it_matters=f"Demonstrates end-to-end practical competence required for {target_career} ({career_goal}).",
                topics_to_learn=[
                    "End-to-end workflow validation and integration testing",
                    "Performance profiling and edge-case hardening",
                    "Writing clear documentation and usage notes",
                    "Self-assessment and milestone verification"
                ],
                learning_focus="Verify your work against the phase milestone criteria before proceeding to the level test.",
                practice_goal=f"Assemble your {skill_0} exercises into a cohesive mini-project with documentation.",
                expected_outcome="Documented, fully functional mini-project demonstrating phase mastery.",
                verification_method="Run full validation suite and verify all milestone criteria are met.",
                recommended_resources=[f"Official {skill_0} Best Practices", f"{target_career} Engineering Standards"],
                difficulty_level=diff,
                prerequisites=[f"{skill_0} Hands-On Implementation"],
                concept_explanation=f"Integration proves you can connect individual {skill_0} concepts into a working, reliable system.",
                next_step="Take the Level Advancement Test to verify your mastery and unlock the next level."
            )
        ]

    async def generate_phase_content(
        self,
        phase_number: int,
        phase_type: str,
        target_career: str,
        phase_skills: List[str],
        user_known_skills: List[str],
        user_level: str = "Beginner",
        learning_style: str = "Hands-on",
        hours_per_day: int = 1,
        career_goal: str = "Entry-level Job",
        weak_areas: Optional[List[str]] = None
    ) -> AIRoadmapPhaseContent:
        """Generates structured learning syllabus, objectives, topic checklist, and project for a roadmap phase."""
        is_beginner = user_level.lower() in ["beginner", "scratch"] or len(user_known_skills) == 0

        scratch_guidance = (
            "THE USER IS A COMPLETE BEGINNER (OR STARTS FROM SCRATCH). "
            "Assume ZERO prior programming or technical knowledge. Explain WHAT to learn in simple, accessible, "
            "step-by-step topics. Lay down foundational syntax and mental models clearly."
            if is_beginner else
            f"The user has experience level '{user_level}'. Build on their verified foundation ({', '.join(user_known_skills[:5]) if user_known_skills else 'general skills'}) and bridge exact gaps without repeating basics."
        )

        goal_guidance = {
            "Internship": "Focus heavily on foundational coding fluency, clean Git commits, core data structures, and practical portfolio projects demonstrating ability to learn and contribute in a team.",
            "Entry-level Job": "Target production-grade conventions, REST/API patterns, unit testing, error handling, and deployable end-to-end full stack/backend projects suitable for junior developer interviews.",
            "Career Transition": "Bridge concepts clearly from general logic to domain frameworks, emphasizing real-world practical applications, tangible portfolio projects, and demystifying industry jargon.",
            "Certification": "Prioritize exam blueprint syllabus topics, architectural concepts, cloud/security standards, and rigorous verification quizzes mirroring official exam objectives.",
            "Skill Mastery": "Dive deep into internal mechanics, performance profiling, concurrency, edge cases, distributed system patterns, and advanced design patterns."
        }.get(career_goal, "Focus on practical industry competence, clear incremental progress, and demonstrable portfolio work.")

        weak_area_clause = f"- Remediate Known Weaknesses / Assessment Gaps: {', '.join(weak_areas[:4])}" if weak_areas else ""

        prompt = f"""
You are an expert Principal Curriculum Architect creating Phase {phase_number} ({phase_type}) of a complete career roadmap for a student aiming to become a '{target_career}'.

Career Goal: {career_goal}
Goal Strategy: {goal_guidance}

{scratch_guidance}

Phase Details:
- Phase Number: {phase_number}
- Phase Type: {phase_type}
- Targeted Skills in this Phase: {', '.join(phase_skills) if phase_skills else 'Core Foundations'}
- User Verified Skills: {', '.join(user_known_skills[:8]) if user_known_skills else 'None (Starting from scratch)'}
- User Level: {user_level}
- Learning Style: {learning_style}
- Daily Study Budget: {hours_per_day} hour(s)/day
{weak_area_clause}

CRITICAL GUIDELINES (STRICT COMPLIANCE REQUIRED):
1. EASY TO FOLLOW & TEACHER-LIKE GUIDANCE: Provide crystal-clear guidance. Structure each task with intuitive step-by-step concepts, concrete practice goals, clear completion outcomes, and teacher notes explaining the core mental model.
2. WHAT TO LEARN & HOW TO PRACTICE: Tell the student EXACTLY what topics to cover and what exercise to build. Break complex subjects into manageable units fitting a {hours_per_day}h/day commitment.
3. CONCRETE ACTIONABLE FIELDS: Every task MUST include:
   - title: Specific action-oriented topic title
   - description: Clear overview of why this topic fits here
   - topics_to_learn: 4-6 ordered subtopics or syntax points
   - learning_focus: Advice on what to prioritize or watch out for
   - practice_goal: One specific hands-on exercise to code or analyze
   - expected_outcome: Concrete deliverable (e.g. working script, test suite)
   - verification_method: Measurable verification criteria
   - recommended_resources: 2-3 standard topics or official docs
   - difficulty_level: Scratch, Beginner, Intermediate, or Advanced
   - prerequisites: 1-2 prerequisite concepts
   - concept_explanation: 2-3 sentences explaining the core mental model or a small concrete code demonstration of this concept like a helpful teacher
   - next_step: 1 sentence clearly explaining what the learner will tackle next once this task is completed
4. DOMAIN RELEVANCE: Ensure all topics directly support '{target_career}'.

Generate:
1. 3-4 clear learning objectives for this phase.
2. A concrete milestone title and verification criteria.
3. 3-4 structured, topic-wise daily tasks matching the specification above.
4. A concrete, portfolio-worthy project recommendation that reinforces the phase skills and boosts resume relevance.
"""
        try:
            raw_content = await self.provider.generate_structured(
                prompt=prompt,
                output_schema=AIRoadmapPhaseContent,
                system_instruction="You are a senior technical curriculum architect creating personalized, zero-difficulty career roadmaps."
            )
            return self._validate_and_sanitize_phase_content(raw_content, target_career, is_beginner, hours_per_day)
        except Exception as e:
            logger.warning(f"Groq/AI roadmap phase content fallback ({e})")
            skills_str = ", ".join(phase_skills[:2]) if phase_skills else "Target Requirements"
            fallback_tasks = self._build_adaptive_fallback_tasks(
                phase_number=phase_number,
                phase_type=phase_type,
                target_career=target_career,
                phase_skills=phase_skills,
                is_beginner=is_beginner,
                hours_per_day=hours_per_day,
                career_goal=career_goal
            )
            return AIRoadmapPhaseContent(
                phase_title=f"Phase {phase_number}: {phase_type} ({skills_str})",
                learning_objectives=[
                    f"Understand the core syntax, mental model, and fundamental principles of {skills_str}.",
                    f"Master the essential subtopics and development patterns of {skills_str}.",
                    f"Build hands-on practical exercises demonstrating practical competence for {target_career} ({career_goal})."
                ],
                milestone_title=f"{skills_str} Practical Competence Milestone",
                milestone_criteria=f"Complete hands-on implementation demonstrating end-to-end understanding of {skills_str} for {target_career}.",
                tasks=fallback_tasks,
                project=AIProjectIdea(
                    title=f"Build {target_career} {skills_str} Practical Mini-Project",
                    objective=f"Develop a complete, functioning application implementing all topics learned in this phase for {skills_str}.",
                    skills_practiced=phase_skills,
                    difficulty="Beginner" if is_beginner else "Intermediate",
                    expected_outcome=f"Working modular project showcasing {skills_str} integration.",
                    resume_relevance=f"Provides tangible proof of {skills_str} proficiency on resume for {target_career} ({career_goal})."
                )
            )

    async def chat_with_roadmap_assistant(
        self,
        user_message: str,
        roadmap_data: dict,
        history: Optional[List[dict]] = None,
        current_phase_id: Optional[str] = None,
        current_task_id: Optional[str] = None
    ) -> str:
        """
        Interacts with user strictly about their learning roadmap using Groq AI.
        Guardrailed so it solely assists with roadmap navigation, concepts, study habits, and learning pacing.
        """
        target_role = roadmap_data.get("target_role", "Software Engineer")
        user_level = roadmap_data.get("user_level", "Beginner")
        progress = roadmap_data.get("overall_progress_percent", 0)
        phases = roadmap_data.get("phases", [])

        phases_summary = []
        current_focus = ""

        for p in phases:
            pid = str(p.get("id") or p.get("phase_id") or "")
            tasks = p.get("tasks", [])
            completed_tasks = [t.get("title", "") for t in tasks if t.get("is_completed") or t.get("completed")]
            pending_tasks = [t.get("title", "") for t in tasks if not (t.get("is_completed") or t.get("completed"))]
            is_active = (pid == current_phase_id)
            status_tag = "Completed" if p.get("test_passed") else ("Active/Current" if is_active else "Upcoming")
            
            p_desc = f"Phase {p.get('phase_number', 1)}: {p.get('title', p.get('name', 'Level'))} [{status_tag}]"
            tasks_desc = f"   - Completed: {', '.join(completed_tasks) if completed_tasks else 'None'}\n   - To Learn: {', '.join(pending_tasks) if pending_tasks else 'None'}"
            phases_summary.append(f"{p_desc}\n{tasks_desc}")

            if is_active or (not current_focus and not p.get("test_passed")):
                current_focus = f"CURRENT FOCUS: Level {p.get('phase_number', 1)} - {p.get('title', p.get('name'))}\nDescription: {p.get('description', '')}\nLearning Objectives: {', '.join(p.get('learning_objectives', []))}"

        system_instruction = f"""You are the official "AI Roadmap Coach" powered by Groq.
Your singular objective is to help the student easily follow, understand, and complete their personalized roadmap for becoming a '{target_role}'.

USER ROADMAP CONTEXT:
- Target Role: {target_role}
- Experience Level: {user_level}
- Overall Roadmap Progress: {progress}% completed
- {current_focus}

FULL ROADMAP STRUCTURE:
{chr(10).join(phases_summary)}

MANDATORY RULES & GUARDRAILS (STRICT COMPLIANCE):
1. SOLE CONVERSATION TOPIC: ROADMAP & LEARNING ONLY.
   - You ONLY discuss this career roadmap, its phases, specific syllabus concepts, daily study plans, hands-on practice, coding doubts, and engineering career advice for {target_role}.
   - IF THE USER ASKS ABOUT UNRELATED TOPICS (e.g. general news, politics, weather, recipes, entertainment, casual banter outside their career), YOU MUST POLITELY AND FIRMLY DECLINE AND STEER THEM BACK TO THE ROADMAP:
     "Main aapka dedicated AI Roadmap Coach hoon! 🎯 Main sirf aapke '{target_role}' roadmap, topics ko samajhne, aur padhai plan karne me madad kar sakta hoon. Kripya apne roadmap ke kisi level, task ya concept ke baare me poochhein!"
2. KEEP IT EXTREMELY EASY, BEGINNER-FRIENDLY & CLEAR:
   - Make all explanations crystal clear, friendly, and easy to follow.
   - Break down intimidating concepts into simple steps with real-world analogies.
   - If the user writes in Hindi or Hinglish, reply in warm, encouraging Hinglish. If in English, reply in clear English.
   - Whenever asked "What should I do next?", give them the exact next pending topic in their roadmap!
3. CONCISE & ACTIONABLE:
   - Use bullet points, bold keywords, and short readable steps.
"""
        messages_payload = []
        if history:
            for m in history[-6:]:
                messages_payload.append({
                    "role": "assistant" if m.get("role") in ["assistant", "ai"] else "user",
                    "content": m.get("content", "")
                })
        messages_payload.append({"role": "user", "content": user_message})

        try:
            if hasattr(self.provider, "generate_chat"):
                reply = await self.provider.generate_chat(
                    messages=messages_payload,
                    system_instruction=system_instruction
                )
            else:
                reply = await self.provider.generate_text(
                    prompt=f"User question: {user_message}",
                    system_instruction=system_instruction
                )
            return reply.strip()
        except Exception as e:
            logger.error(f"Roadmap AI Assistant chat error: {e}")
            # Friendly fallback
            return f"Main aapka Groq AI Roadmap Coach hoon! Aapke '{target_role}' roadmap me abhi aap Level '{current_focus or 'Active Level'}' par hain. Agla step lene ke liye syllabus me diye gaye pehle incomplete topic se shuru karein aur concepts padhkar checkmark par tick karein!"
