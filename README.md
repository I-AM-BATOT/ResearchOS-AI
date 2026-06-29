<div align="center">

# 🔬 ResearchOS AI

### An Intelligent Multi-Agent Research Operating System

**Read. Understand. Verify. Compare. Learn. Present.**

Transform research papers into a collaborative AI-powered research workflow using specialized agents, semantic memory, scholarly search, and automated knowledge generation.

<p>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Memory-6D28D9?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</p>

**🏆 Kaggle Capstone — AI Agents: Intensive Vibe Coding**

---

### 🚀 From PDFs to Research Insights in Minutes

ResearchOS AI combines multiple AI agents that collaborate to analyze academic papers, discover related research, verify claims, generate literature reviews, create study materials, and build presentations—all within one intelligent research workspace.

<br>

<img src="YOUR_SCREENSHOT.png" width="100%">

</div>

---

# 📖 Overview

Research papers are becoming increasingly difficult to keep up with.

Researchers spend hours reading papers, comparing methodologies, verifying claims, discovering related work, preparing presentations, and identifying research gaps.

**ResearchOS AI** automates this entire workflow using a team of specialized AI agents.

Instead of relying on a single LLM, every task is handled by a dedicated agent with a specific responsibility, resulting in more accurate, transparent, and scalable research assistance.

---

# ✨ Key Features

## 🤖 Multi-Agent Collaboration

Ten specialized AI agents cooperate to complete complex research tasks.

- Coordinator Agent
- Paper Reader
- Research Explainer
- Fact Checker
- Related Work Finder
- Literature Review Builder
- Research Gap Detector
- Quiz & Teaching Agent
- Presentation Generator
- Memory Agent

---

## 📄 Smart Paper Analysis

Upload one or multiple research papers and automatically extract:

- Abstract
- Introduction
- Methodology
- Results
- Discussion
- Conclusion
- References
- Metadata

Supports multiple PDF research papers.

---

## 🧠 AI Research Assistant

Generate:

- Executive summaries
- Technical summaries
- Beginner explanations
- ELI5 explanations
- Research insights
- Methodology breakdowns

---

## 🔍 Fact Verification

ResearchOS AI verifies important research claims by comparing them against scholarly sources.

Features include:

- Claim extraction
- Evidence retrieval
- Confidence scoring
- Verification status
- Citation support

---

## 🌐 Related Research Discovery

Searches scholarly databases including:

- arXiv
- Semantic Scholar

Automatically discovers:

- Related papers
- Influential work
- Citation relationships
- Similar methodologies
- Emerging trends

---

## 📚 Literature Review Generation

Automatically builds comprehensive literature reviews across multiple uploaded papers.

Includes:

- State-of-the-art overview
- Method comparison
- Trend analysis
- Research evolution
- Strengths & weaknesses
- Future directions

---

## 💡 Research Gap Identification

Automatically detects:

- Missing experiments
- Dataset limitations
- Method weaknesses
- Open problems
- Novel research opportunities

Helping researchers discover potential publication ideas.

---

## 🎓 Learning Mode

Convert research papers into learning resources.

Generate:

- Flashcards
- MCQs
- Short-answer questions
- Study guides
- Teaching notes

Perfect for students and educators.

---

## 🎤 Presentation Builder

Automatically create:

- Slide outlines
- Speaker notes
- Conference presentations
- Poster summaries
- Research pitches

---

## 🧠 Persistent Memory

ResearchOS AI remembers previous sessions.

Supports:

- Semantic search
- Research history
- User preferences
- Previous outputs
- Paper summaries

Powered by **ChromaDB** with automatic **SQLite fallback**.

---

## 🔒 Secure by Design

Every request passes through multiple security layers.

- Prompt Injection Detection
- PDF Validation
- Input Validation
- PII Masking
- Safe Logging
- Human Verification

---

# 🏗️ System Architecture

```text
                     ┌──────────────────────┐
                     │    Streamlit UI      │
                     └──────────┬───────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │   Coordinator Agent    │
                    └──────────┬─────────────┘
                               │
      ┌──────────────┬──────────┼──────────┬──────────────┐
      ▼              ▼          ▼          ▼              ▼
 Paper Reader   Fact Checker  Related   Literature   Presentation
                              Work       Review
      ▼              ▼          ▼          ▼              ▼
 Research       Research     Memory     Teaching      MCP Server
 Explainer        Gap         Agent        Agent
                               │
                               ▼
                 ChromaDB / SQLite Memory
                               │
                               ▼
                    Security Processing
```

