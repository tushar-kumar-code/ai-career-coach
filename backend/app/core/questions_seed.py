from typing import List, Dict, Any

SEED_QUESTIONS: List[Dict[str, Any]] = [
    {
        "order_index": 1,
        "dimension": "Logical Reasoning & Systems",
        "question_type": "scenario",
        "question_text": "Imagine a web service starts crashing intermittently every day at 2:00 PM. Memory usage spikes up to 99%. What is your immediate instinctual approach to investigate this issue?",
        "difficulty_level": 1,
        "options": [
            {
                "id": "A",
                "text": "Inspect system log files, stack traces, and memory heap dumps to pinpoint the exact failing code lines.",
                "archetype": "Systems Builder",
                "weights": {"Software Developer": 9, "Backend Developer": 10, "Logical Reasoning": 9}
            },
            {
                "id": "B",
                "text": "Query database access logs and traffic analytics to check if a scheduled daily job or API spike occurred at 2:00 PM.",
                "archetype": "Data Investigator",
                "weights": {"Data Analyst": 9, "Backend Developer": 8, "Analytical Thinking": 9}
            },
            {
                "id": "C",
                "text": "Check server container metrics, load balancer rules, and auto-scaling group thresholds to ensure server resilience.",
                "archetype": "Infrastructure Architect",
                "weights": {"Cloud/DevOps Engineer": 10, "Cybersecurity Analyst": 7, "Systems Thinking": 9}
            },
            {
                "id": "D",
                "text": "Gather reports from impacted users to understand what feature they were attempting to use when the outage occurred.",
                "archetype": "User & Process Strategist",
                "weights": {"Product Manager": 8, "Business Analyst": 9, "User Empathy": 9}
            }
        ]
    },
    {
        "order_index": 2,
        "dimension": "Work Style & Environment",
        "question_type": "preference",
        "question_text": "Which work environment energizes you the most when completing a major project?",
        "difficulty_level": 1,
        "options": [
            {
                "id": "A",
                "text": "Deep focus time writing clean code, designing logic models, and solving technical algorithms independently.",
                "archetype": "Systems Builder",
                "weights": {"Software Developer": 9, "Backend Developer": 9, "Independent Focus": 9}
            },
            {
                "id": "B",
                "text": "Interactive collaborative sessions crafting user interfaces, visual flows, and UI experiences with feedback.",
                "archetype": "Creative Visualizer",
                "weights": {"Frontend Developer": 9, "UI/UX Designer": 10, "Creativity": 8}
            },
            {
                "id": "C",
                "text": "Analyzing datasets, finding hidden patterns, and building charts that answer key strategic questions.",
                "archetype": "Data Investigator",
                "weights": {"Data Analyst": 10, "Data Scientist": 9, "Analytical Thinking": 10}
            },
            {
                "id": "D",
                "text": "Facilitating team discussions, organizing project roadmaps, and translating user needs into actionable goals.",
                "archetype": "User & Process Strategist",
                "weights": {"Product Manager": 10, "Business Analyst": 9, "Collaboration": 9}
            }
        ]
    },
    {
        "order_index": 3,
        "dimension": "Problem Solving & Innovation",
        "question_type": "scenario",
        "question_text": "Your team needs to automate customer support inquiry classification. Which angle of the solution excites you most?",
        "difficulty_level": 2,
        "options": [
            {
                "id": "A",
                "text": "Training and fine-tuning a Machine Learning or Natural Language Model to classify incoming support tickets accurately.",
                "archetype": "AI & ML Pioneer",
                "weights": {"AI/ML Engineer": 10, "Data Scientist": 9, "Technology Interest": 10}
            },
            {
                "id": "B",
                "text": "Building a robust microservice API pipeline that receives the tickets, routes payloads, and stores results cleanly.",
                "archetype": "Systems Builder",
                "weights": {"Backend Developer": 10, "Software Developer": 8, "Problem Solving": 9}
            },
            {
                "id": "C",
                "text": "Designing an intuitive dashboard UI where support agents can review AI recommendations and override classifications.",
                "archetype": "Creative Visualizer",
                "weights": {"Frontend Developer": 9, "UI/UX Designer": 9, "User Empathy": 9}
            },
            {
                "id": "D",
                "text": "Evaluating security controls to ensure customer personally identifiable information (PII) is encrypted and protected.",
                "archetype": "Infrastructure Architect",
                "weights": {"Cybersecurity Analyst": 10, "Cloud/DevOps Engineer": 7, "Risk Assessment": 9}
            }
        ]
    },
    {
        "order_index": 4,
        "dimension": "Analytical Thinking & Data",
        "question_type": "mini_reasoning",
        "question_text": "When presented with a dataset containing 500,000 transaction records, what is your first logical step?",
        "difficulty_level": 2,
        "options": [
            {
                "id": "A",
                "text": "Check for missing values, outliers, data distributions, and clean anomalies before drawing conclusions.",
                "archetype": "Data Investigator",
                "weights": {"Data Analyst": 10, "Data Scientist": 10, "Analytical Thinking": 10}
            },
            {
                "id": "B",
                "text": "Design a relational database schema with optimal indexes to query the dataset with millisecond response time.",
                "archetype": "Systems Builder",
                "weights": {"Backend Developer": 9, "Software Developer": 8, "Data Modeling": 9}
            },
            {
                "id": "C",
                "text": "Identify which key business metrics (revenue trends, customer churn) can be summarized from this dataset.",
                "archetype": "User & Process Strategist",
                "weights": {"Business Analyst": 10, "Product Manager": 8, "Business Acumen": 9}
            },
            {
                "id": "D",
                "text": "Explore whether an automated anomaly detection algorithm can flag suspicious or fraudulent transactions.",
                "archetype": "AI & ML Pioneer",
                "weights": {"AI/ML Engineer": 9, "Cybersecurity Analyst": 8, "Pattern Recognition": 9}
            }
        ]
    },
    {
        "order_index": 5,
        "dimension": "Creativity & Visual Instincts",
        "question_type": "preference",
        "question_text": "When you visit a poorly designed website or mobile app that is confusing to navigate, how do you react?",
        "difficulty_level": 1,
        "options": [
            {
                "id": "A",
                "text": "I immediately mentally redesign the layout, navigation hierarchy, color contrast, and interactive buttons.",
                "archetype": "Creative Visualizer",
                "weights": {"UI/UX Designer": 10, "Frontend Developer": 9, "Creativity": 10}
            },
            {
                "id": "B",
                "text": "I inspect the developer tools network tab to see why page API requests are loading so slowly.",
                "archetype": "Systems Builder",
                "weights": {"Frontend Developer": 8, "Software Developer": 8, "Technology Interest": 8}
            },
            {
                "id": "C",
                "text": "I consider how the poor user journey harms conversion metrics, user retention, and business growth.",
                "archetype": "User & Process Strategist",
                "weights": {"Product Manager": 10, "Business Analyst": 9, "Product Vision": 9}
            },
            {
                "id": "D",
                "text": "I check if the app lacks HTTPS certificates or exposes client-side API secrets in source code.",
                "archetype": "Infrastructure Architect",
                "weights": {"Cybersecurity Analyst": 9, "Cloud/DevOps Engineer": 7, "Security Awareness": 9}
            }
        ]
    },
    {
        "order_index": 6,
        "dimension": "Technology Interest & Curiosity",
        "question_type": "preference",
        "question_text": "Which technology topic would you most eagerly read an article or watch a tech talk about?",
        "difficulty_level": 1,
        "options": [
            {
                "id": "A",
                "text": "How modern Generative AI, Large Language Models, and Neural Networks are trained and evaluated.",
                "archetype": "AI & ML Pioneer",
                "weights": {"AI/ML Engineer": 10, "Data Scientist": 9, "Technology Interest": 10}
            },
            {
                "id": "B",
                "text": "How cloud providers manage zero-downtime deployments using Kubernetes and automated CI/CD pipelines.",
                "archetype": "Infrastructure Architect",
                "weights": {"Cloud/DevOps Engineer": 10, "Backend Developer": 7, "Automation": 9}
            },
            {
                "id": "C",
                "text": "How high-throughput applications structure code, design patterns, and database caching for 1M+ active users.",
                "archetype": "Systems Builder",
                "weights": {"Software Developer": 10, "Backend Developer": 9, "Systems Architecture": 9}
            },
            {
                "id": "D",
                "text": "How top tech companies conduct user research to discover unmet user needs and build multi-billion dollar products.",
                "archetype": "User & Process Strategist",
                "weights": {"Product Manager": 10, "UI/UX Designer": 8, "Product Strategy": 9}
            }
        ]
    },
    {
        "order_index": 7,
        "dimension": "Collaboration & Team Dynamics",
        "question_type": "work_style",
        "question_text": "When collaborating with a cross-functional team on a high-priority deadline, what role do you naturally assume?",
        "difficulty_level": 1,
        "options": [
            {
                "id": "A",
                "text": "The technical execution specialist — diving straight into code or technical assets to complete core deliverables.",
                "archetype": "Systems Builder",
                "weights": {"Software Developer": 9, "Full Stack Developer": 9, "Execution": 9}
            },
            {
                "id": "B",
                "text": "The analyst — verifying assumptions with data, double-checking facts, and validating requirements accuracy.",
                "archetype": "Data Investigator",
                "weights": {"Data Analyst": 9, "Business Analyst": 9, "Analytical Rigor": 9}
            },
            {
                "id": "C",
                "text": "The facilitator — keeping everyone aligned, clarifying goals, organizing milestones, and unblocking team members.",
                "archetype": "User & Process Strategist",
                "weights": {"Product Manager": 10, "Business Analyst": 8, "Leadership": 9}
            },
            {
                "id": "D",
                "text": "The reliability guardian — testing edge cases, checking for deployment risks, and ensuring stability.",
                "archetype": "Infrastructure Architect",
                "weights": {"Cloud/DevOps Engineer": 8, "Cybersecurity Analyst": 8, "Risk Assessment": 9}
            }
        ]
    },
    {
        "order_index": 8,
        "dimension": "Communication Preference",
        "question_type": "preference",
        "question_text": "How do you prefer to explain complex technical concepts to non-technical stakeholders?",
        "difficulty_level": 1,
        "options": [
            {
                "id": "A",
                "text": "Using clear visual diagrams, flowcharts, and interactive interface mockups.",
                "archetype": "Creative Visualizer",
                "weights": {"UI/UX Designer": 9, "Frontend Developer": 8, "Visual Communication": 9}
            },
            {
                "id": "B",
                "text": "Using real-world analogies, high-level business goals, and clear summary bullet points.",
                "archetype": "User & Process Strategist",
                "weights": {"Product Manager": 9, "Business Analyst": 10, "Structured Communication": 9}
            },
            {
                "id": "C",
                "text": "Using data metrics, statistical charts, and evidence-backed figures.",
                "archetype": "Data Investigator",
                "weights": {"Data Analyst": 9, "Data Scientist": 8, "Data Storytelling": 9}
            },
            {
                "id": "D",
                "text": "Using concise code examples, technical documentation, and clear architectural diagrams.",
                "archetype": "Systems Builder",
                "weights": {"Software Developer": 9, "Backend Developer": 8, "Technical Writing": 8}
            }
        ]
    },
    {
        "order_index": 9,
        "dimension": "Motivation & Growth Driver",
        "question_type": "preference",
        "question_text": "What type of career milestone would make you feel most proud after 1 year in a role?",
        "difficulty_level": 1,
        "options": [
            {
                "id": "A",
                "text": "Having architected and launched a complex software feature that thousands of people use daily.",
                "archetype": "Systems Builder",
                "weights": {"Software Developer": 9, "Full Stack Developer": 9, "Impact": 9}
            },
            {
                "id": "B",
                "text": "Having uncovered a critical data insight that directly increased company efficiency or revenue by 25%.",
                "archetype": "Data Investigator",
                "weights": {"Data Analyst": 10, "Data Scientist": 9, "Business Impact": 9}
            },
            {
                "id": "C",
                "text": "Having designed a seamless user interface experience that earned rave reviews from users.",
                "archetype": "Creative Visualizer",
                "weights": {"UI/UX Designer": 10, "Frontend Developer": 9, "User Experience": 10}
            },
            {
                "id": "D",
                "text": "Having built an automated cloud deployment pipeline that reduced system downtime to near zero.",
                "archetype": "Infrastructure Architect",
                "weights": {"Cloud/DevOps Engineer": 10, "Cybersecurity Analyst": 8, "Reliability": 9}
            }
        ]
    },
    {
        "order_index": 10,
        "dimension": "Technical Instinct & Logic",
        "question_type": "tech_signal",
        "question_text": "When building an application that needs to search through 100,000 user profiles by name, which logic choice feels most natural?",
        "difficulty_level": 2,
        "options": [
            {
                "id": "A",
                "text": "Add a database index on the name column or use an inverted search index like Elasticsearch.",
                "archetype": "Systems Builder",
                "weights": {"Backend Developer": 10, "Software Developer": 9, "Technical Aptitude": 9}
            },
            {
                "id": "B",
                "text": "Implement client-side instant filtering with debounced search input for smooth visual feedback.",
                "archetype": "Creative Visualizer",
                "weights": {"Frontend Developer": 10, "UI/UX Designer": 7, "Frontend Logic": 9}
            },
            {
                "id": "C",
                "text": "Use fuzzy matching or natural language processing vectors to match misspelled search terms.",
                "archetype": "AI & ML Pioneer",
                "weights": {"AI/ML Engineer": 10, "Data Scientist": 8, "AI Logic": 9}
            },
            {
                "id": "D",
                "text": "Implement rate limiting on search endpoints to prevent malicious scraping or DDoS attacks.",
                "archetype": "Infrastructure Architect",
                "weights": {"Cybersecurity Analyst": 9, "Cloud/DevOps Engineer": 8, "Security Logic": 9}
            }
        ]
    },
    {
        "order_index": 11,
        "dimension": "Systems & Automation",
        "question_type": "scenario",
        "question_text": "Your team repeats a 4-hour manual testing and server deployment process every Friday. How do you respond?",
        "difficulty_level": 1,
        "options": [
            {
                "id": "A",
                "text": "Write a script or CI/CD workflow to automate the entire build, test, and deployment process in minutes.",
                "archetype": "Infrastructure Architect",
                "weights": {"Cloud/DevOps Engineer": 10, "Software Developer": 8, "Automation": 10}
            },
            {
                "id": "B",
                "text": "Write comprehensive automated unit and integration tests to verify code stability before deployment.",
                "archetype": "Systems Builder",
                "weights": {"Software Developer": 9, "Backend Developer": 9, "Quality Engineering": 9}
            },
            {
                "id": "C",
                "text": "Document the deployment workflow steps clearly in a shared knowledge base so anyone can execute it safely.",
                "archetype": "User & Process Strategist",
                "weights": {"Business Analyst": 9, "Product Manager": 7, "Documentation": 8}
            },
            {
                "id": "D",
                "text": "Measure how much time and developer salary cost is wasted on manual deployment to justify automated tools.",
                "archetype": "Data Investigator",
                "weights": {"Data Analyst": 8, "Product Manager": 8, "Cost Analysis": 8}
            }
        ]
    },
    {
        "order_index": 12,
        "dimension": "Natural Strengths",
        "question_type": "preference",
        "question_text": "When friends or colleagues ask you for help on technical or project challenges, what do they usually come to you for?",
        "difficulty_level": 1,
        "options": [
            {
                "id": "A",
                "text": "Debugging tricky code errors, fixing broken algorithms, or structuring code logic.",
                "archetype": "Systems Builder",
                "weights": {"Software Developer": 10, "Full Stack Developer": 9, "Debugging": 10}
            },
            {
                "id": "B",
                "text": "Making things look beautiful, designing slides/pages, or fixing layout and visual details.",
                "archetype": "Creative Visualizer",
                "weights": {"UI/UX Designer": 10, "Frontend Developer": 9, "Aesthetics": 10}
            },
            {
                "id": "C",
                "text": "Making sense of messy data, creating Excel/SQL formulas, or interpreting charts and statistics.",
                "archetype": "Data Investigator",
                "weights": {"Data Analyst": 10, "Data Scientist": 9, "Data Skills": 10}
            },
            {
                "id": "D",
                "text": "Structuring complex ideas into actionable steps, organizing plans, or leading group decisions.",
                "archetype": "User & Process Strategist",
                "weights": {"Product Manager": 10, "Business Analyst": 9, "Organization": 9}
            }
        ]
    },
    {
        "order_index": 13,
        "dimension": "Current Technical Skills Signal",
        "question_type": "tech_signal",
        "question_text": "Which technical area do you currently feel most confident in, or are most excited to master?",
        "difficulty_level": 1,
        "options": [
            {
                "id": "A",
                "text": "Programming Languages & Web Frameworks (Python, JavaScript, React, FastAPI, Java).",
                "archetype": "Systems Builder",
                "weights": {"Software Developer": 9, "Full Stack Developer": 9, "Web Development": 9}
            },
            {
                "id": "B",
                "text": "Data Analysis & Databases (SQL, Pandas, PostgreSQL, Data Visualization, Excel).",
                "archetype": "Data Investigator",
                "weights": {"Data Analyst": 10, "Data Scientist": 9, "SQL & Data": 10}
            },
            {
                "id": "C",
                "text": "Machine Learning & AI Tools (PyTorch, LLM Prompts, Scikit-learn, OpenAI API).",
                "archetype": "AI & ML Pioneer",
                "weights": {"AI/ML Engineer": 10, "Data Scientist": 8, "AI Tech": 10}
            },
            {
                "id": "D",
                "text": "Design & Product Tools (Figma, Wireframing, User Research, Agile/Jira).",
                "archetype": "Creative Visualizer",
                "weights": {"UI/UX Designer": 10, "Product Manager": 9, "Design & Product": 9}
            }
        ]
    },
    {
        "order_index": 14,
        "dimension": "Security & Risk Instincts",
        "question_type": "scenario",
        "question_text": "When building an app that stores user passwords, which practice is most essential?",
        "difficulty_level": 2,
        "options": [
            {
                "id": "A",
                "text": "Hash passwords using a strong salted algorithm (Bcrypt/Argon2) before saving to the DB.",
                "archetype": "Systems Builder",
                "weights": {"Cybersecurity Analyst": 10, "Backend Developer": 9, "Security Best Practice": 10}
            },
            {
                "id": "B",
                "text": "Ensure password input fields mask characters and provide clear real-time password strength rules.",
                "archetype": "Creative Visualizer",
                "weights": {"Frontend Developer": 9, "UI/UX Designer": 7, "User Experience": 8}
            },
            {
                "id": "C",
                "text": "Monitor failed login attempt rates in logs to detect brute-force password spraying attacks.",
                "archetype": "Infrastructure Architect",
                "weights": {"Cybersecurity Analyst": 10, "Cloud/DevOps Engineer": 8, "Threat Monitoring": 9}
            },
            {
                "id": "D",
                "text": "Draft a privacy policy explaining how credential data is stored and protected according to GDPR rules.",
                "archetype": "User & Process Strategist",
                "weights": {"Business Analyst": 9, "Product Manager": 7, "Compliance": 8}
            }
        ]
    },
    {
        "order_index": 15,
        "dimension": "Problem Solving Complexity",
        "question_type": "mini_reasoning",
        "question_text": "When faced with a bug in code that only happens occasionally and is hard to reproduce, what do you do?",
        "difficulty_level": 2,
        "options": [
            {
                "id": "A",
                "text": "Add structured logging around race conditions and boundary conditions to capture state when it fails.",
                "archetype": "Systems Builder",
                "weights": {"Software Developer": 10, "Backend Developer": 9, "Debugging": 10}
            },
            {
                "id": "B",
                "text": "Analyze historical event timestamps to correlate failure times with network or server load patterns.",
                "archetype": "Data Investigator",
                "weights": {"Data Analyst": 9, "Cloud/DevOps Engineer": 8, "Pattern Analysis": 9}
            },
            {
                "id": "C",
                "text": "Replicate user interaction sequences step-by-step to find the exact edge case trigger.",
                "archetype": "Creative Visualizer",
                "weights": {"Frontend Developer": 8, "UI/UX Designer": 7, "User Reproduction": 8}
            },
            {
                "id": "D",
                "text": "Assess the severity impact on users to decide whether to hotfix immediately or schedule in next sprint.",
                "archetype": "User & Process Strategist",
                "weights": {"Product Manager": 10, "Business Analyst": 8, "Prioritization": 9}
            }
        ]
    },
    {
        "order_index": 16,
        "dimension": "Product Vision & Strategy",
        "question_type": "preference",
        "question_text": "If you had 3 months to build any technology project from scratch, what would you choose?",
        "difficulty_level": 1,
        "options": [
            {
                "id": "A",
                "text": "A high-performance SaaS web application with authentication, payment processing, and smooth UI.",
                "archetype": "Systems Builder",
                "weights": {"Full Stack Developer": 10, "Software Developer": 9, "Product Building": 10}
            },
            {
                "id": "B",
                "text": "An AI assistant tool powered by custom LLM agents and RAG vector search.",
                "archetype": "AI & ML Pioneer",
                "weights": {"AI/ML Engineer": 10, "Data Scientist": 9, "AI Project": 10}
            },
            {
                "id": "C",
                "text": "An interactive data analytics platform visualizing real-world financial or sports trends.",
                "archetype": "Data Investigator",
                "weights": {"Data Analyst": 10, "Data Scientist": 8, "Data Project": 10}
            },
            {
                "id": "D",
                "text": "A mobile application with a stunning design system that solves a daily productivity problem.",
                "archetype": "Creative Visualizer",
                "weights": {"UI/UX Designer": 10, "Frontend Developer": 9, "Mobile App": 9}
            }
        ]
    }
]
