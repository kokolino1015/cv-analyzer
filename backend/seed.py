from retrieval import insert_listings

LISTINGS = [
    {
        "company": "Playtech Managed Services",
        "title": "AI Engineer",
        "text": """Playtech Managed Services is looking for an AI Engineer with strong system design thinking,
exceptional collaboration skills, and a high sense of ownership.

Build AI powered applications using modern LLMs, RAG, and AI agents to deliver intelligent, high impact
enterprise capabilities. Develop scalable backend services using Python, server side JavaScript, and .NET,
ensuring clean, maintainable architecture. Create modern web applications using React and contribute across
the full stack. Design and implement APIs, microservices, and system integrations for robust distributed
systems. Develop and optimize SQL, NoSQL, and vector database solutions to support AI workloads. Build data
pipelines, ETL and ELT flows, and AI knowledge repositories for structured and unstructured data. Deploy and
operate solutions in cloud environments, Azure preferred, ensuring reliability and scalability.

Requirements: 3+ years of software engineering experience building production grade systems. Work confidently
with backend frameworks using Python, FastAPI, Flask, Node.js, and .NET. Apply practical AI and ML knowledge
including LLMs, Generative AI, RAG architectures, and AI agents. Demonstrate strong API expertise in REST,
microservices, and modern integration patterns. Utilize databases including SQL Server, PostgreSQL, MySQL,
MongoDB, Cosmos DB, Redis, and vector stores such as Azure AI Search, Pinecone, Weaviate, or Milvus. Apply
prompt engineering, semantic search, and AI evaluation strategies to improve reliability. Understand data
modeling, query optimization, and pipeline development. Work with modern cloud and DevOps tools including
Azure, Docker, Kubernetes, and monitoring systems.""",
    },
    {
        "company": "KBC Global Services",
        "title": "Python Developer, M365 Integration",
        "text": """The M365 Integration team plays a key role in enabling conversational AI solutions and Power
Platform integrations for departments such as HR, Facilities, and Marketing and Communications.

Translating business requirements into conversational AI solutions. Performing business and functional
analysis to understand user needs and design intuitive solutions. Building and deploying Retrieval Augmented
Generation (RAG) applications and related AI components using Amazon Bedrock within a secure AWS environment.
Collaborating with architecture teams to apply architectural patterns, security standards, and best practices.
Working closely with the Data Science team, the Public Cloud team, and other stakeholders to ensure seamless
integration and deployment. Contributing to the evolution of the platform through custom development and high
code extensions in Python. Supporting the delivery, monitoring, and continuous improvement of AI powered
business solutions.

Key competences: 3+ years of experience with Python. Hands on experience with Amazon Web Services, including
Amazon Bedrock, S3 and other cloud storage services. Understanding of Retrieval Augmented Generation (RAG)
architectures. Experience working with Claude or similar Large Language Models. Knowledge of REST APIs and
integrations. Experience with CI/CD pipelines and DevOps practices. Strong analytical and problem solving
mindset. Ability to translate business needs into technical solutions.""",
    },
    {
        "company": "Fastmarkets",
        "title": "AI Engineer, Innovation and AI",
        "text": """The Innovation and AI team is responsible for developing and delivering the company's AI and
data strategy through agentic AI systems, intelligent data applications, and AI powered analytics.

Design and develop agentic AI systems that solve real business problems: request intake agents, natural
language query systems, intelligent data exploration tools, and AI powered search and analysis features.
Integrate LLMs into applications using best practices: prompt engineering, tool use, multi turn conversation
management, output validation, and cost optimisation. Build semantic models and data schemas that enable
natural language querying over enterprise data, including custom RAG systems. Connect AI systems to data
pipelines. Develop full stack AI applications: Next.js frontends with streaming chat UIs, FastAPI and Python
backends for agentic workflows. Implement observability and evaluation frameworks for AI systems including
structured logging, conversation tracing and golden evals.

Essential: Advanced Python expertise including async and await, dependency injection, structured logging,
testing patterns, and Python type hints with Pydantic v2. Experience building production API services with
FastAPI, Django or Flask. TypeScript and JavaScript expertise with React and Next.js. LLM and prompt
engineering knowledge including multi turn conversation design, tool use and function calling, output parsing
and validation. Familiarity with agentic AI frameworks: LangGraph, LangChain, AutoGen, CrewAI or equivalent.
Can implement agent loops from scratch using the Anthropic SDK. Snowflake expertise. Semantic data modelling.""",
    },
    {
        "company": "Trane Technologies / Nuvolo",
        "title": "Software Engineer",
        "text": """We are seeking a Software Engineer with a strong foundation in computer science fundamentals
and practical experience building scalable applications. This role focuses on engineering excellence and
problem solving skills rather than platform specific knowledge.

Design and implement features following SOLID principles and clean code practices. Collaborate on full stack
development across frontend and backend systems. Participate in code reviews and contribute to continuous
improvement of engineering standards. Debug complex issues and optimize application performance. Design and
implement features in all areas of the product development including backend, frontend, mobile, CI/CD, cloud
services and data migration. Communicate effectively across frontend and backend integration points.

Required: 2 to 3 years of professional software development experience. Strong grasp of computer science
fundamentals including data structures, algorithms and design patterns. Demonstrated understanding of SOLID
principles and software architecture. Experience with at least one programming language such as JavaScript,
Python, Java or C#. Familiarity with version control systems. Understanding of CI/CD concepts and automated
testing. Knowledge of cloud platforms or willingness to learn. Experience with REST APIs and backend frontend
communication patterns. Strong problem solving and debugging skills.

We value solid programming fundamentals over framework expertise, a continuous learning mindset, code quality
and attention to detail.""",
    },
    {
        "company": "ICT Strypes",
        "title": "Python Software Engineer, ASML",
        "text": """We are growing our teams that work on various applications for ASML, the largest manufacturer
of lithography machines used in semiconductor manufacturing.

The applications tackle Python encryption, Statistical Process Control and Testing Support. They mimic the real
configuration of the lithography machines and give the user the chance to make changes and analyse them. They
maintain the software lifecycle of the client machine, containing a command line interface and modern web
application. Standalone Python based applications are used to calibrate the parameters, measure the performance,
and diagnose the machine.

Responsibilities: Implementation, testing, and integration of customer requirements. Debugging and fixing
problems in the existing code. Ensuring up to date and high quality documentation. Participating in Scrum
ceremonies. Mentoring teammates. Actively participating in architectural discussions.

Required: 3+ years of experience in programming in Python and its ecosystems. Experience with multi threading
and concurrency. Experience with debugging tools such as GDB and Valgrind. Version control systems.
Familiarity with Linux and Unix environments. Excellent problem solving skills and attention to detail.

Nice to have: cross platform development, MATLAB and C/C++, background in numerical computing, signal
processing, or scientific computing.""",
    },
    {
        "company": "Trading 212",
        "title": "DevOps Engineer",
        "text": """Design and deploy dynamically scalable, self healing infrastructure and applications in public
and private cloud environments. Use infrastructure as a service automation tools like Terraform, AWS
CloudFormation and Ansible. Migrate environments from on premise infrastructure to AWS and GCP environments.
Handling operational and security alerts and incidents. Improving infrastructure, application and security
monitoring systems. Continuous performance improvement and troubleshooting of critical components. The role
requires work on shifts, which may include public holidays.

What you need to have: Basic understanding of public cloud, AWS or GCP. Experience with CI/CD services such as
GitHub, GitLab or Jenkins. Basic understanding of containers and container orchestration systems including
Docker and Kubernetes. Previous experience with monitoring and log management systems such as Grafana, the ELK
Stack, Splunk or SIEM. Good understanding of networking and security concepts including TCP/IP, routing and
firewalls.

Nice to have: understanding of relational databases, basic knowledge of Python or Bash scripting,
infrastructure as code tools, configuration management tools such as Puppet and Ansible, experience with on
premise private cloud infrastructures running VMware or KVM.

Our tech stack: AWS and GCP, Terraform, Ansible, Puppet, GitHub, NGINX, Envoy, HAProxy, Docker, Kubernetes,
Amazon RDS, TimescaleDB, ClickHouse, Amazon MSK, RabbitMQ, Grafana, Prometheus, ELK Stack, OpenTelemetry.""",
    },
]

if __name__ == "__main__":
    insert_listings(LISTINGS)