---

# 🤖 Agent Ecosystem

| Agent | Responsibility |
|-------|----------------|
| 🧭 Coordinator | Orchestrates the complete workflow |
| 📄 Paper Reader | Extracts structured content from PDFs |
| 🧑‍🏫 Research Explainer | Creates summaries for different audiences |
| ✅ Fact Checker | Verifies research claims |
| 🔗 Related Work | Discovers scholarly publications |
| 📚 Literature Review | Builds comprehensive reviews |
| 💡 Research Gap | Finds limitations and opportunities |
| 🎓 Teaching Agent | Generates educational content |
| 🎤 Presentation Agent | Creates presentation materials |
| 🧠 Memory Agent | Stores and retrieves research history |

---

# 🚀 Why Multi-Agent AI?

Large language models are powerful, but expecting a single model to simultaneously:

- Read research papers
- Verify scientific claims
- Search scholarly databases
- Build literature reviews
- Generate presentations
- Maintain long-term memory

often produces inconsistent results.

ResearchOS AI solves this by dividing responsibilities among specialized agents coordinated through a central workflow.

Benefits include:

- Better reasoning
- Easier debugging
- Transparent workflows
- Modular architecture
- Independent testing
- Future scalability

---
# 🔌 MCP Server Integration

ResearchOS AI includes a dedicated MCP (Model Context Protocol) server that enables agents to access external research tools through a unified interface.

The MCP server is implemented using FastAPI and acts as the bridge between AI agents and scholarly data sources.

---

## Available MCP Tools

| Tool | Description |
|--------|-------------|
| `search_arxiv` | Search research papers on arXiv |
| `search_semantic_scholar` | Discover related scholarly work |
| `retrieve_citation_graph` | Explore citation networks |
| `verify_research_claim` | Validate research claims |
| `compare_papers` | Compare methodologies and results |
| `generate_bibliography` | Generate APA, MLA, and BibTeX citations |
| `extract_metadata` | Extract paper metadata |

---

## MCP Architecture

```text
                    AI Agents
                         │
                         ▼
                MCP Tool Interface
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     arXiv      Semantic Scholar     Citation Graph
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                   Structured Data
                         │
                         ▼
                     AI Agents
```

---

## Graceful Offline Mode

ResearchOS AI was designed to run even when external APIs are unavailable.

If a tool cannot access external services due to:

- Network issues
- API downtime
- Rate limiting
- Missing credentials

the system automatically falls back to deterministic mock responses.

This ensures:

- Reliable demos
- Offline operation
- Reproducible testing
- Kaggle-friendly execution

---

# 🔄 Agent Workflow

Every agent follows the same structured lifecycle.

```text
PLAN
  ↓
EXECUTE
  ↓
VERIFY
  ↓
REFLECT
  ↓
RESPOND
```

---

## PLAN

The agent determines:

- What task must be completed
- What resources are required
- Which tools should be called

---

## EXECUTE

The agent performs its primary responsibility.

Examples:

- Reading PDFs
- Searching papers
- Generating summaries
- Verifying claims

---

## VERIFY

Results are validated before being returned.

Checks include:

- Missing information
- Confidence thresholds
- Tool output consistency

---

## REFLECT

The agent evaluates:

- Response quality
- Potential errors
- Missing context
- Opportunities for improvement

---

## RESPOND

The final structured output is returned to the Coordinator Agent.

---

# 🧩 Shared Agent Skills

To avoid duplicated logic, agents share reusable skills.

## Research Skills

Used by:

- Related Work Agent
- Literature Review Agent
- Fact Checker Agent

Capabilities:

- Scholarly search
- Citation retrieval
- Research comparison

---

## Summarization Skills

Used by:

- Research Explainer Agent
- Literature Review Agent

Capabilities:

- Executive summaries
- Technical summaries
- Beginner explanations
- ELI5 generation

---

## Teaching Skills

Used by:

- Teaching Agent

Capabilities:

- Flashcards
- MCQs
- Study guides
- Educational content

---

## Presentation Skills

Used by:

- Presentation Agent

Capabilities:

- Slide generation
- Speaker notes
- Research pitches
- Poster summaries

---

## Verification Skills

