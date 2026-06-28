"""
agents/related_work.py
Related Work Agent: finds related papers, competing methods, prior work,
and recent publications. Produces a Related Research Map.
"""
from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from core.models import AgentName
from skills.research import discover_related_work


class RelatedWorkAgent(BaseAgent):
    name = AgentName.RELATED_WORK

    def plan(self, task_input: dict[str, Any]) -> dict[str, Any]:
        return {"summary": f"Search arXiv + Semantic Scholar for work related to '{task_input.get('topic', '')}'."}

    def execute(self, task_input: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        topic = task_input["topic"]
        max_results = task_input.get("max_results", 6)
        related = discover_related_work(topic, max_results=max_results)
        # Build a simple "research map": group by relation type for the UI graph.
        research_map: dict[str, list[dict]] = {}
        for paper in related:
            research_map.setdefault(paper.relation, []).append(paper.model_dump())
        return {"related_papers": [p.model_dump() for p in related], "research_map": research_map}

    def verify(self, task_input: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
        if not result.get("related_papers"):
            return False, ["No related papers were found for this topic."]
        return True, []
