"""
pages/1_Research_Workspace.py
Upload PDFs, run the full multi-agent analysis pipeline, and chat with papers.
"""
from __future__ import annotations

import streamlit as st

from core.config import settings
from core.llm_client import llm_client
from core.ui_state import (active_paper, all_papers, get_coordinator, init_session_state,
                            log_security_event, render_human_in_loop_notice, set_active_paper)
from core.ui_theme import apply_theme, icon, titled
from security.prompt_injection import sanitize_for_prompt, scan_text
from security.validation import validate_pdf_upload, validate_query

st.set_page_config(page_title="Research Workspace · ResearchOS AI", page_icon=":material/upload_file:", layout="wide")
apply_theme()
init_session_state()

st.title(titled("workspace", "Research Workspace"))
st.caption("Upload one or more papers and run the full multi-agent pipeline, or chat with an already-loaded paper.")

with st.expander("Pipeline options", icon=icon("settings"), expanded=False):
    difficulty = st.selectbox("Study material difficulty", ["Easy", "Medium", "Hard"], index=1)
    n_slides = st.slider("Number of presentation slides", 4, 15, 8)
    max_related = st.slider("Related papers to retrieve", 3, 12, 6)

uploaded_files = st.file_uploader("Upload research paper(s) (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    for uploaded in uploaded_files:
        file_bytes = uploaded.read()
        validation = validate_pdf_upload(uploaded.name, file_bytes)
        if not validation.is_valid:
            st.error(f"Rejected `{uploaded.name}`: {validation.reason}", icon=icon("error"))
            log_security_event("PDF Validation Failure", f"{uploaded.name}: {validation.reason}", "warning")
            continue

        already_loaded = any(
            p.get("structured_paper", {}).get("metadata", {}).get("source_filename") == uploaded.name
            for p in all_papers().values()
        )
        if already_loaded:
            st.info(f"`{uploaded.name}` is already loaded.", icon=icon("info"))
            continue

        with st.spinner(f"Running multi-agent analysis on `{uploaded.name}` (Paper Reader → Explainer → Fact Checker → Related Work → Research Gap → Quiz → Presentation)..."):
            coordinator = get_coordinator()
            result = coordinator.run({
                "workflow": "full_analysis",
                "pdf_bytes": file_bytes,
                "filename": uploaded.name,
                "difficulty": difficulty,
                "n_slides": n_slides,
                "max_related": max_related,
            })

        if result.data.get("error"):
            st.error(f"Analysis failed for `{uploaded.name}`: {result.data['error']}", icon=icon("error"))
            for w in result.warnings:
                st.caption(w)
            log_security_event("Pipeline Error", f"{uploaded.name}: {result.data['error']}", "error")
            continue

        structured_paper = result.data.get("structured_paper")
        if not structured_paper or not structured_paper.get("paper_id"):
            st.error(
                f"Analysis for `{uploaded.name}` did not complete as expected "
                f"(missing data). Check the terminal/console running `streamlit run app.py` "
                f"for the full error traceback.",
                icon=icon("error"),
            )
            for w in result.warnings:
                st.caption(w)
            log_security_event("Pipeline Error", f"{uploaded.name}: unexpected empty result", "error")
            continue

        paper_id = structured_paper["paper_id"]
        st.session_state.papers[paper_id] = result.data
        st.session_state.chat_history[paper_id] = []
        set_active_paper(paper_id)

        if structured_paper.get("injection_flagged"):
            log_security_event(
                "Prompt Injection Heuristic",
                f"Suspicious patterns detected inside `{uploaded.name}` text — content was sandboxed before reaching the LLM.",
                "warning",
            )

        for warning in result.warnings:
            st.warning(warning, icon=icon("warn"))

        st.success(f"Analysis complete for `{uploaded.name}`  ·  confidence {result.confidence:.2f}", icon=icon("check"))

st.divider()

papers = all_papers()
if not papers:
    st.info("No papers loaded yet. Upload a PDF above to get started.", icon=icon("info"))
    st.stop()

st.subheader("Loaded papers")
options = {pid: p["structured_paper"]["metadata"]["title"] for pid, p in papers.items()}
selected_id = st.selectbox(
    "Active paper", options=list(options.keys()), format_func=lambda pid: options[pid],
    index=list(options.keys()).index(st.session_state.active_paper_id) if st.session_state.active_paper_id in options else 0,
)
set_active_paper(selected_id)
paper = active_paper()

if paper:
    meta = paper["structured_paper"]["metadata"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Pages", paper["structured_paper"].get("page_count", "—"))
    c2.metric("Authors", len(meta.get("authors", [])) or "—")
    c3.metric("Sections detected", len(paper["structured_paper"].get("sections_detected", [])))

    render_human_in_loop_notice()

    st.subheader(titled("chat", "Chat with this paper"))
    pid = st.session_state.active_paper_id
    for role, text in st.session_state.chat_history.get(pid, []):
        with st.chat_message(role):
            st.markdown(text)

    question = st.chat_input("Ask a question about this paper...")
    if question:
        q_validation = validate_query(question)
        if not q_validation.is_valid:
            st.error(q_validation.reason, icon=icon("error"))
        else:
            scan = scan_text(question)
            if scan.is_suspicious:
                log_security_event(
                    "Prompt Injection Heuristic",
                    f"Chat message flagged categories={scan.matched_categories}",
                    "warning",
                )
            st.session_state.chat_history[pid].append(("user", question))
            with st.chat_message("user"):
                st.markdown(question)

            paper_text = paper["structured_paper"]["raw_text"][:6000]
            prompt = (
                "Answer the user's question about this paper using ONLY information from the "
                f"paper text below. If the answer isn't in the paper, say so.\n\n"
                f"PAPER TEXT:\n{sanitize_for_prompt(paper_text)}\n\nQUESTION: {question}"
            )
            answer = llm_client.generate(prompt, system="You are a helpful research assistant who answers strictly from the given paper.")
            st.session_state.chat_history[pid].append(("assistant", answer))
            with st.chat_message("assistant"):
                st.markdown(answer)
            st.rerun()
