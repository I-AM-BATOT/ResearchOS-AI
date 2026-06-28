# ResearchOS AI
### Multi-Agent Research Operating System

*A Kaggle AI Agents Intensive — Vibe Coding Capstone submission*

---

## Problem

Reading research papers carefully is slow. Reading them *critically* — checking
whether claims hold up, finding what else has been written on the topic,
spotting gaps worth pursuing — is slower still. A working researcher or
student doing a literature review might spend days on work that follows a
fairly repeatable pattern: read, summarize, verify, contextualize, synthesize,
teach, present. That repeatable pattern is exactly what a coordinated team of
specialized agents is good at automating, while leaving the actual judgment
calls to the human.

## Motivation

I wanted to build something that didn't just wrap an LLM in a chat box and
call it an "agent." The brief asked for a *system*: multiple agents with
distinct responsibilities, real communication between them, tools backed by
live data, persistent memory, and safety guardrails that hold up under
adversarial input. ResearchOS AI is my attempt at building that system end to
end — and, importantly, building it so it's genuinely runnable and testable
by a grader who may have no API key and no guaranteed network access. Every
external dependency in this project has a graceful, visible offline fallback,
which is a non-negotiable design constraint from line one, not an
afterthought.

## Solution

Upload one or more PDFs. A **Coordinator Agent** plans a workflow and
delegates across nine specialist agents:

- **Paper Reader** — extracts text and segments it into Abstract, Introduction,
  Methods, Results, Discussion, Conclusion.
- **Research Explainer** — four summaries: Executive, Technical, Beginner, ELI5.
- **Fact Checker** — extracts checkable claims and verifies them against
  scholarly sources, returning Verified / Questionable / Needs Review with a
  confidence score.
- **Related Work** — discovers related papers, prior work, and competing
  methods via arXiv and Semantic Scholar.
- **Research Gap** — surfaces weaknesses, limitations, missing experiments,
  and novel research ideas.
- **Literature Review** — synthesizes multiple papers into trends, a
  comparative analysis, and a state-of-the-art summary.
- **Quiz & Teaching** — flashcards, MCQs, short-answer questions, and a study
  guide at Easy/Medium/Hard difficulty.
- **Presentation** — a slide outline with speaker notes, a conference talk
  script, and a poster summary.
- **Memory** — persistent, semantically searchable storage of every paper,
  summary, and observation across the session.

A Streamlit app exposes eleven pages — Home, Research Workspace, Paper
Analysis, Related Work Explorer, Literature Review Builder, Fact Checking
Center, Learning Center, Presentation Builder, Memory Dashboard, Security
Dashboard, and Architecture — each surfacing a different slice of the same
underlying agent run.

## Architecture

The system is layered: **UI → Agents → Skills → MCP Tools → External APIs**,
with **Memory** and **Security** cutting across every layer.

Every agent subclasses a shared `BaseAgent` that implements the required
**Plan → Execute → Verify → Reflect → Respond** loop, and every stage
transition — including explicit agent-to-agent handoffs like "Paper Reader
handing off to Fact Checker" — is published to a shared event bus. The
Architecture page in the app renders this as a live trace: it is the literal
communication log from the run that just happened, not a pre-scripted
animation. That distinction mattered a lot to me — it's easy to fake "agent
collaboration" with a static diagram, and I wanted the judging panel to be
able to verify the collaboration is real by running the app themselves.

The `BaseAgent` lifecycle is deliberately shaped like Google ADK's agent/
runner pattern (an `LlmAgent` driven by a `Runner`), with two additions: an
explicit, code-level `verify()` step that sanity-checks an agent's output
before anything downstream trusts it, and a `reflect()` step that produces a
structured self-critique (reasoning, confidence, quality notes) which gets
written to memory. This makes the planning-and-reflection requirement a real
architectural feature rather than a single LLM call asked to "reflect on your
answer."

## Agent design

