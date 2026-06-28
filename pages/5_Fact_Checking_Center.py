"""
pages/5_Fact_Checking_Center.py
Claim verification, evidence review, and confidence scoring for the active paper.
"""
from __future__ import annotations

import streamlit as st

from core.ui_state import active_paper, init_session_state, render_human_in_loop_notice
from core.ui_theme import apply_theme, badge, icon, titled
from mcp.tools import verify_research_claim
from security.validation import validate_query

st.set_page_config(page_title="Fact Checking Center · ResearchOS AI", page_icon=":material/fact_check:", layout="wide")
apply_theme()
init_session_state()

st.title(titled("fact_check", "Fact Checking Center"))

paper = active_paper()
if not paper:
    st.info("No active paper. Upload one in **Research Workspace** first.", icon=icon("info"))
    st.stop()

render_human_in_loop_notice()

fact_check = paper.get("fact_check", {})
verifications = fact_check.get("verifications", [])

st.subheader(f"Claims checked: {fact_check.get('claims_checked', 0)}")

status_kind = {"Verified": "success", "Questionable": "warning", "Needs Review": "error"}
for v in verifications:
    kind = status_kind.get(v["status"], "neutral")
    with st.expander(f"{v['status']}  ·  {v['confidence']:.0%} confidence  —  {v['claim'][:90]}"):
        st.markdown(badge(v["status"], kind), unsafe_allow_html=True)
        st.markdown(f"**Full claim:** {v['claim']}")
        st.progress(v["confidence"])
        if v.get("supporting_evidence"):
            st.markdown("**Supporting evidence:**")
            for e in v["supporting_evidence"]:
                st.markdown(f"- {e}")
        else:
            st.caption("No supporting evidence found.")
        if v.get("notes"):
            st.caption(v["notes"])

st.divider()
st.subheader("Verify a custom claim")
custom_claim = st.text_area("Enter a research claim to verify against scholarly sources")
if st.button("Verify claim", icon=icon("search")) and custom_claim:
    validation = validate_query(custom_claim)
    if not validation.is_valid:
        st.error(validation.reason, icon=icon("error"))
    else:
        with st.spinner("Cross-referencing against Semantic Scholar..."):
            result = verify_research_claim(custom_claim)
        kind = status_kind.get(result["status"], "neutral")
        st.markdown(f"### {result['confidence']:.0%} confidence")
        st.markdown(badge(result["status"], kind), unsafe_allow_html=True)
        if result.get("mock"):
            st.caption(result.get("note", ""))
        for e in result.get("supporting_evidence", []):
            st.markdown(f"- {e}")
