"""
core/ui_state.py
Shared Streamlit session-state helpers used by app.py and every page in
pages/. Kept out of the pages/ directory itself so Streamlit doesn't try
to render it as a page.
"""
from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from agents.coordinator import CoordinatorAgent
from core.config import settings
from core.event_bus import event_bus
from core.ui_theme import badge, icon


def init_session_state() -> None:
    if "coordinator" not in st.session_state:
        st.session_state.coordinator = CoordinatorAgent()
    if "papers" not in st.session_state:
        st.session_state.papers = {}  # paper_id -> full analysis result dict
    if "active_paper_id" not in st.session_state:
        st.session_state.active_paper_id = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}  # paper_id -> list[(role, text)]
    if "security_log" not in st.session_state:
        st.session_state.security_log = []  # list of dicts: {type, detail, severity}


def get_coordinator() -> CoordinatorAgent:
    init_session_state()
    return st.session_state.coordinator


def active_paper() -> Optional[dict]:
    init_session_state()
    pid = st.session_state.active_paper_id
    return st.session_state.papers.get(pid) if pid else None


def set_active_paper(paper_id: str) -> None:
    st.session_state.active_paper_id = paper_id


def all_papers() -> dict[str, dict]:
    init_session_state()
    return st.session_state.papers


def log_security_event(event_type: str, detail: str, severity: str = "info") -> None:
    init_session_state()
    st.session_state.security_log.insert(0, {"type": event_type, "detail": detail, "severity": severity})


def mode_badge() -> str:
    return badge("LIVE · Gemini", "success") if settings.live_mode else badge("MOCK · offline demo", "neutral")


def render_human_in_loop_notice() -> None:
    st.warning("Research findings should be independently verified.", icon=icon("warn"))


def render_agent_trace(limit: int = 30) -> None:
    """Renders the real agent-to-agent communication trace from the event bus."""
    messages = event_bus.history()[-limit:]
    if not messages:
        st.info("No agent activity yet. Run an analysis to see the agent collaboration trace.", icon=icon("info"))
        return
    for m in reversed(messages):
        conf = f"  ·  confidence {m.confidence:.2f}" if m.confidence is not None else ""
        st.markdown(
            f"**{m.sender.value} &rarr; {m.receiver.value}**  `{m.stage.value}`{conf}  \n{m.summary}",
            unsafe_allow_html=True,
        )
