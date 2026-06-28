"""
skills/teaching.py
Teaching Skill: Quiz Generation, Flashcards, Study Guides.
"""
from __future__ import annotations

import json
import re

from core.llm_client import llm_client
from core.models import DifficultyLevel, Flashcard, MCQ, StudyPack
from security.prompt_injection import sanitize_for_prompt

_SYSTEM = "You are an expert science educator who writes precise, unambiguous quiz questions."


def generate_flashcards(paper_text: str, difficulty: DifficultyLevel, n: int = 6) -> list[Flashcard]:
    prompt = (
        f"Create {n} flashcards (front = question/term, back = answer/definition) "
        f"at {difficulty.value} difficulty, based strictly on this paper. "
        "Respond ONLY as a JSON list of objects with keys 'front' and 'back'.\n\n"
        f"{sanitize_for_prompt(paper_text)}"
    )
    raw = llm_client.generate(prompt, system=_SYSTEM, json_mode=True)
    items = _safe_json_list(raw)
    if items:
        return [Flashcard(front=i.get("front", ""), back=i.get("back", ""), difficulty=difficulty) for i in items]
    return [
        Flashcard(front=f"[MOCK] Key concept #{i+1} of this paper?", back="[MOCK] See paper for full answer.",
                   difficulty=difficulty)
        for i in range(n)
    ]


def generate_mcqs(paper_text: str, difficulty: DifficultyLevel, n: int = 5) -> list[MCQ]:
    prompt = (
        f"Create {n} multiple-choice questions at {difficulty.value} difficulty "
        "strictly based on this paper. Each question has exactly 4 options, one "
        "correct. Respond ONLY as a JSON list of objects with keys "
        "'question', 'options' (list of 4), 'correct_index' (0-3), 'explanation'.\n\n"
        f"{sanitize_for_prompt(paper_text)}"
    )
    raw = llm_client.generate(prompt, system=_SYSTEM, json_mode=True)
    items = _safe_json_list(raw)
    if items:
        return [
            MCQ(
                question=i.get("question", ""),
                options=i.get("options", ["A", "B", "C", "D"])[:4],
                correct_index=int(i.get("correct_index", 0)),
                difficulty=difficulty,
                explanation=i.get("explanation", ""),
            )
            for i in items
        ]
    return [
        MCQ(
            question=f"[MOCK] Question #{i+1} about this paper's main contribution?",
            options=["Option A", "Option B", "Option C", "Option D"],
            correct_index=0,
            difficulty=difficulty,
            explanation="[MOCK] Configure GEMINI_API_KEY for real questions.",
        )
        for i in range(n)
    ]


def generate_short_answer(paper_text: str, n: int = 4) -> list[str]:
    prompt = (
        f"Write {n} short-answer (1-2 sentence response expected) study "
        f"questions about this paper, one per line:\n\n{sanitize_for_prompt(paper_text)}"
    )
    raw = llm_client.generate(prompt, system=_SYSTEM)
    lines = [l.strip("-•* ") for l in raw.splitlines() if l.strip()]
    return lines[:n] if lines else [f"[MOCK] Short-answer question #{i+1}" for i in range(n)]


def generate_study_guide(paper_text: str) -> str:
    prompt = (
        "Write a structured STUDY GUIDE (headed sections: Key Concepts, "
        "Important Terms, Main Takeaways, Common Misconceptions) for this paper:\n\n"
        f"{sanitize_for_prompt(paper_text)}"
    )
    return llm_client.generate(prompt, system=_SYSTEM)


def build_study_pack(paper_text: str, difficulty: DifficultyLevel = DifficultyLevel.MEDIUM) -> StudyPack:
    return StudyPack(
        flashcards=generate_flashcards(paper_text, difficulty),
        mcqs=generate_mcqs(paper_text, difficulty),
        short_answer=generate_short_answer(paper_text),
        study_guide=generate_study_guide(paper_text),
    )


def _safe_json_list(raw: str) -> list[dict]:
    try:
        cleaned = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE).strip()
        data = json.loads(cleaned)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
