"""
agents/quiz_teaching.py
Quiz and Teaching Agent: generates flashcards, MCQs, short-answer questions,
and study guides at Easy / Medium / Hard difficulty.
"""
from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from core.models import AgentName, DifficultyLevel
from skills.teaching import build_study_pack


class QuizTeachingAgent(BaseAgent):
    name = AgentName.QUIZ_TEACHING

    def plan(self, task_input: dict[str, Any]) -> dict[str, Any]:
        difficulty = task_input.get("difficulty", "Medium")
        return {"summary": f"Build a study pack (flashcards, MCQs, short-answer, guide) at {difficulty} difficulty."}

    def execute(self, task_input: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        paper_text = task_input["paper_text"]
        difficulty = DifficultyLevel(task_input.get("difficulty", "Medium"))
        pack = build_study_pack(paper_text, difficulty=difficulty)
        return pack.model_dump()

    def verify(self, task_input: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
        warnings = []
        if not result.get("flashcards"):
            warnings.append("No flashcards were generated.")
        if not result.get("mcqs"):
            warnings.append("No MCQs were generated.")
        return bool(result.get("flashcards") or result.get("mcqs")), warnings
