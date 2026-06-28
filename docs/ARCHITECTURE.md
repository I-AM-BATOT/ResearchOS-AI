# Architecture Deep Dive

This document expands on the README's architecture section with module-level
detail. See `diagrams/*.mmd` for the visual versions (rendered live in the
app's Architecture page).

## Layered design

```
┌─────────────────────────────────────────────────────────────────┐
│ Streamlit UI (app.py + pages/)                                  │
│   Home · Workspace · Analysis · Related Work · Lit Review ·     │
│   Fact Checking · Learning · Presentation · Memory · Security · │
│   Architecture                                                  │
└───────────────────────────┬───────────────────────────────────--┘
                            │
┌───────────────────────────▼───────────────────────────────────--┐
│ Agent Layer (agents/)                                           │
│   CoordinatorAgent orchestrates 9 specialist agents, all         │
│   subclassing BaseAgent's PLAN→EXECUTE→VERIFY→REFLECT→RESPOND    │
└───────────────────────────┬───────────────────────────────────--┘
                            │
┌───────────────────────────▼───────────────────────────────────--┐
│ Skills Layer (skills/)                                          │
│   Stateless reusable functions: summarization, research,        │
│   teaching, presentation, fact_verification                     │
└───────────────────────────┬───────────────────────────────────--┘
                            │
┌───────────────────────────▼───────────────────────────────────--┐
│ Tool Layer (mcp/)                                                │
│   tools.py = plain Python callables (used in-process)           │
│   server.py = FastAPI HTTP wrapper (used by external clients)   │
└───────────────────────────┬───────────────────────────────────--┘
                            │
┌───────────────────────────▼───────────────────────────────────--┐
│ External services: arXiv API, Semantic Scholar API, Gemini      │
│ (every call has a graceful offline mock fallback)                │
└───────────────────────────────────────────────────────────────--┘

Cross-cutting layers (touch every layer above):
- core/ — config, LLM client, shared Pydantic models, event bus
- memory/ — persistent store (ChromaDB / SQLite)
- security/ — injection defense, PII masking, validation, safe logging
```

## Why this shape

**BaseAgent mirrors Google ADK's agent/runner lifecycle on purpose.** Google
ADK structures an agent as an `LlmAgent` run through a `Runner` with a
`SessionService`. This project's `BaseAgent.run()` performs the same
plan → act → respond arc, with two additions required by the competition
brief: an explicit `verify()` step (cheap, code-based sanity checks before
trusting an LLM's output) and a `reflect()` step (a structured self-critique
stored to memory). Swapping `core/llm_client.py`'s direct
`google.generativeai` call for a real ADK `Runner.run()` call is therefore a
localized change, not a rewrite of the agent layer.

**Every external dependency has an offline mock fallback.** LLM calls
(`core/llm_client.py`), arXiv/Semantic Scholar HTTP calls (`mcp/tools.py`),
and the memory backend (`memory/memory_store.py`, ChromaDB → SQLite) all
degrade gracefully and visibly (`"mock": true` / "[MOCK]" labels) instead of
raising. This was validated directly: in the development sandbox (no network
egress), every MCP tool call returned a real `403`/connection error from the
live API and correctly fell through to mock data without the pipeline
crashing — the exact failure mode a grading environment with restricted
network access might also hit.

**Security wraps the agent layer, not just the chat box.** Extracted PDF text
goes through the same `scan_text()` / `mask_pii()` path as user chat
messages, because a malicious or adversarially-crafted PDF is just as much an
LLM-facing attack surface as a typed prompt.

## Data flow for "Full Analysis"

1. User uploads a PDF in **Research Workspace**.
2. `security.validation.validate_pdf_upload` checks extension, magic bytes, size.
3. `CoordinatorAgent._full_analysis()` runs:
   `PaperReader → {ResearchExplainer, FactChecker} → RelatedWork → ResearchGap
   → {QuizTeaching, Presentation} → MemoryAgent (store)`.
4. Every hop calls `agent.handoff(...)` (logs a PLAN-stage message) then
   `agent.run(...)` (logs EXECUTE/VERIFY/REFLECT/RESPOND messages) — all
   published to the shared `core.event_bus.event_bus`.
5. The Coordinator aggregates every sub-agent's `.data` into one result dict,
   attaches the human-in-the-loop notice, and returns it to the UI.
6. The UI stores the full result in `st.session_state.papers[paper_id]` and
   every other page (Analysis, Related Work, Fact Checking, Learning,
   Presentation) reads from that same cached result — no recomputation.

## Extending the system

- **New agent**: subclass `agents.base.BaseAgent`, implement `plan`/`execute`
  (and optionally override `verify`/`reflect`), register it in
  `CoordinatorAgent.__init__`, and add a handoff call in the relevant
  workflow method.
- **New MCP tool**: add a function to `mcp/tools.py`, register it in
  `TOOL_REGISTRY`, and it's automatically available via `/mcp/call` and to
  any skill/agent that imports it directly.
- **New skill**: add a stateless function module to `skills/`; skills should
  never hold state — all persistence goes through `memory.memory_store`.
