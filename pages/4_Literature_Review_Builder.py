"""
pages/4_Literature_Review_Builder.py
Compare papers and generate a combined literature review across all loaded papers.
"""
from __future__ import annotations

import streamlit as st

from core.ui_state import all_papers, get_coordinator, init_session_state, render_human_in_loop_notice
from core.ui_theme import apply_theme, icon, titled
from mcp.tools import compare_papers

st.set_page_config(page_title="Literature Review Builder · ResearchOS AI", page_icon=":material/menu_book:", layout="wide")
apply_theme()
init_session_state()

st.title(titled("literature", "Literature Review Builder"))

papers = all_papers()
if len(papers) < 1:
    st.info("Upload at least one paper in **Research Workspace** first (2+ recommended for a richer review).",
             icon=icon("info"))
    st.stop()

st.subheader("Select papers to include")
options = {pid: p["structured_paper"]["metadata"]["title"] for pid, p in papers.items()}
selected_ids = st.multiselect(
    "Papers", options=list(options.keys()), default=list(options.keys()),
    format_func=lambda pid: options[pid],
)

if len(selected_ids) >= 2:
    st.subheader(titled("compare", "Quick pairwise comparison"))
    a_id, b_id = selected_ids[0], selected_ids[1]
    paper_a = papers[a_id]["structured_paper"]
    paper_b = papers[b_id]["structured_paper"]
    comparison = compare_papers(
        {"title": paper_a["metadata"]["title"], "methods": paper_a.get("methods", ""), "results": paper_a.get("results", "")},
        {"title": paper_b["metadata"]["title"], "methods": paper_b.get("methods", ""), "results": paper_b.get("results", "")},
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{comparison['paper_a']['title']}**")
        st.caption(comparison['paper_a']['methods_excerpt'] or "—")
    with c2:
        st.markdown(f"**{comparison['paper_b']['title']}**")
        st.caption(comparison['paper_b']['methods_excerpt'] or "—")
    if comparison.get("shared_terminology"):
        st.markdown("**Shared terminology:** " + ", ".join(comparison["shared_terminology"]))

st.divider()
if st.button("Generate literature review", type="primary", icon=icon("literature"), disabled=len(selected_ids) == 0):
    structured_papers = [papers[pid]["structured_paper"] for pid in selected_ids]
    with st.spinner("Literature Review Agent synthesizing trends, comparisons, and state-of-the-art..."):
        coordinator = get_coordinator()
        result = coordinator.run({"workflow": "literature_review", "papers": structured_papers})
    st.session_state["last_literature_review"] = result.data.get("literature_review", {})
    st.success(f"Done  ·  confidence {result.confidence:.2f}", icon=icon("check"))

review = st.session_state.get("last_literature_review")
if review:
    render_human_in_loop_notice()
    st.subheader("Synthesis")
    st.write(review.get("synthesis", "—"))

    st.subheader(titled("trend", "Research trends"))
    for trend in review.get("research_trends", []):
        st.markdown(f"- {trend}")

    if review.get("comparative_analysis"):
        st.subheader("Comparative analysis")
        st.write(review["comparative_analysis"])

    st.subheader("State of the art")
    st.write(review.get("state_of_the_art", "—"))

    st.caption("Papers considered: " + ", ".join(review.get("papers_considered", [])))
