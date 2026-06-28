"""
agents/fact_checker.py
Fact Checker Agent: verifies claims, statistics, references, and scientific
statements via MCP tools + external sources. Outputs Verified /
Questionable / Needs Review with a confidence score per claim.
"""
from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from core.models import AgentName
from skills.fact_verification import extract_claims, verify_claims


class FactCheckerAgent(BaseAgent):
    name = AgentName.FACT_CHECKER

    def plan(self, task_input: dict[str, Any]) -> dict[str, Any]:
        return {"summary": "Extract checkable claims and cross-reference them against scholarly sources."}

    def execute(self, task_input: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        paper_text = task_input["paper_text"]
        max_claims = task_input.get("max_claims", 6)
        claims = extract_claims(paper_text, max_claims=max_claims)
        verifications = verify_claims(claims)
        return {
            "claims_checked": len(claims),
            "verifications": [v.model_dump() for v in verifications],
        }

    def verify(self, task_input: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
        warnings = []
        if result.get("claims_checked", 0) == 0:
            warnings.append("No checkable claims were found in this text.")
        low_conf = [v for v in result.get("verifications", []) if v["confidence"] < 0.5]
        if low_conf:
            warnings.append(f"{len(low_conf)} claim(s) have low confidence and need human review.")
        return result.get("claims_checked", 0) > 0, warnings
