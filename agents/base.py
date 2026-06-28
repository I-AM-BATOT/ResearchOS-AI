"""
agents/base.py
BaseAgent: every agent in ResearchOS AI implements the same five-stage
workflow required by the spec:

    PLAN -> EXECUTE -> VERIFY -> REFLECT -> RESPOND

Subclasses implement `plan()`, `execute()`, and `verify()`; `reflect()` and
`respond()` have sensible default implementations that subclasses may
override. Every stage transition is published to the shared `event_bus` so
the Streamlit "Architecture" page and terminal logs show real agent-to-agent
communication, not a scripted animation.

This shape deliberately mirrors Google ADK's agent/runner lifecycle
(plan -> tool calls -> response, with reflection as an explicit extra step
for this project) so that swapping `core.llm_client.LLMClient` for an actual
`google.adk` `LlmAgent` + `Runner` later is a drop-in change rather than a
rewrite -- see the NOTE in core/llm_client.py.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from core.config import get_logger
from core.event_bus import event_bus
from core.models import AgentMessage, AgentName, AgentReflection, AgentResult, WorkflowStage
from memory.memory_store import memory_store


class BaseAgent(ABC):
    name: AgentName

    def __init__(self) -> None:
        self.logger = get_logger(f"agent.{self.name.value}")

    # ------------------------------------------------------------------ #
    # Stages every subclass must define
    # ------------------------------------------------------------------ #
    @abstractmethod
    def plan(self, task_input: dict[str, Any]) -> dict[str, Any]:
        """Return a small plan dict describing what this agent intends to do.
        Cheap and fast -- no LLM call required unless genuinely useful."""

    @abstractmethod
    def execute(self, task_input: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        """Do the actual work (call skills / MCP tools / LLM). Returns raw data."""

    def verify(self, task_input: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
        """Sanity-check the execute() output. Default: passes if result is non-empty.
        Subclasses override for domain-specific checks (e.g. FactChecker double-checking
        confidence thresholds)."""
        warnings: list[str] = []
        ok = bool(result)
        if not ok:
            warnings.append("Agent produced an empty result.")
        return ok, warnings

    def reflect(self, task_input: dict[str, Any], result: dict[str, Any], verified: bool) -> AgentReflection:
        """Self-critique step. Default implementation produces a structured
        reflection without an extra LLM call (cheap); override for richer reflection."""
        confidence = 0.85 if verified else 0.45
        reasoning = (
            f"{self.name.value} completed its task with "
            f"{'no' if verified else 'some'} verification concerns."
        )
        quality_notes = "Result passed basic verification." if verified else "Result failed verification checks."
        reflection = AgentReflection(
            agent=self.name,
            task=str(task_input.get("task_summary", self.name.value)),
            reasoning=reasoning,
            confidence=confidence,
            quality_notes=quality_notes,
        )
        memory_store.remember(
            kind="observation",
            text=f"[{self.name.value}] {reasoning} {quality_notes}",
            metadata={"agent": self.name.value, "confidence": confidence},
        )
        return reflection

    # ------------------------------------------------------------------ #
    # Orchestration (shared by all agents -- do not override)
    # ------------------------------------------------------------------ #
    def run(self, task_input: dict[str, Any], *, sender: AgentName = AgentName.COORDINATOR) -> AgentResult:
        start = time.time()
        self.logger.info("PLAN stage starting")
        plan = self.plan(task_input)
        self._publish(sender, WorkflowStage.PLAN, f"Planning: {plan.get('summary', '...')}")

        self.logger.info("EXECUTE stage starting")
        try:
            result = self.execute(task_input, plan)
        except Exception as exc:
            self.logger.exception("EXECUTE stage failed")
            error_message = f"{type(exc).__name__}: {exc}"
            self._publish(sender, WorkflowStage.EXECUTE, f"Execution FAILED: {error_message}")
            return AgentResult(
                agent=self.name, success=False, data={"error": error_message},
                confidence=0.0, warnings=[f"Execution error: {error_message}"],
            )
        self._publish(sender, WorkflowStage.EXECUTE, "Execution complete", payload_preview=str(result)[:160])

        self.logger.info("VERIFY stage starting")
        try:
            verified, warnings = self.verify(task_input, result)
        except Exception as exc:
            self.logger.exception("VERIFY stage failed (treating as unverified, continuing)")
            verified, warnings = False, [f"Verification error: {type(exc).__name__}: {exc}"]
        self._publish(sender, WorkflowStage.VERIFY, f"Verified={verified}" + (f" warnings={warnings}" if warnings else ""))

        self.logger.info("REFLECT stage starting")
        try:
            reflection = self.reflect(task_input, result, verified)
        except Exception as exc:
            self.logger.exception("REFLECT stage failed (continuing without a stored reflection)")
            reflection = AgentReflection(
                agent=self.name, task=str(task_input.get("task_summary", self.name.value)),
                reasoning="Reflection step failed and was skipped.",
                confidence=0.5 if verified else 0.3,
                quality_notes=f"Reflection error: {type(exc).__name__}: {exc}",
            )
        self._publish(sender, WorkflowStage.REFLECT, reflection.quality_notes, confidence=reflection.confidence)

        elapsed = time.time() - start
        self.logger.info("RESPOND stage complete in %.2fs (confidence=%.2f)", elapsed, reflection.confidence)
        self._publish(sender, WorkflowStage.RESPOND, f"Done in {elapsed:.2f}s", confidence=reflection.confidence)

        return AgentResult(
            agent=self.name,
            success=verified,
            data=result,
            confidence=reflection.confidence,
            reflection=reflection,
            warnings=warnings,
        )

    def handoff(self, to: AgentName, summary: str) -> None:
        """Explicit agent-to-agent handoff message (used by Coordinator)."""
        self._publish(to, WorkflowStage.PLAN, summary)

    def _publish(self, counterpart: AgentName, stage: WorkflowStage, summary: str,
                 payload_preview: str = "", confidence: Optional[float] = None) -> None:
        # When this agent is being driven BY a sender (e.g. Coordinator), the
        # message direction is sender->self for PLAN and self->sender for the
        # rest. We keep it simple: always log self<->counterpart.
        sender, receiver = (counterpart, self.name) if stage == WorkflowStage.PLAN else (self.name, counterpart)
        event_bus.publish(AgentMessage(
            sender=sender, receiver=receiver, stage=stage, summary=summary,
            payload_preview=payload_preview, confidence=confidence,
        ))
