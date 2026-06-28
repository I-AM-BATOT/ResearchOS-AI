"""
agents/presentation.py
Presentation Agent: generates a slide deck outline, speaker notes,
conference presentation script, and poster summary.
"""
from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from core.models import AgentName
from skills.presentation import build_presentation_pack


class PresentationAgent(BaseAgent):
    name = AgentName.PRESENTATION

    def plan(self, task_input: dict[str, Any]) -> dict[str, Any]:
        n_slides = task_input.get("n_slides", 8)
        return {"summary": f"Build a {n_slides}-slide presentation pack with speaker notes."}

    def execute(self, task_input: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        paper_text = task_input["paper_text"]
        n_slides = task_input.get("n_slides", 8)
        pack = build_presentation_pack(paper_text, n_slides=n_slides)
        return pack.model_dump()

    def verify(self, task_input: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
        if not result.get("slides"):
            return False, ["No slides were generated."]
        return True, []
