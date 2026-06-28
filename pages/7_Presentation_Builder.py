"""
pages/7_Presentation_Builder.py
Slides, speaker notes, conference talk script, and poster summary.
"""
from __future__ import annotations

import streamlit as st

from core.ui_state import active_paper, init_session_state
from core.ui_theme import apply_theme, icon, titled

st.set_page_config(page_title="Presentation Builder · ResearchOS AI", page_icon=":material/slideshow:", layout="wide")
apply_theme()
init_session_state()

st.title(titled("presentation", "Presentation Builder"))

paper = active_paper()
if not paper:
    st.info("No active paper. Upload one in **Research Workspace** first.", icon=icon("info"))
    st.stop()

presentation = paper.get("presentation", {})
slides = presentation.get("slides", [])

st.subheader(f"Slide deck  ·  {len(slides)} slides")
if not slides:
    st.caption("No slides generated.")
else:
    slide_idx = st.slider("Slide", 1, len(slides), 1) - 1 if len(slides) > 1 else 0
    slide = slides[slide_idx]

    bullets_html = "".join(f"<li>{b}</li>" for b in slide["bullets"])
    st.markdown(
        f"<div style='border:1px solid rgba(120,120,120,0.28); border-radius:14px; padding:32px; "
        f"background:rgba(120,120,120,0.06); min-height:260px; box-shadow:0 4px 14px rgba(0,0,0,0.10);'>"
        f"<h3 style='margin-top:0;'>{slide['title']}</h3>"
        f"<ul>{bullets_html}</ul></div>",
        unsafe_allow_html=True,
    )
    with st.expander("Speaker notes", icon=icon("notes")):
        st.write(slide.get("speaker_notes", "—"))

    with st.expander("Full outline (all slides)"):
        for i, s in enumerate(slides, start=1):
            st.markdown(f"**{i}. {s['title']}**")
            for b in s["bullets"]:
                st.markdown(f"- {b}")

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.subheader("Conference talk script")
    st.write(presentation.get("conference_talk_summary", "—"))
with col2:
    st.subheader(titled("poster", "Poster summary"))
    st.write(presentation.get("poster_summary", "—"))