Used by:

- Fact Checker Agent

Capabilities:

- Claim extraction
- Evidence retrieval
- Confidence scoring

---

# 🧠 Memory System

ResearchOS AI includes a persistent memory layer that allows agents to remember previous research sessions.

---

## Memory Capabilities

The system can:

- Store summaries
- Store research interests
- Store generated outputs
- Retrieve previous conversations
- Search past research semantically
- Maintain long-term context

---

## Backend Selection

ResearchOS AI automatically selects the best available backend.

### ChromaDB

When installed:

- Embedding-based retrieval
- Semantic similarity search
- Vector memory

---

### SQLite Fallback

Always available:

- Lightweight
- No dependencies
- Keyword-ranked retrieval
- Offline compatible

---

## Memory Architecture

```text
                     Memory Agent
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
       ChromaDB                    SQLite Fallback
            │                             │
            └──────────────┬──────────────┘
                           ▼
                  Research History
```

---

## Stored Information

Examples include:

- Paper summaries
- Generated reviews
- Fact-check results
- Research interests
- User preferences
- Agent observations

---

# 🔒 Security

ResearchOS AI uses a defense-in-depth security architecture.

Every input and output passes through multiple protection layers.

---

## Prompt Injection Defense

Detects attempts such as:

```text
Ignore previous instructions
Reveal system prompt
Bypass security checks
```

Suspicious content is treated as data rather than executable instructions.

---

## PDF Validation

Uploaded files are verified using:

- Extension checks
- MIME validation
- Magic-byte inspection
- File size limits

This prevents malformed uploads from entering the pipeline.

---

## PII Protection

Sensitive information is automatically masked before logging.

Supported detection:

- Email addresses
- Phone numbers
- Credit cards
- IP addresses
- Social security numbers

Example:

Input:

```text
john@example.com
```

Logged:

```text
[EMAIL_REDACTED]
```

---

## Safe Logging

Global logging filters automatically remove:

- API keys
- Authentication tokens
- Personal information
- Secrets

before records are written.

---

## Human Verification

Every generated research output includes a reminder:

> Research findings should be independently verified.

ResearchOS AI assists researchers—it does not replace scientific review.

---

# 🛠️ Tech Stack

## Frontend

| Technology | Purpose |
|------------|----------|
| Streamlit | Interactive UI |
| HTML/CSS | Styling |
| Mermaid | Architecture diagrams |

---

## Backend

| Technology | Purpose |
|------------|----------|
| Python 3.11 | Core language |
| FastAPI | MCP server |
| SQLite | Local persistence |
| ChromaDB | Vector memory |

---

## AI & Research

| Technology | Purpose |
|------------|----------|
| Gemini | LLM backend |
| Multi-Agent Framework | Agent orchestration |
| EventBus | Agent communication |
| MCP | Tool interoperability |

---

## Deployment

| Technology | Purpose |
|------------|----------|
| Docker | Containerization |
| Streamlit Cloud | Hosted deployment |
| Google Cloud Run | Serverless deployment |
| Hugging Face Spaces | Public demos |

---

# 📁 Project Structure

```text
ResearchOS-AI/
│
├── app.py
├── requirements.txt
├── README.md
├── .env.example
│
├── agents/
│   ├── coordinator.py
│   ├── paper_reader.py
│   ├── research_explainer.py
│   ├── fact_checker.py
│   ├── related_work.py
│   ├── literature_review.py
│   ├── research_gap.py
│   ├── quiz_teaching.py
│   ├── presentation.py
│   └── memory_agent.py
│
├── skills/
│   ├── summarization.py
│   ├── research.py
│   ├── teaching.py
│   ├── presentation.py
│   └── fact_verification.py
│
├── mcp/
│   ├── server.py
│   └── tools.py
│
├── memory/
│   └── memory_store.py
│
├── security/
│   ├── prompt_injection.py
│   ├── validation.py
│   ├── pii.py
│   └── safe_logging.py
│
├── diagrams/
│
├── deployment/
│
├── tests/
│
└── docs/
```

---
# 🚀 Getting Started

Follow these steps to run ResearchOS AI locally.

---

## Prerequisites

Before starting, ensure you have:

- Python 3.11 or later
- pip
- Git
- Virtual Environment (recommended)

Optional:

- Docker Desktop
- ChromaDB (for vector memory)

---

