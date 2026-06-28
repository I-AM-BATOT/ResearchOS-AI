"""
pages/3_Related_Work_Explorer.py
Research graph, citation graph, and related papers for the active paper.
"""
from __future__ import annotations

import streamlit as st

from core.ui_state import active_paper, init_session_state
from core.ui_theme import apply_theme, icon, titled
from mcp.tools import retrieve_citation_graph

st.set_page_config(page_title="Related Work Explorer · ResearchOS AI", page_icon=":material/link:", layout="wide")
apply_theme()
init_session_state()

st.title(titled("related", "Related Work Explorer"))

paper = active_paper()
if not paper:
    st.info("No active paper. Upload one in **Research Workspace** first.", icon=icon("info"))
    st.stop()

related = paper.get("related_work", {})
research_map = related.get("research_map", {})

st.subheader("Related research map")
if not research_map:
    st.caption("No related-work data available for this paper.")
else:
    relation_labels = {
        "related": "Related (arXiv)",
        "prior_work": "Prior work (Semantic Scholar)",
        "competing_method": "Competing methods",
        "citing": "Citing papers",
        "referenced": "Referenced papers",
    }
    cols = st.columns(len(research_map) or 1)
    for col, (relation, items) in zip(cols, research_map.items()):
        with col:
            st.markdown(f"**{relation_labels.get(relation, relation)}**")
            for item in items:
                link = item.get("link")
                title = item.get("title", "Untitled")
                year = item.get("year", "")
                if link:
                    st.markdown(f"- [{title}]({link}) {f'({year})' if year else ''}")
                else:
                    st.markdown(f"- {title} {f'({year})' if year else ''}")

st.divider()
st.subheader("Citation graph")
title = paper["structured_paper"]["metadata"].get("title", "")
if st.button("Retrieve citation graph for this paper", icon=icon("graph")):
    with st.spinner("Querying Semantic Scholar citation graph..."):
        graph = retrieve_citation_graph(title)
    if graph.get("mock"):
        st.caption(graph.get("note", ""))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Citing papers**")
        for cp in graph.get("citing_papers", []):
            st.markdown(f"- {cp}")
    with c2:
        st.markdown("**Referenced papers**")
        for rp in graph.get("referenced_papers", []):
            st.markdown(f"- {rp}")
