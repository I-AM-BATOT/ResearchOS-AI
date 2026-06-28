"""
skills/research.py
Research Skill: Related Work Discovery, Citation Analysis, Trend Analysis.
Wraps the MCP tools with prompt assembly so agents get back prose, not raw JSON.
"""
from __future__ import annotations

from core.llm_client import llm_client
from core.models import RelatedPaper
from mcp.tools import search_arxiv, search_semantic_scholar, retrieve_citation_graph

_SYSTEM = "You are a meticulous literature-search research assistant."


def discover_related_work(topic: str, max_results: int = 5) -> list[RelatedPaper]:
    arxiv_results = search_arxiv(topic, max_results=max_results).get("results", [])
    scholar_results = search_semantic_scholar(topic, limit=max_results).get("results", [])

    related: list[RelatedPaper] = []
    for r in arxiv_results:
        related.append(RelatedPaper(
            title=r.get("title", "Untitled"),
            authors=r.get("authors", []),
            year=_year_from_date(r.get("published")),
            link=r.get("link"),
            relation="related",
        ))
    for r in scholar_results:
        related.append(RelatedPaper(
            title=r.get("title", "Untitled"),
            authors=r.get("authors", []),
            year=r.get("year"),
            link=r.get("url"),
            relation="prior_work",
        ))
    return related


def citation_analysis(paper_title: str) -> dict:
    return retrieve_citation_graph(paper_title)


def trend_analysis(topic: str, related: list[RelatedPaper]) -> str:
    years = [r.year for r in related if r.year]
    titles = "\n".join(f"- {r.title} ({r.year or 'n.d.'})" for r in related[:10])
    prompt = (
        f"Given this set of papers related to '{topic}':\n{titles}\n\n"
        "Write a short RESEARCH TRENDS paragraph: is interest growing, what "
        "sub-themes recur, and what direction does the field seem to be moving?"
    )
    return llm_client.generate(prompt, system=_SYSTEM)


def _year_from_date(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        return int(date_str[:4])
    except (ValueError, TypeError):
        return None
