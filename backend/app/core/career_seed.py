from typing import List, Dict, Any

SEED_CAREER_ROLES: List[Dict[str, Any]] = [
    {
        "slug": "software-developer",
        "title": "Software Developer",
        "description": "Designs, builds, and maintains reliable software systems and software components with high algorithmic and architectural standards.",
        "difficulty_level": "Intermediate",
        "required_skills": ["Python", "Java", "Data Structures", "OOP", "Git"],
        "important_skills": ["SQL", "REST APIs", "Problem Solving", "Unit Testing"],
        "optional_skills": ["Docker", "Linux", "CI/CD Pipelines"],
        "recommended_proficiency": {
            "Python": "Intermediate",
            "Java": "Intermediate",
            "Data Structures": "Intermediate",
            "OOP": "Intermediate",
            "Git": "Intermediate",
            "SQL": "Intermediate",
            "Problem Solving": "Intermediate"
        },
        "preferred_strengths": ["Problem Solving", "Logical Reasoning", "Systems Thinking"],
        "interest_areas": ["Software Construction", "Algorithms", "Automation"],
        "work_style": "Independent & Collaborative Technical Work",
        "responsibilities": ["Design algorithm logic", "Build scalable features", "Refactor codebase", "Write unit tests"],
        "learning_areas": ["Design Patterns", "System Architecture", "Async Programming"]
    },
    {
        "slug": "frontend-developer",
        "title": "Frontend Developer",
        "description": "Specializes in building responsive, fast, and accessible user interfaces using modern web frameworks and design systems.",
        "difficulty_level": "Entry to Intermediate",
        "required_skills": ["HTML", "CSS", "JavaScript"],
        "important_skills": ["React", "TypeScript", "Git", "Tailwind CSS"],
        "optional_skills": ["Next.js", "Web Performance", "Figma"],
        "recommended_proficiency": {
            "HTML": "Intermediate",
            "CSS": "Intermediate",
            "JavaScript": "Intermediate",
            "React": "Intermediate",
            "TypeScript": "Intermediate",
            "Git": "Beginner"
        },
        "preferred_strengths": ["Visual & UI Instincts", "User Empathy", "Attention to Detail"],
        "interest_areas": ["Web Development", "UI Engineering", "Design Systems"],
        "work_style": "Collaborative with Designers & Product Managers",
        "responsibilities": ["Build interactive web UI", "Integrate REST APIs", "Optimize page load speed", "Ensure cross-browser compatibility"],
        "learning_areas": ["Next.js", "State Management", "Web Performance Optimization"]
    },
    {
        "slug": "backend-developer",
        "title": "Backend Developer",
        "description": "Engineers server-side business logic, database architectures, microservices, and secure RESTful/GraphQL APIs.",
        "difficulty_level": "Intermediate",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "REST APIs"],
        "important_skills": ["Node.js", "Docker", "Git", "SQL"],
        "optional_skills": ["Redis", "Kubernetes", "Microservices"],
        "recommended_proficiency": {
            "Python": "Intermediate",
            "FastAPI": "Intermediate",
            "PostgreSQL": "Intermediate",
            "REST APIs": "Intermediate",
            "Docker": "Beginner"
        },
        "preferred_strengths": ["Logical Reasoning", "Data Modeling", "Systems Architecture"],
        "interest_areas": ["API Architecture", "Database Design", "Performance Scaling"],
        "work_style": "Focused Systems & Data Engineering",
        "responsibilities": ["Build RESTful/GraphQL APIs", "Design DB schemas", "Implement authentication & security", "Optimize DB queries"],
        "learning_areas": ["Distributed Systems", "Message Queues", "Caching Strategies"]
    },
    {
        "slug": "full-stack-developer",
        "title": "Full Stack Developer",
        "description": "Bridging client-side interfaces and server-side infrastructure to deliver end-to-end web applications.",
        "difficulty_level": "Intermediate to Advanced",
        "required_skills": ["TypeScript", "React", "Node.js", "FastAPI", "SQL"],
        "important_skills": ["HTML", "CSS", "Git", "PostgreSQL", "Docker"],
        "optional_skills": ["Next.js", "AWS", "CI/CD Pipelines"],
        "recommended_proficiency": {
            "TypeScript": "Intermediate",
            "React": "Intermediate",
            "Node.js": "Intermediate",
            "FastAPI": "Intermediate",
            "SQL": "Intermediate"
        },
        "preferred_strengths": ["Holistic Problem Solving", "Adaptability", "Systems Architecture"],
        "interest_areas": ["End-to-End Product Building", "Full Stack Web Architecture"],
        "work_style": "Versatile Product & Tech Engineering",
        "responsibilities": ["Implement UI components & server endpoints", "Manage database integration", "Deploy web apps"],
        "learning_areas": ["Serverless Architecture", "DevOps Pipelines", "Microfrontends"]
    },
    {
        "slug": "data-analyst",
        "title": "Data Analyst",
        "description": "Transforms raw operational data into actionable business insights through SQL queries, visualization dashboards, and statistical analysis.",
        "difficulty_level": "Entry to Intermediate",
        "required_skills": ["SQL", "Python", "Tableau", "PowerBI", "Data Visualization"],
        "important_skills": ["Pandas", "Analytical Thinking", "Communication"],
        "optional_skills": ["NumPy", "Excel", "Statistics"],
        "recommended_proficiency": {
            "SQL": "Intermediate",
            "Python": "Beginner",
            "Tableau": "Intermediate",
            "PowerBI": "Intermediate",
            "Data Visualization": "Intermediate"
        },
        "preferred_strengths": ["Analytical Thinking", "Pattern Recognition", "Data Storytelling"],
        "interest_areas": ["Business Intelligence", "Data Analytics", "Statistical Modeling"],
        "work_style": "Data-Driven Business Collaboration",
        "responsibilities": ["Query SQL databases", "Create operational dashboards", "Present data stories to stakeholders", "Conduct trend analysis"],
        "learning_areas": ["Advanced SQL Window Functions", "Statistical Hypothesis Testing", "dbt"]
    },
    {
        "slug": "data-scientist",
        "title": "Data Scientist",
        "description": "Applies statistical algorithms, machine learning models, and predictive analytics to solve complex predictive data problems.",
        "difficulty_level": "Advanced",
        "required_skills": ["Python", "Pandas", "Scikit-Learn", "SQL"],
        "important_skills": ["NumPy", "PyTorch", "Analytical Thinking", "Problem Solving"],
        "optional_skills": ["TensorFlow", "LLMs", "R"],
        "recommended_proficiency": {
            "Python": "Advanced",
            "Pandas": "Advanced",
            "Scikit-Learn": "Intermediate",
            "SQL": "Intermediate"
        },
        "preferred_strengths": ["Mathematical Intuition", "Hypothesis Driven Curiosity", "Analytical Rigor"],
        "interest_areas": ["Predictive Analytics", "Machine Learning", "Applied Statistics"],
        "work_style": "Experimental & Analytical Research",
        "responsibilities": ["Build predictive models", "Clean & feature-engineer complex datasets", "Run A/B test experiments", "Deploy ML models"],
        "learning_areas": ["Deep Learning", "Natural Language Processing", "Model Evaluation & Drift"]
    },
    {
        "slug": "ai-ml-engineer",
        "title": "AI / ML Engineer",
        "description": "Designs, trains, fine-tunes, and deploys scalable Artificial Intelligence and Large Language Models into production applications.",
        "difficulty_level": "Advanced",
        "required_skills": ["Python", "PyTorch", "TensorFlow", "LLMs"],
        "important_skills": ["Vector Databases", "Docker", "FastAPI", "Git"],
        "optional_skills": ["Kubernetes", "AWS", "C++"],
        "recommended_proficiency": {
            "Python": "Advanced",
            "PyTorch": "Intermediate",
            "TensorFlow": "Intermediate",
            "LLMs": "Intermediate"
        },
        "preferred_strengths": ["Algorithmic Reasoning", "Pioneering Tech Curiosity", "Complex Problem Solving"],
        "interest_areas": ["Generative AI", "Deep Learning Architectures", "AI Automation"],
        "work_style": "Research-to-Production Engineering",
        "responsibilities": ["Fine-tune LLMs", "Build RAG vector search pipelines", "Deploy ML inference endpoints", "Optimize GPU latency"],
        "learning_areas": ["Agentic Architectures", "Model Distillation", "CUDA Optimization"]
    },
    {
        "slug": "cybersecurity-analyst",
        "title": "Cybersecurity Analyst",
        "description": "Protects organizational infrastructure, networks, and data assets from cyber threats, vulnerabilities, and unauthorized access.",
        "difficulty_level": "Intermediate",
        "required_skills": ["Networking Protocols", "Linux", "Vulnerability Testing"],
        "important_skills": ["Python", "Problem Solving", "Analytical Thinking"],
        "optional_skills": ["AWS", "Docker", "Git"],
        "recommended_proficiency": {
            "Networking Protocols": "Intermediate",
            "Linux": "Intermediate",
            "Vulnerability Testing": "Intermediate"
        },
        "preferred_strengths": ["Vigilant Observation", "Risk Assessment", "Methodical Investigation"],
        "interest_areas": ["Cyber Defense", "Ethical Hacking", "Security Compliance"],
        "work_style": "High-Stakes Protective Monitoring",
        "responsibilities": ["Monitor security alerts", "Conduct vulnerability scans", "Implement security policies", "Investigate threat breaches"],
        "learning_areas": ["Penetration Testing", "Zero Trust Architecture", "Cloud Security"]
    },
    {
        "slug": "cloud-devops-engineer",
        "title": "Cloud / DevOps Engineer",
        "description": "Automates cloud infrastructure provisioning, CI/CD pipelines, container orchestration, and system reliability monitoring.",
        "difficulty_level": "Intermediate to Advanced",
        "required_skills": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD Pipelines"],
        "important_skills": ["Linux", "Python", "Git", "GCP"],
        "optional_skills": ["Go", "Systems Thinking"],
        "recommended_proficiency": {
            "AWS": "Intermediate",
            "Docker": "Intermediate",
            "Kubernetes": "Intermediate",
            "Terraform": "Intermediate",
            "CI/CD Pipelines": "Intermediate"
        },
        "preferred_strengths": ["Systems Thinking", "Automation Mindset", "Operational Reliability"],
        "interest_areas": ["Cloud Infrastructure", "Site Reliability", "Automation"],
        "work_style": "Infrastructure & Platform Support",
        "responsibilities": ["Maintain CI/CD pipelines", "Manage Kubernetes clusters", "Provision Infrastructure as Code", "Monitor uptime"],
        "learning_areas": ["GitOps", "Service Mesh (Istio)", "Cost Optimization"]
    },
    {
        "slug": "ui-ux-designer",
        "title": "UI / UX Designer",
        "description": "Researches user needs, creates wireframes, prototypes visual interfaces, and crafts human-centered product experiences.",
        "difficulty_level": "Entry to Intermediate",
        "required_skills": ["Figma", "HTML", "CSS"],
        "important_skills": ["Communication", "Problem Solving"],
        "optional_skills": ["React", "Tailwind CSS"],
        "recommended_proficiency": {
            "Figma": "Advanced",
            "HTML": "Beginner",
            "CSS": "Beginner"
        },
        "preferred_strengths": ["Visual Design Instinct", "User Empathy", "Creative Problem Solving"],
        "interest_areas": ["Human-Computer Interaction", "Product Design", "User Experience"],
        "work_style": "User-Focused Creative Collaboration",
        "responsibilities": ["Conduct user interviews", "Design Figma prototypes", "Maintain design system UI kit", "Test usability"],
        "learning_areas": ["Micro-interactions", "Accessibility (WCAG)", "Design Systems Tokens"]
    },
    {
        "slug": "product-manager",
        "title": "Product Manager",
        "description": "Defines product strategy, prioritizes feature roadmaps, and aligns cross-functional engineering, design, and business teams.",
        "difficulty_level": "Intermediate to Advanced",
        "required_skills": ["Agile/Scrum", "Communication", "Leadership", "Stakeholder Communication"],
        "important_skills": ["Jira", "SQL", "Problem Solving", "Analytical Thinking"],
        "optional_skills": ["Data Visualization", "Figma"],
        "recommended_proficiency": {
            "Agile/Scrum": "Intermediate",
            "Communication": "Advanced",
            "Leadership": "Intermediate",
            "Stakeholder Communication": "Advanced"
        },
        "preferred_strengths": ["Strategic Prioritization", "Communication & Leadership", "Product Intuition"],
        "interest_areas": ["Product Vision", "Business Growth", "Cross-Functional Leadership"],
        "work_style": "Cross-Functional Strategic Coordination",
        "responsibilities": ["Define product vision & scope", "Write spec requirements", "Prioritize engineering backlog", "Measure KPI metrics"],
        "learning_areas": ["Growth Loops", "Product Analytics", "Go-To-Market Strategy"]
    },
    {
        "slug": "business-analyst",
        "title": "Business Analyst",
        "description": "Bridges business goals and technical engineering teams by evaluating processes, documenting business requirements, and optimizing workflows.",
        "difficulty_level": "Entry to Intermediate",
        "required_skills": ["SQL", "Jira", "Communication", "Analytical Thinking"],
        "important_skills": ["Problem Solving", "Stakeholder Communication", "Tableau"],
        "optional_skills": ["Python", "PowerBI"],
        "recommended_proficiency": {
            "SQL": "Intermediate",
            "Jira": "Intermediate",
            "Communication": "Intermediate",
            "Analytical Thinking": "Intermediate"
        },
        "preferred_strengths": ["Structured Communication", "Process Optimization", "Analytical Problem Solving"],
        "interest_areas": ["Business Workflows", "Requirements Analysis", "Operations"],
        "work_style": "Business & Engineering Facilitation",
        "responsibilities": ["Gather business requirements", "Document functional specifications", "Analyze workflow bottlenecks", "Validate solution UAT"],
        "learning_areas": ["BPMN 2.0", "Data Modeling Basics", "Agile Product Ownership"]
    }
]