Each agent is intentionally narrow. The Coordinator doesn't know *how* to
verify a claim or summarize a paper — it knows *who* to ask and how to
sequence the asks, then aggregates results into one report. This separation
is what lets the system add a tenth or eleventh agent later without touching
the others: register it with the Coordinator, give it a `plan`/`execute`
implementation, and wire in a handoff call.

Reusable logic that multiple agents need (summarization, scholarly search,
quiz generation, presentation building, claim verification) lives in a
separate **Skills** layer rather than being duplicated per agent — this
mirrors the "Agent Skills" requirement directly and kept the codebase from
accumulating copy-pasted prompt-assembly code.

## MCP integration

`mcp/server.py` is a FastAPI application exposing seven tools required by the
brief — `search_arxiv`, `search_semantic_scholar`, `retrieve_citation_graph`,
`verify_research_claim`, `compare_papers`, `generate_bibliography`, and
`extract_metadata` — both through a generic `/mcp/call` dispatcher (so any
MCP-style client can use them) and through convenience REST routes with
auto-generated Swagger docs.

`search_arxiv` and `search_semantic_scholar` hit the real public arXiv and
Semantic Scholar APIs. `retrieve_citation_graph` resolves a paper on Semantic
Scholar and walks its citation/reference edges. Crucially, every tool call is
wrapped so that a network failure, rate limit, or API error doesn't crash the
agent pipeline — it falls back to clearly labeled (`"mock": true`)
placeholder data instead. I validated this directly during development: in a
network-isolated sandbox, every live call returned a `403`/connection error
from the egress layer, and every tool correctly degraded without breaking a
single downstream agent. That's not a hypothetical resilience story — it's
the exact failure path the system hit and handled while I was building it.

## Memory

`memory/memory_store.py` exposes one interface — store, retrieve, update,
delete, semantic search, list — over two interchangeable backends: ChromaDB
when available (true embedding-based semantic search) and a SQLite-backed
keyword-overlap search as an automatic, zero-extra-dependency fallback. The
Memory Agent uses this to persist paper summaries, research interests,
generated outputs, and every other agent's reflections, giving later sessions
context awareness instead of starting from zero each time. The Memory
Dashboard page makes this inspectable and searchable rather than a black box.

## Security

Security is treated as a layer that wraps the agent pipeline, not a filter
bolted onto the chat box. Four mechanisms work together:

1. **Prompt injection defense** — a heuristic pattern scanner runs on every
   chat message *and* on every PDF's extracted text (a paper's body is just
   as much an LLM-facing attack surface as a typed message). Flagged content
   isn't blocked outright — it's wrapped as explicitly inert "untrusted
   content" before being handed to the LLM, so a paper that happens to quote
   adversarial text can still be summarized safely.
2. **PDF validation** — extension, magic-byte, and size checks reject
   corrupt, oversized, or non-PDF uploads before they ever reach the parser.
3. **PII protection + safe logging** — emails, phone numbers, SSNs, credit
   cards, and IP addresses are masked via a dedicated module, and a global
   logging filter additionally scrubs API keys and bearer tokens from every
   log record application-wide, not just in the modules I remembered to guard.
4. **Human-in-the-loop safety** — every research output, without exception,
   carries an explicit "Research findings should be independently verified"
   notice. The system is positioned as a research *assistant*, not an
   authority.

The Security Dashboard page exposes live versions of the injection scanner
and PII masker so reviewers can test them directly with their own input,
rather than taking the claim on faith.

## Reflection workflow

The required Plan → Execute → Verify → Reflect → Respond loop is implemented
once, in `BaseAgent.run()`, and inherited by every agent rather than
reimplemented per agent. `verify()` is code-level (e.g., the Fact Checker
flags itself if it found zero checkable claims; the Related Work agent fails
verification if it found no related papers at all), which keeps the
verification step honest and cheap rather than asking the LLM to grade its
own homework. `reflect()` produces a structured `AgentReflection` (reasoning,
confidence score, quality notes) that's written to memory, so the system
accumulates a record of its own performance over time, not just of the
papers it analyzed.

