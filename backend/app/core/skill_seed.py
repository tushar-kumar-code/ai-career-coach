from typing import List, Dict, Any

SEED_SKILL_DEFINITIONS: List[Dict[str, Any]] = [
    # Programming Languages
    {"slug": "python", "name": "Python", "category": "Programming Languages", "description": "High-level programming language popular for web, data analysis, and AI/ML."},
    {"slug": "javascript", "name": "JavaScript", "category": "Programming Languages", "description": "Core dynamic language of web browsers and web platforms."},
    {"slug": "typescript", "name": "TypeScript", "category": "Programming Languages", "description": "Strongly typed superset of JavaScript for scalable web development."},
    {"slug": "java", "name": "Java", "category": "Programming Languages", "description": "Class-based object-oriented language widely used in enterprise applications."},
    {"slug": "c-plus-plus", "name": "C++", "category": "Programming Languages", "description": "High-performance systems programming language."},
    {"slug": "go", "name": "Go", "category": "Programming Languages", "description": "Statically typed concurrent programming language created by Google."},
    {"slug": "rust", "name": "Rust", "category": "Programming Languages", "description": "Memory-safe systems programming language."},

    # Web Development
    {"slug": "html", "name": "HTML", "category": "Web Development", "description": "Standard markup language for web page structure."},
    {"slug": "css", "name": "CSS", "category": "Web Development", "description": "Style sheet language used for describing presentation of HTML documents."},
    {"slug": "react", "name": "React", "category": "Web Development", "description": "Frontend UI library for building interactive component-driven user interfaces."},
    {"slug": "next-js", "name": "Next.js", "category": "Web Development", "description": "Production React framework with SSR, SSG, and API routes."},
    {"slug": "tailwind-css", "name": "Tailwind CSS", "category": "Web Development", "description": "Utility-first CSS framework for rapid UI styling."},
    {"slug": "node-js", "name": "Node.js", "category": "Web Development", "description": "Server-side JavaScript runtime environment."},
    {"slug": "fastapi", "name": "FastAPI", "category": "Web Development", "description": "High-performance Python web framework for RESTful APIs."},
    {"slug": "express-js", "name": "Express.js", "category": "Web Development", "description": "Minimalist server framework for Node.js."},

    # Databases
    {"slug": "sql", "name": "SQL", "category": "Databases", "description": "Domain-specific language for querying relational database management systems."},
    {"slug": "postgresql", "name": "PostgreSQL", "category": "Databases", "description": "Advanced open-source object-relational database system."},
    {"slug": "mongodb", "name": "MongoDB", "category": "Databases", "description": "Document-based NoSQL database for unstructured JSON data."},
    {"slug": "redis", "name": "Redis", "category": "Databases", "description": "In-memory key-value data structure store used as a database and cache."},

    # Data & Analytics
    {"slug": "pandas", "name": "Pandas", "category": "Data & Analytics", "description": "Data manipulation and analysis library for Python."},
    {"slug": "numpy", "name": "NumPy", "category": "Data & Analytics", "description": "Fundamental package for scientific computing with multi-dimensional arrays in Python."},
    {"slug": "tableau", "name": "Tableau", "category": "Data & Analytics", "description": "Business intelligence software for creating interactive data visualisations."},
    {"slug": "powerbi", "name": "PowerBI", "category": "Data & Analytics", "description": "Microsoft data visualization tool for enterprise business analytics."},
    {"slug": "data-visualization", "name": "Data Visualization", "category": "Data & Analytics", "description": "Technique of transforming complex datasets into visual charts and stories."},

    # AI/ML
    {"slug": "pytorch", "name": "PyTorch", "category": "AI/ML", "description": "Open-source machine learning library used for computer vision and NLP."},
    {"slug": "tensorflow", "name": "TensorFlow", "category": "AI/ML", "description": "End-to-end open-source machine learning platform."},
    {"slug": "scikit-learn", "name": "Scikit-Learn", "category": "AI/ML", "description": "Python module for machine learning and data mining algorithms."},
    {"slug": "llms", "name": "LLMs", "category": "AI/ML", "description": "Large Language Models and Generative AI prompt engineering."},
    {"slug": "vector-dbs", "name": "Vector Databases", "category": "AI/ML", "description": "Specialized databases for semantic embedding search (Chroma, Pinecone, Qdrant)."},

    # Cloud
    {"slug": "aws", "name": "AWS", "category": "Cloud", "description": "Amazon Web Services cloud platform and ecosystem."},
    {"slug": "gcp", "name": "GCP", "category": "Cloud", "description": "Google Cloud Platform infrastructure services."},
    {"slug": "azure", "name": "Azure", "category": "Cloud", "description": "Microsoft cloud computing services."},

    # DevOps
    {"slug": "docker", "name": "Docker", "category": "DevOps", "description": "Containerization platform for packaging applications and dependencies."},
    {"slug": "kubernetes", "name": "Kubernetes", "category": "DevOps", "description": "Open-source container orchestration system for automating application deployment."},
    {"slug": "terraform", "name": "Terraform", "category": "DevOps", "description": "Infrastructure as Code tool for building and provisioning cloud resources."},
    {"slug": "ci-cd-pipelines", "name": "CI/CD Pipelines", "category": "DevOps", "description": "Automated continuous integration and deployment pipelines."},

    # Cybersecurity
    {"slug": "networking-protocols", "name": "Networking Protocols", "category": "Cybersecurity", "description": "Fundamental computer network communications (TCP/IP, HTTP, DNS, SSL)."},
    {"slug": "linux", "name": "Linux", "category": "Cybersecurity", "description": "Open-source operating system administration and terminal command execution."},
    {"slug": "vulnerability-testing", "name": "Vulnerability Testing", "category": "Cybersecurity", "description": "Security auditing and penetration testing techniques."},

    # Software Engineering
    {"slug": "data-structures", "name": "Data Structures", "category": "Software Engineering", "description": "Core computer science data organization formats (Arrays, Hash Maps, Trees, Graphs)."},
    {"slug": "oop", "name": "OOP", "category": "Software Engineering", "description": "Object-Oriented Programming design paradigms."},
    {"slug": "rest-apis", "name": "REST APIs", "category": "Software Engineering", "description": "Architectural style for web service API contracts."},
    {"slug": "git", "name": "Git", "category": "Software Engineering", "description": "Distributed version control system for tracking source code changes."},

    # Tools
    {"slug": "github", "name": "GitHub", "category": "Tools", "description": "Cloud code hosting platform for version control and collaboration."},
    {"slug": "figma", "name": "Figma", "category": "Tools", "description": "Collaborative web-based UI/UX vector design and prototyping application."},
    {"slug": "jira", "name": "Jira", "category": "Tools", "description": "Issue tracking and project management software for Agile teams."},

    # Communication
    {"slug": "communication", "name": "Communication", "category": "Communication", "description": "Clear verbal and written technical storytelling and stakeholder collaboration."},
    {"slug": "stakeholder-communication", "name": "Stakeholder Communication", "category": "Communication", "description": "Articulating technical decisions to non-technical business leaders."},

    # Leadership
    {"slug": "leadership", "name": "Leadership", "category": "Leadership", "description": "Guiding technical initiatives, mentoring peers, and driving projects to completion."},
    {"slug": "agile-scrum", "name": "Agile/Scrum", "category": "Leadership", "description": "Iterative software development frameworks and team organization."},

    # Problem Solving
    {"slug": "problem-solving", "name": "Problem Solving", "category": "Problem Solving", "description": "Methodical approach to dissecting complex bugs and system failures."},
    {"slug": "logical-reasoning", "name": "Logical Reasoning", "category": "Problem Solving", "description": "Algorithmic thinking and decision-making logic."},

    # Analytical Thinking
    {"slug": "analytical-thinking", "name": "Analytical Thinking", "category": "Analytical Thinking", "description": "Dissecting quantitative data to uncover root causes and drive strategy."},
    {"slug": "systems-thinking", "name": "Systems Thinking", "category": "Analytical Thinking", "description": "Understanding end-to-end system architectures and inter-dependencies."}
]
