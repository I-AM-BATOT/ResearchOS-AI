"""
pages/8_Memory_Dashboard.py
Past papers, research history, and stored knowledge with semantic search.
"""
from __future__ import annotations

import streamlit as st

from core.ui_state import init_session_state
from core.ui_theme import apply_theme, icon, titled
from memory.memory_store import memory_store

st.set_page_config(page_title="Memory Dashboard · ResearchOS AI", page_icon=":material/memory:", layout="wide")
apply_theme()
init_session_state()

st.title(titled("memory", "Memory Dashboard"))
st.caption(f"Backend: **{memory_store.backend_name}** "
           f"({'true semantic vector search' if memory_store.backend_name == 'chromadb' else 'keyword-overlap search (install chromadb for embeddings)'})")

all_records = memory_store.all_records()
kinds = sorted({r.kind for r in all_records})

c1, c2, c3 = st.columns(3)
c1.metric("Total memories", len(all_records))
c2.metric("Paper summaries", sum(1 for r in all_records if r.kind == "paper_summary"))
c3.metric("Agent observations", sum(1 for r in all_records if r.kind == "observation"))

st.divider()
st.subheader(titled("search", "Search memory"))
query = st.text_input("Search past papers, insights, and observations")
kind_filter = st.selectbox("Filter by kind", ["(any)"] + kinds)
if query:
    results = memory_store.recall(query, top_k=10, kind=None if kind_filter == "(any)" else kind_filter)
    if not results:
        st.caption("No matching memories found.")
    for r in results:
        with st.expander(f"[{r.kind}] {r.text[:90]}"):
            st.write(r.text)
            st.json(r.metadata)
            if st.button("Delete", icon=icon("delete"), key=f"del_{r.record_id}"):
                memory_store.forget(r.record_id)
                st.rerun()

st.divider()
st.subheader("All stored memories")
for r in all_records:
    with st.expander(f"[{r.kind}] {r.text[:90]}  ·  {r.created_at}"):
        st.write(r.text)
        if r.metadata:
            st.json(r.metadata)
        if st.button("Delete", icon=icon("delete"), key=f"del_all_{r.record_id}"):
            memory_store.forget(r.record_id)
            st.rerun()

if not all_records:
    st.info("No memories stored yet. Run an analysis in **Research Workspace** to populate memory.",
             icon=icon("info"))