## Results

Across a development pass that included an arXiv-formatted sample PDF
generated for testing, the full nine-agent pipeline runs end-to-end: PDF in,
aggregated report out, with every stage's confidence score and warnings
surfaced to the UI. The test suite (`pytest tests/`) exercises agent routing,
the Fact Checker, Related Work discovery, Literature Review synthesis,
Presentation generation, real PDF extraction and section segmentation, all
seven MCP tools (including their mock-fallback branch), and the security
layer's injection/PII/validation logic — all forced into deterministic mock
mode so the suite needs no API key and no network access to pass.

## Impact

The honest claim here isn't "this replaces a researcher's judgment" — it's
that ResearchOS AI removes the *mechanical* front-loaded work of engaging
with a paper (extraction, multi-level explanation, a first pass at claim
verification, a first pass at related-work discovery) so a human's limited
attention goes toward the parts that actually require it: deciding whether a
claim's supporting evidence is convincing, deciding which research gap is
worth pursuing, deciding what to say in the actual conference talk. The
human-in-the-loop notice on every output is there because that boundary
matters, not as a liability disclaimer.

## Future work

- Swap the direct Gemini call in `core/llm_client.py` for a real Google ADK
  `LlmAgent` + `Runner` + `SessionService` deployment — the agent shape was
  designed specifically to make this a drop-in change.
- Run independent agents (Explainer/Fact Checker, Quiz/Presentation) truly in
  parallel via `asyncio.gather` instead of sequentially, which would cut
  latency meaningfully without changing the communication model.
- Add OCR fallback for scanned, image-only PDFs with no extractable text layer.
- Multi-user persistent memory with authentication, replacing per-session
  Streamlit state.
- A real interactive citation-graph visualization instead of the current
  list-based related-work view.

## Lessons learned

Designing mock-mode as a first-class feature rather than a fallback turned
out to be the single highest-leverage decision in the project: it made the
whole system runnable and testable with zero configuration, and it forced
every external call site to handle failure explicitly from the start instead
of after a demo broke. Sharing one agent lifecycle across ten agents paid for
itself the moment I had more than three or four agents — verification,
reflection, and event-bus logging were each written exactly once. And
treating extracted PDF text as untrusted input, on equal footing with chat
messages, closed a security gap I hadn't initially considered: a paper's
body is just as much an attack surface as anything a user types.

## Track justification

ResearchOS AI was submitted to the **Agents for Good** track. The track
description explicitly calls out "advancing education" as in scope, and
that's the core of what this project does: it lowers the barrier to
engaging critically with research for students, early-career researchers,
and anyone trying to learn from papers outside their home field — turning a
slow, expert-gated process (reading, verifying, contextualizing, teaching)
into something a non-expert can use as a credible starting point.

Against the course's key concepts, this submission demonstrates at least
three directly in code: an **MCP Server** built from scratch in FastAPI
exposing seven tools backed by live scholarly data sources (arXiv,
Semantic Scholar); a defense-in-depth **security** layer covering prompt
injection, PII masking, input validation, and safe logging; and
**deployability** across Docker, Streamlit Cloud, Google Cloud Run, and
Hugging Face Spaces, each with working configuration and instructions.
It also implements a coordinated ten-agent **multi-agent system** with
genuine, logged agent-to-agent communication and a shared
plan-execute-verify-reflect lifecycle — built as a custom framework rather
than on the literal `google-adk` package, since the project was developed
through conversational pair-programming rather than Google's Antigravity
IDE. The agent shape was deliberately kept close to ADK 2.0's
graph-style workflow model (see the note in `core/llm_client.py`) so a
real ADK 2.0 migration is a scoped follow-up rather than a rewrite.
