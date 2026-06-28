"""
agents/research_explainer.py
Research Explainer Agent: generates Executive / Technical / Beginner / ELI5
summaries answering "what does this paper mean?"
"""
from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from core.models import AgentName
from skills.summarization import all_summaries


class ResearchExplainerAgent(BaseAgent):
    name = AgentName.RESEARCH_EXPLAINER

    def plan(self, task_input: dict[str, Any]) -> dict[str, Any]:
        return {"summary": "Generate multi-level summaries (executive/technical/beginner/ELI5)."}

    def execute(self, task_input: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        paper_text = task_input["paper_text"]
        return all_summaries(paper_text)

    def verify(self, task_input: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
        warnings = [k for k, v in result.items() if not v or not v.strip()]
        if warnings:
            return False, [f"Empty output for: {', '.join(warnings)}"]
        return True, []
