"""
skills/summarization.py
Summarization Skill: Executive / Technical / ELI5 summaries.

This is a reusable "skill" (per the spec's Agent Skills requirement) --
a stateless function module that any agent can call. The ResearchExplainer
Agent is the primary consumer, but the LiteratureReview and Presentation
agents reuse it too.
"""
from __future__ import annotations

from core.llm_client import llm_client
from security.prompt_injection import sanitize_for_prompt

_SYSTEM = (
    "You are a precise scientific writing assistant. You summarize research "
    "papers faithfully without inventing facts not present in the source text."
)


def executive_summary(paper_text: str) -> str:
    prompt = (
        "Write a 4-6 sentence EXECUTIVE SUMMARY of this paper for a research "
        "manager who needs the headline contribution and why it matters:\n\n"
        f"{sanitize_for_prompt(paper_text)}"
    )
    return llm_client.generate(prompt, system=_SYSTEM)


def technical_summary(paper_text: str) -> str:
    prompt = (
        "Write a TECHNICAL SUMMARY of this paper for a domain expert. Include "
        "methodology, architecture/approach, datasets, and key quantitative "
        "results:\n\n"
        f"{sanitize_for_prompt(paper_text)}"
    )
    return llm_client.generate(prompt, system=_SYSTEM)


def beginner_summary(paper_text: str) -> str:
    prompt = (
        "Write a BEGINNER-FRIENDLY summary of this paper for an undergraduate "
        "student who knows the basics of the field but not this subarea:\n\n"
        f"{sanitize_for_prompt(paper_text)}"
    )
    return llm_client.generate(prompt, system=_SYSTEM)


def eli5_summary(paper_text: str) -> str:
    prompt = (
        "Explain this paper's core idea LIKE I'M 5 YEARS OLD. Use a simple "
        "analogy. No jargon:\n\n"
        f"{sanitize_for_prompt(paper_text)}"
    )
    return llm_client.generate(prompt, system=_SYSTEM)


def all_summaries(paper_text: str) -> dict[str, str]:
    return {
        "executive_summary": executive_summary(paper_text),
        "technical_summary": technical_summary(paper_text),
        "beginner_summary": beginner_summary(paper_text),
        "eli5_summary": eli5_summary(paper_text),
    }
