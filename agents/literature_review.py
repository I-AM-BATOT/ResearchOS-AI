"""
agents/literature_review.py
Literature Review Agent: combines multiple papers into a Literature Review,
Research Trends, Comparative Analysis, and State-of-the-Art Summary.
"""
from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from core.llm_client import llm_client
from core.models import AgentName, LiteratureReview
from mcp.tools import compare_papers
from security.prompt_injection import sanitize_for_prompt

_SYSTEM = "You are a research scientist writing a rigorous, well-organized literature review."


class LiteratureReviewAgent(BaseAgent):
    name = AgentName.LITERATURE_REVIEW

    def plan(self, task_input: dict[str, Any]) -> dict[str, Any]:
        n = len(task_input.get("papers", []))
        return {"summary": f"Synthesize a literature review across {n} paper(s)."}

    def execute(self, task_input: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        papers: list[dict] = task_input["papers"]  # list of StructuredPaper-like dicts

        combined_excerpt = "\n\n---\n\n".join(
            f"TITLE: {p.get('metadata', {}).get('title', p.get('title', 'Untitled'))}\n"
            f"ABSTRACT: {p.get('abstract', '')[:600]}"
            for p in papers
        )

        synthesis = llm_client.generate(
            "Write a literature review SYNTHESIS paragraph weaving together these "
            f"papers' contributions and how they relate:\n\n{sanitize_for_prompt(combined_excerpt)}",
            system=_SYSTEM,
        )
        trends_raw = llm_client.generate(
            f"List 3-5 RESEARCH TRENDS visible across these papers, one per line:\n\n{sanitize_for_prompt(combined_excerpt)}",
            system=_SYSTEM,
        )
        trends = [t.strip("-•* ") for t in trends_raw.splitlines() if t.strip()][:5]

        comparative = ""
        if len(papers) >= 2:
            comparison = compare_papers(papers[0], papers[1])
            comparative = llm_client.generate(
                f"Turn this structural comparison into a short COMPARATIVE ANALYSIS prose paragraph: {comparison}",
                system=_SYSTEM,
            )

        sota = llm_client.generate(
            f"Write a 'STATE OF THE ART' summary paragraph for this research area based on these papers:\n\n{sanitize_for_prompt(combined_excerpt)}",
            system=_SYSTEM,
        )

        review = LiteratureReview(
            synthesis=synthesis,
            research_trends=trends,
            comparative_analysis=comparative,
            state_of_the_art=sota,
            papers_considered=[p.get("metadata", {}).get("title", p.get("title", "Untitled")) for p in papers],
        )
        return review.model_dump()

    def verify(self, task_input: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
        if not result.get("synthesis"):
            return False, ["Literature review synthesis is empty."]
        return True, []
