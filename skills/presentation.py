"""
skills/presentation.py
Presentation Skill: Slides, Speaker Notes, Conference Talks, Poster Summaries.
"""
from __future__ import annotations

import json
import re

from core.llm_client import llm_client
from core.models import PresentationPack, SlideContent
from security.prompt_injection import sanitize_for_prompt

_SYSTEM = "You are a research communication expert who builds clear, compelling academic slide decks."


def generate_slide_outline(paper_text: str, n_slides: int = 8) -> list[SlideContent]:
    prompt = (
        f"Create an outline for a {n_slides}-slide academic presentation of this "
        "paper (Title, Motivation, Related Work, Method, Results, Limitations, "
        "Conclusion, Future Work as a guide -- adapt as needed). Respond ONLY "
        "as JSON: a list of objects with 'title', 'bullets' (3-5 short bullets), "
        "'speaker_notes' (2-3 sentences).\n\n"
        f"{sanitize_for_prompt(paper_text)}"
    )
    raw = llm_client.generate(prompt, system=_SYSTEM, json_mode=True)
    items = _safe_json_list(raw)
    if items:
        return [
            SlideContent(title=i.get("title", "Slide"), bullets=i.get("bullets", []),
                         speaker_notes=i.get("speaker_notes", ""))
            for i in items
        ]
    fallback_titles = ["Title", "Motivation", "Related Work", "Method", "Results",
                        "Limitations", "Conclusion", "Future Work"][:n_slides]
    return [
        SlideContent(title=t, bullets=["[MOCK] bullet point"], speaker_notes="[MOCK] speaker notes")
        for t in fallback_titles
    ]


def generate_conference_talk_summary(paper_text: str) -> str:
    prompt = (
        "Write a 5-minute CONFERENCE TALK script summary (intro hook, 3 main "
        "points, closing) for presenting this paper:\n\n"
        f"{sanitize_for_prompt(paper_text)}"
    )
    return llm_client.generate(prompt, system=_SYSTEM)


def generate_poster_summary(paper_text: str) -> str:
    prompt = (
        "Write a CONFERENCE POSTER summary: Background, Method, Results, "
        "Conclusion -- each 2-3 sentences, for this paper:\n\n"
        f"{sanitize_for_prompt(paper_text)}"
    )
    return llm_client.generate(prompt, system=_SYSTEM)


def build_presentation_pack(paper_text: str, n_slides: int = 8) -> PresentationPack:
    return PresentationPack(
        slides=generate_slide_outline(paper_text, n_slides),
        conference_talk_summary=generate_conference_talk_summary(paper_text),
        poster_summary=generate_poster_summary(paper_text),
    )


def _safe_json_list(raw: str) -> list[dict]:
    try:
        cleaned = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE).strip()
        data = json.loads(cleaned)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
