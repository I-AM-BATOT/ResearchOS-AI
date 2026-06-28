"""
pages/6_Learning_Center.py
Flashcards, MCQs, short-answer questions, and study guides for the active paper.
"""
from __future__ import annotations

import streamlit as st

from core.ui_state import active_paper, init_session_state
from core.ui_theme import apply_theme, icon, titled

st.set_page_config(page_title="Learning Center · ResearchOS AI", page_icon=":material/school:", layout="wide")
apply_theme()
init_session_state()

st.title(titled("learning", "Learning Center"))

paper = active_paper()
if not paper:
    st.info("No active paper. Upload one in **Research Workspace** first.", icon=icon("info"))
    st.stop()

study_pack = paper.get("study_pack", {})

tab_flash, tab_mcq, tab_short, tab_guide = st.tabs([
    titled("flashcard", "Flashcards"),
    titled("quiz", "MCQs"),
    "Short Answer",
    titled("guide", "Study Guide"),
])

with tab_flash:
    flashcards = study_pack.get("flashcards", [])
    if not flashcards:
        st.caption("No flashcards generated.")
    for i, card in enumerate(flashcards):
        with st.expander(f"Card {i + 1}: {card['front']}  ·  {card['difficulty']}"):
            st.markdown(f"**Answer:** {card['back']}")

with tab_mcq:
    mcqs = study_pack.get("mcqs", [])
    if not mcqs:
        st.caption("No MCQs generated.")
    for i, mcq in enumerate(mcqs):
        st.markdown(f"**Q{i + 1}. {mcq['question']}**  `{mcq['difficulty']}`")
        choice = st.radio(
            f"q{i}", options=list(range(len(mcq["options"]))),
            format_func=lambda idx, opts=mcq["options"]: opts[idx],
            key=f"mcq_{i}", index=None, label_visibility="collapsed",
        )
        if choice is not None:
            if choice == mcq["correct_index"]:
                st.success("Correct.", icon=icon("check"))
            else:
                st.error(f"Incorrect. Correct answer: {mcq['options'][mcq['correct_index']]}", icon=icon("error"))
            if mcq.get("explanation"):
                st.caption(mcq["explanation"])
        st.divider()

with tab_short:
    for i, q in enumerate(study_pack.get("short_answer", []), start=1):
        st.markdown(f"**{i}.** {q}")
        st.text_area("Your answer", key=f"sa_{i}", label_visibility="collapsed")

with tab_guide:
    st.write(study_pack.get("study_guide", "No study guide generated."))
