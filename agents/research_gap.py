"""
agents/research_gap.py
Research Gap Agent: identifies weaknesses, limitations, missing experiments,
and future opportunities. Outputs Novel Research Ideas.
"""
from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from core.llm_client import llm_client
from core.models import AgentName, ResearchGap
from security.prompt_injection import sanitize_for_prompt

_SYSTEM = "You are a critical, constructive peer reviewer skilled at identifying genuine research gaps."


class ResearchGapAgent(BaseAgent):
    name = AgentName.RESEARCH_GAP

    def plan(self, task_input: dict[str, Any]) -> dict[str, Any]:
        return {"summary": "Critically analyze limitations and propose novel research directions."}

    def execute(self, task_input: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        paper_text = task_input["paper_text"]
        ctx = sanitize_for_prompt(paper_text)

        weaknesses = self._bullet_list(
            f"List 3-5 WEAKNESSES in this paper's argument or experimental design:\n\n{ctx}"
        )
        limitations = self._bullet_list(
            f"List 3-5 LIMITATIONS the authors acknowledge or should acknowledge:\n\n{ctx}"
        )
        missing = self._bullet_list(
            f"List 3-5 MISSING EXPERIMENTS that would strengthen this paper's claims:\n\n{ctx}"
        )
        ideas = self._bullet_list(
            f"Propose 3-5 NOVEL RESEARCH IDEAS that extend this paper's work in a new direction:\n\n{ctx}"
        )

        gap = ResearchGap(
            weaknesses=weaknesses,
            limitations=limitations,
            missing_experiments=missing,
            novel_ideas=ideas,
        )
        return gap.model_dump()

    def verify(self, task_input: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
        if not result.get("novel_ideas"):
            return False, ["No novel research ideas were generated."]
        return True, []

    @staticmethod
    def _bullet_list(prompt: str) -> list[str]:
        raw = llm_client.generate(prompt, system=_SYSTEM)
        return [l.strip("-•* ") for l in raw.splitlines() if l.strip()][:5]