## Clone the Repository

```bash
git clone https://github.com/yourusername/researchos-ai.git

cd researchos-ai
```

---

## Create a Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file.

Example:

```env
GOOGLE_API_KEY=your_api_key

MEMORY_BACKEND=chromadb

MEMORY_DB_PATH=research_memory.db

LOG_LEVEL=INFO
```

---

## Run the Application

Start the Streamlit application.

```bash
streamlit run app.py
```

Open:

```
http://localhost:8501
```

---

## Start MCP Server

In another terminal:

```bash
uvicorn mcp.server:app --reload --port 8080
```

API Documentation:

```
http://localhost:8080/docs
```

---

# 💻 Using ResearchOS AI

Using the application is simple.

### Step 1

Upload one or more research papers.

Supported formats:

- PDF

---

### Step 2

Select a task.

Examples:

- Summarize Paper
- Explain Research
- Verify Claims
- Literature Review
- Related Work
- Presentation
- Flashcards
- Research Gaps

---

### Step 3

The Coordinator Agent assigns work to specialized agents.

Each agent completes its task independently before returning results.

---

### Step 4

Receive a structured research report containing:

- Summary
- Key Findings
- Related Research
- Citations
- Verification Results
- Presentation Outline
- Study Material

---

# 🧪 Testing

Run the complete test suite.

```bash
pytest
```

Verbose mode:

```bash
pytest -v
```

Generate coverage report:

```bash
pytest --cov
```

---

## Test Categories

| Test | Description |
|--------|-------------|
| Agent Tests | Individual AI agent behavior |
| MCP Tests | Tool integrations |
| Memory Tests | Storage & retrieval |
| Security Tests | Prompt injection & validation |
| Integration Tests | Complete workflows |
| UI Tests | Streamlit interface |

---

# 📸 Screenshots

## Home Page

Replace with your screenshot.

```markdown
![Home](images/home.png)
```

---

## Upload Papers

```markdown
![Upload](images/upload.png)
```

---

## Research Summary

```markdown
![Summary](images/summary.png)
```

---

## Literature Review

```markdown
![Review](images/review.png)
```

---

## Presentation Generator

```markdown
![Presentation](images/presentation.png)
```

---

# 🐳 Docker

Build the container.

```bash
docker build -t researchos-ai .
```

Run:

```bash
docker run -p 8501:8501 researchos-ai
```

---

# ☁️ Deployment

ResearchOS AI can be deployed on multiple platforms.

| Platform | Status |
|------------|---------|
| Docker | ✅ |
| Streamlit Cloud | ✅ |
| Hugging Face Spaces | ✅ |
| Google Cloud Run | ✅ |
| Railway | ✅ |
| Render | ✅ |

---

# 📈 Future Roadmap

ResearchOS AI continues to evolve.

Planned improvements include:

- Live arXiv synchronization
- Semantic Scholar API integration
- Citation graph visualization
- PDF annotation
- OCR support
- Research recommendation engine
- AI-powered writing assistant
- Multi-user collaboration
- Voice interaction
- Mobile support
- Knowledge graph generation
- Automatic paper comparison dashboard

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository.

2. Create a feature branch.

```bash
git checkout -b feature/new-feature
```

3. Commit your changes.

```bash
git commit -m "Add awesome feature"
```

4. Push your branch.

```bash
git push origin feature/new-feature
```

5. Open a Pull Request.

---

# 📄 License

This project is licensed under the **MIT License**.

See the **LICENSE** file for more information.

---

# 🙏 Acknowledgements

Special thanks to:

- Kaggle AI Agents Capstone
- Google AI
- Streamlit
- FastAPI
- ChromaDB
- arXiv
- Semantic Scholar
- Python Community
- Open Source Contributors

---

# ⭐ Support

If you found this project useful:

- ⭐ Star the repository
- 🍴 Fork the project
- 🐛 Report issues
- 💡 Suggest improvements
- 📢 Share with fellow researchers

Your support helps improve ResearchOS AI for everyone.

---

<div align="center">

# 🔬 ResearchOS AI

### Building the Future of AI-Assisted Research

**Read Smarter • Research Faster • Discover More**

Made with ❤️ using **Python**, **FastAPI**, **Streamlit**, **ChromaDB**, and **Multi-Agent AI**.

⭐ **If you like this project, don't forget to star the repository!**

</div>
