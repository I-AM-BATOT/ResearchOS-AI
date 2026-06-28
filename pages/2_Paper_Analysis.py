"""
pages/2_Paper_Analysis.py
Summaries, insights, and key findings for the active paper.
"""
from __future__ import annotations

import streamlit as st

from core.ui_state import active_paper, init_session_state, render_human_in_loop_notice
from core.ui_theme import apply_theme, icon, titled

st.set_page_config(page_title="Paper Analysis · ResearchOS AI", page_icon=":material/article:", layout="wide")
apply_theme()
init_session_state()

st.title(titled("analysis", "Paper Analysis"))

paper = active_paper()
if not paper:
    st.info("No active paper. Upload one in **Research Workspace** first.", icon=icon("info"))
    st.stop()

meta = paper["structured_paper"]["metadata"]
st.subheader(meta.get("title", "Untitled"))
if meta.get("authors"):
    st.caption(", ".join(meta["authors"]))

render_human_in_loop_notice()

summaries = paper.get("summaries", {})
tab_exec, tab_tech, tab_beg, tab_eli5 = st.tabs([
    "Executive Summary", "Technical Summary", "Beginner Summary", "ELI5",
])
with tab_exec:
    st.write(summaries.get("executive_summary", "—"))
with tab_tech:
    st.write(summaries.get("technical_summary", "—"))
with tab_beg:
    st.write(summaries.get("beginner_summary", "—"))
with tab_eli5:
    st.write(summaries.get("eli5_summary", "—"))

st.divider()
st.subheader("Detected sections")
sp = paper["structured_paper"]
section_names = ["abstract", "introduction", "methods", "results", "discussion", "conclusion"]
cols = st.columns(2)
for i, sec in enumerate(section_names):
    content = sp.get(sec, "")
    if content:
        with cols[i % 2]:
            with st.expander(sec.title(), expanded=(sec == "abstract")):
                st.write(content[:2000] + ("…" if len(content) > 2000 else ""))

st.divider()
st.subheader(titled("idea", "Key research gaps (preview)"))
gap = paper.get("research_gap", {})
if gap.get("novel_ideas"):
    for idea in gap["novel_ideas"][:3]:
        st.markdown(f"- {idea}")
    st.caption("See the Literature Review Builder and other pages for the full breakdown.")
else:
    st.caption("No research gap data available for this paper.")
