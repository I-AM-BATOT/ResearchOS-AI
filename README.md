# 🔬 ResearchOS AI

### Multi-Agent Research Operating System

**Built for Kaggle's "AI Agents: Intensive Vibe Coding Capstone Project"**

ResearchOS AI turns a folder of research PDFs into a fully-staffed AI research team:
it reads papers, explains them at four levels of depth, fact-checks their claims,
discovers related work, builds literature reviews, finds research gaps, generates
study materials, and produces presentations — all coordinated by a multi-agent
system with real agent-to-agent communication, persistent memory, an MCP tool
server, and a defense-in-depth security layer.

---

## Table of contents
- [Problem](#problem)
- [Solution](#solution)
- [Architecture](#architecture)
- [Agent roles](#agent-roles)
- [MCP integration](#mcp-integration)
- [Memory](#memory)
- [Security](#security)
- [Installation](#installation)
- [Running the app](#running-the-app)
- [Deployment](#deployment)
- [Testing](#testing)
- [Screenshots](#screenshots)
- [Future work](#future-work)
- [Lessons learned](#lessons-learned)

---

## Problem

Researchers spend countless hours reading papers, understanding methodologies,
comparing studies, verifying claims, building literature reviews, creating
presentations, and discovering research gaps. This is slow, repetitive, and
doesn't scale with the volume of papers published every year.

## Solution

Upload one or more papers. ResearchOS AI automatically:

- Understands the paper (section-aware extraction)
- Explains it at 4 levels (executive / technical / beginner / ELI5)
- Verifies its claims against scholarly sources
- Finds related work, competing methods, and citation graphs
- Builds a literature review across multiple papers
- Identifies weaknesses, limitations, and novel research directions
- Generates flashcards, MCQs, and study guides
- Builds a slide deck, speaker notes, conference script, and poster summary
- Remembers everything for future, context-aware sessions

Every step is performed by a dedicated agent running a
**PLAN → EXECUTE → VERIFY → REFLECT → RESPOND** loop, with real
agent-to-agent handoffs visible in the **Architecture** page.

## Architecture

```
Streamlit UI  →  Coordinator Agent  →  9 specialist agents  →  Skills layer  →  MCP Server (FastAPI)  →  arXiv / Semantic Scholar
                         │                                                            │
                         └────────────────────→ Memory Agent → ChromaDB / SQLite ←─────┘
                         │
                         └────────────────────→ Security layer (every input/output passes through it)
```

Full interactive diagrams (Mermaid) live in [`diagrams/`](diagrams/) and render
live in the app's **Architecture** page:

| Diagram | File |
|---|---|
| System Architecture | `diagrams/system_architecture.mmd` |
| Agent Collaboration Flow | `diagrams/agent_collaboration.mmd` |
| MCP Tool Architecture | `diagrams/mcp_architecture.mmd` |
| Memory Architecture | `diagrams/memory_architecture.mmd` |
| Security Architecture | `diagrams/security_architecture.mmd` |
| Research Pipeline | `diagrams/research_pipeline.mmd` |

## Agent roles

| Agent | File | Responsibility |
|---|---|---|
| 🧭 Coordinator | `agents/coordinator.py` | Plans the workflow, delegates to every specialist agent, aggregates the final report |
| 📄 Paper Reader | `agents/paper_reader.py` | Extracts PDF text, segments Abstract/Intro/Methods/Results/Discussion/Conclusion |
| 🧑‍🏫 Research Explainer | `agents/research_explainer.py` | Executive / Technical / Beginner / ELI5 summaries |
| ✅ Fact Checker | `agents/fact_checker.py` | Extracts claims, verifies them, outputs status + confidence |
| 🔗 Related Work | `agents/related_work.py` | arXiv + Semantic Scholar discovery, builds a Related Research Map |
| 📚 Literature Review | `agents/literature_review.py` | Synthesizes multiple papers into trends, comparisons, SOTA summary |
| 🧩 Research Gap | `agents/research_gap.py` | Weaknesses, limitations, missing experiments, novel ideas |
| 🎓 Quiz & Teaching | `agents/quiz_teaching.py` | Flashcards, MCQs, short answer, study guide at 3 difficulty levels |
| 🖼️ Presentation | `agents/presentation.py` | Slide outline, speaker notes, conference talk, poster summary |
| 🧠 Memory | `agents/memory_agent.py` | Store / retrieve / update / delete + semantic search over research history |

Every agent inherits `agents/base.py:BaseAgent`, which implements the shared
`PLAN → EXECUTE → VERIFY → REFLECT → RESPOND` lifecycle and publishes every
stage transition to a shared `EventBus` (`core/event_bus.py`) — this is what
powers the live agent-collaboration trace in the UI's Architecture page; it is
the actual communication log, not a scripted animation.

Reusable **Agent Skills** (`skills/`) are shared across agents:
`summarization.py`, `research.py`, `teaching.py`, `presentation.py`,
`fact_verification.py`.

## MCP integration

`mcp/server.py` is a FastAPI app exposing 7 tools, both as a generic
`/mcp/call` dispatcher and as convenience GET routes:

| Tool | Purpose |
|---|---|
| `search_arxiv` | Search arXiv (title, authors, abstract, link, date) |
| `search_semantic_scholar` | Related work + citation influence |
| `retrieve_citation_graph` | Citing / referenced paper network |
| `verify_research_claim` | Cross-reference a claim against scholarly sources |
| `compare_papers` | Structural diff of methods/results between two papers |
| `generate_bibliography` | APA / MLA / BibTeX reference generation |
| `extract_metadata` | Title / authors / keywords / year from a PDF |

Run standalone:
```bash
uvicorn mcp.server:app --port 8765
# Swagger docs at http://localhost:8765/docs
```

**Live research integration**: tools call the real arXiv and Semantic Scholar
public APIs. If the network is unavailable, rate-limited, or the call errors
out, every tool gracefully degrades to clearly-labeled (`"mock": true`)
deterministic placeholder data instead of crashing the pipeline — this was
verified during development in a fully network-isolated sandbox, where every
tool correctly fell back without breaking the agent pipeline.

## Memory

`memory/memory_store.py` implements persistent memory with automatic backend
selection:
- **ChromaDB** (if installed) → true embedding-based semantic search
- **SQLite fallback** (always available) → keyword-overlap ranked search

Both backends implement the same interface: store, retrieve, update, delete,
semantic search, and `list_all`. The **Memory Dashboard** page lets you browse,
search, and delete stored memories (paper summaries, research interests,
generated outputs, agent observations).

## Security

| Layer | File | What it does |
|---|---|---|
| Prompt Injection Defense | `security/prompt_injection.py` | Heuristic detection of override/extraction/jailbreak patterns in chat + PDF text; sandboxes suspicious content as inert data rather than instructions |
| PDF Validation | `security/validation.py` | Rejects corrupt, oversized, or non-PDF uploads via extension + magic-byte + size checks |
| PII Protection | `security/pii.py` | Masks emails, phone numbers, SSNs, credit cards, IPs before logging |
| Safe Logging | `security/safe_logging.py` | Global logging filter scrubs API keys/tokens + PII from every log record |
| Input Validation | `security/validation.py` | Schema/length validation for uploads, chat queries, and MCP tool requests |
| Human-in-the-loop | every agent output | "Research findings should be independently verified" notice on every result |

Try the live detectors yourself in the **Security Dashboard** page.

## Installation

Requires **Python 3.11+**.

```bash
git clone <this-repo>
cd ResearchOS-AI
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # optional — leave blank to run in MOCK mode
```

To enable live Gemini calls and full agent intelligence, set `GEMINI_API_KEY`
in `.env`. **The platform runs fully end-to-end with zero configuration** —
no API keys required — using a deterministic mock LLM backend
(`core/llm_client.py`) so graders/reviewers can run the whole pipeline offline.

## Running the app

```bash
streamlit run app.py
```
Then open http://localhost:8501.

Optionally run the MCP server standalone (useful for testing tools directly
or connecting other MCP clients):
```bash
uvicorn mcp.server:app --port 8765
```

Or run everything with Docker Compose:
```bash
docker compose -f deployment/docker-compose.yml up --build
```

## Deployment

Deployment guides are provided for:
- **Docker** — `deployment/Dockerfile`, `deployment/Dockerfile.mcp`, `deployment/docker-compose.yml`
- **Streamlit Community Cloud** — `deployment/STREAMLIT_CLOUD.md`
- **Google Cloud Run** — `deployment/CLOUD_RUN.md`
- **Hugging Face Spaces** — `deployment/HUGGINGFACE_SPACES.md`

## Testing

```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

Test coverage includes: agent routing/orchestration, memory (store/retrieve/
update/delete/search), fact checking, related work discovery, prompt
injection detection, PII masking, PDF extraction (against a real generated
PDF), all 7 MCP tools (including the offline mock-fallback path),
presentation generation, and literature review generation. Tests force
MOCK mode (`FORCE_MOCK_MODE=true`) so they run deterministically with zero
API keys or network access required.

## Screenshots

See the app live — every page listed below is reachable from the sidebar:
Home, Research Workspace, Paper Analysis, Related Work Explorer, Literature
Review Builder, Fact Checking Center, Learning Center, Presentation Builder,
Memory Dashboard, Security Dashboard, Architecture.

## UI design

The interface uses a small, deliberate icon set (Google Material Symbols via
Streamlit's native `:material/icon_name:` support — see `core/ui_theme.py`)
rather than emoji: one icon per page, tab, or action, not one per line of
text. A shared theme (`apply_theme()`, called once per page) adds a custom
color palette, a fade-in on page load, hover-lift on buttons/cards/metrics,
an animated tab underline, and a pill-shaped status-badge component
(`badge()`) used for verification status, agent mode, and security events
instead of colored emoji circles.

## Future work

- Migrate to a real Google ADK 2.0 deployment — this project does not
  currently use the literal `google-adk` package. ADK 2.0 is a graph-based
  framework (nodes, edges, a root Workflow, scaffolded via `agents-cli`);
  migrating would mean expressing the Coordinator's handoff sequence as an
  explicit ADK Workflow graph rather than a line-for-line substitution. See
  the honest note in `core/llm_client.py` for what that scoped follow-up
  would actually involve.
- True parallel agent execution (the Coordinator currently runs agents
  sequentially for log-trace clarity; an `asyncio.gather` version would cut
  latency significantly).
- Persistent multi-user memory with auth, instead of per-session Streamlit state.
- OCR fallback (`pytesseract`, already a transitive dependency of several
  PDF libraries) for scanned/image-only PDFs that have no extractable text layer.
- A real citation-graph visualization (e.g. via `pyvis` or `d3.js`) instead of
  the current list-based UI.

## Lessons learned

- **Mock-mode-by-default is a feature, not a fallback.** Designing every
  external dependency (LLM calls, arXiv/Semantic Scholar HTTP calls,
  ChromaDB) with a graceful, clearly-labeled offline degradation path made
  the whole system testable, demoable, and gradeable without requiring
  reviewers to provision API keys or guarantee network access — and it
  surfaced real reliability requirements (timeouts, error handling) earlier
  than a "happy path only" implementation would have.
- **A shared agent lifecycle (`BaseAgent`) pays for itself immediately** once
  you have more than 3-4 agents: verification and reflection logic, event-bus
  publishing, and error handling only had to be written once.
- **Security has to run on extracted PDF text, not just chat input** — a
  paper's body text is just as much an LLM-facing attack surface as a typed
  message, so the Paper Reader Agent runs the same injection scan and PII
  mask used on chat messages.

## Track justification

This project was submitted to the **Agents for Good** track — the track
description explicitly names "advancing education" as in scope, and that's
the core of what ResearchOS AI does: lowering the barrier to engaging
critically with research for students and non-experts.

Against the course's key concepts, it demonstrates at least three directly
in code: a from-scratch **MCP server** with 7 live-data tools; a
defense-in-depth **security** layer (prompt injection, PII, validation, safe
logging); and **deployability** across Docker, Streamlit Cloud, Cloud Run,
and Hugging Face Spaces. It also implements a coordinated 10-agent
**multi-agent system** with real agent-to-agent communication and a shared
planning/reflection workflow — built as a custom framework rather than the
literal `google-adk` package; see the honest note in `core/llm_client.py`
for what a real ADK 2.0 migration would involve.
#   R e s e a r c h O S - A I  
 