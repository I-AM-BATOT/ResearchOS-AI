"""
agents/memory_agent.py
Memory Agent: stores previous papers, research topics, generated insights,
research interests, and conversation history. Provides persistent memory,
semantic retrieval, and context awareness to every other agent.
"""
from __future__ import annotations

from typing import Any, Optional

from agents.base import BaseAgent
from core.models import AgentName
from memory.memory_store import memory_store


class MemoryAgent(BaseAgent):
    name = AgentName.MEMORY

    def plan(self, task_input: dict[str, Any]) -> dict[str, Any]:
        op = task_input.get("operation", "search")
        return {"summary": f"Memory operation: {op}"}

    def execute(self, task_input: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        op = task_input.get("operation", "search")

        if op == "store":
            record = memory_store.remember(
                kind=task_input["kind"], text=task_input["text"], metadata=task_input.get("metadata", {})
            )
            return {"record_id": record.record_id}

        if op == "search":
            records = memory_store.recall(
                task_input["query"], top_k=task_input.get("top_k", 5), kind=task_input.get("kind")
            )
            return {"records": [r.model_dump() for r in records]}

        if op == "update":
            ok = memory_store.update(
                task_input["record_id"], text=task_input.get("text"), metadata=task_input.get("metadata")
            )
            return {"updated": ok}

        if op == "delete":
            ok = memory_store.forget(task_input["record_id"])
            return {"deleted": ok}

        if op == "list":
            records = memory_store.all_records(kind=task_input.get("kind"))
            return {"records": [r.model_dump() for r in records]}

        return {"error": f"Unknown memory operation: {op}"}

    def verify(self, task_input: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
        if "error" in result:
            return False, [result["error"]]
        return True, []

    # Convenience helpers used directly by the Coordinator / UI (bypassing
    # the full plan/execute/verify/reflect ceremony for simple lookups).
    @staticmethod
    def context_for_topic(topic: str, top_k: int = 5) -> list[dict]:
        return [r.model_dump() for r in memory_store.recall(topic, top_k=top_k)]
