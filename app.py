"""
app.py
ResearchOS AI - Streamlit entry point (Home / Overview page).

Run with:
    streamlit run app.py

Other pages live in pages/ and are auto-discovered by Streamlit's
multipage app convention.
"""
from __future__ import annotations

import streamlit as st

from core.config import settings
from core.ui_state import all_papers, init_session_state, mode_badge
from core.ui_theme import apply_theme, icon, titled
from memory.memory_store import memory_store
from security.safe_logging import install_safe_logging

st.set_page_config(
    page_title="ResearchOS AI",
    page_icon=":material/science:",
    layout="wide",
)

apply_theme()
install_safe_logging()
init_session_state()

st.title(titled("app", "ResearchOS AI"))
st.caption("Multi-Agent Research Operating System  ·  Kaggle AI Agents Intensive Vibe Coding Capstone")
st.markdown(mode_badge(), unsafe_allow_html=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.metric("Memory backend", memory_store.backend_name)
with col2:
    st.metric("Papers loaded", len(all_papers()))

st.divider()

st.markdown(
    "ResearchOS AI acts like an entire AI research team. Upload one or more papers and the "
    "system automatically understands them, verifies claims, finds related work, builds "
    "literature reviews, generates study materials, builds presentations, and surfaces "
    "research gaps — using a coordinated team of specialist agents that plan, execute, "
    "verify, and reflect on every task."
)

st.subheader(titled("settings", "How it's built"))
left, right = st.columns(2)
with left:
    st.markdown("**10 specialist agents**, each running a `PLAN → EXECUTE → VERIFY → REFLECT → RESPOND` loop:")
    st.markdown(
        "- Coordinator — plans and delegates across all agents\n"
        "- Paper Reader — extracts and segments PDF text\n"
        "- Research Explainer — executive / technical / beginner / ELI5 summaries\n"
        "- Fact Checker — claim verification with confidence scoring\n"
        "- Related Work — arXiv and Semantic Scholar discovery\n"
        "- Literature Review — synthesis across multiple papers\n"
        "- Research Gap — limitations and novel research ideas\n"
        "- Quiz & Teaching — flashcards, MCQs, study guides\n"
        "- Presentation — slide decks, speaker notes, posters\n"
        "- Memory — persistent, semantically-searchable history"
    )
with right:
    st.markdown("**Platform capabilities:**")
    st.markdown(
        "- MCP Server (FastAPI) with 7 research tools — arXiv, Semantic Scholar, citation "
        "graphs, claim verification, paper comparison, bibliography generation, metadata extraction\n"
        "- Persistent memory — ChromaDB semantic search with an automatic SQLite fallback\n"
        "- Security — prompt-injection defense, PII masking, PDF validation, safe logging\n"
        "- Human-in-the-loop — every research output is flagged for independent verification\n"
        "- Deployable via Docker, Streamlit Cloud, Google Cloud Run, or Hugging Face Spaces"
    )

st.divider()
st.subheader("Get started")
st.page_link("pages/1_Research_Workspace.py", label="Go to Research Workspace to upload a paper",
             icon=icon("workspace"))

if not settings.live_mode:
    st.info(
        "Running in **mock mode** — no `GEMINI_API_KEY` was found, so the platform uses deterministic "
        "offline placeholder text instead of live Gemini calls. The full agent pipeline, MCP tools, "
        "memory, and security layers all still run end-to-end. Add a key to your `.env` file (see "
        "`.env.example`) to switch to live mode.",
        icon=icon("mock"),
    )
