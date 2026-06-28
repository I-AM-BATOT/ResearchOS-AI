"""
skills/fact_verification.py
Fact Verification Skill: Claim Verification, Evidence Collection, Confidence Estimation.
"""
from __future__ import annotations

import re

from core.models import ClaimVerification, VerificationStatus
from mcp.tools import verify_research_claim

_CLAIM_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def extract_claims(paper_text: str, max_claims: int = 8) -> list[str]:
    """Naive sentence-level claim extraction: prioritizes sentences with
    quantitative / causal language, which tend to be checkable claims."""
    sentences = [s.strip() for s in _CLAIM_SPLIT_RE.split(paper_text) if len(s.strip()) > 30]
    signal_words = ("show", "demonstrate", "outperform", "achieve", "%", "significant",
                     "improve", "reduce", "increase", "state-of-the-art", "novel")
    scored = sorted(
        sentences,
        key=lambda s: sum(w in s.lower() for w in signal_words),
        reverse=True,
    )
    return scored[:max_claims] if scored else sentences[:max_claims]


def verify_claims(claims: list[str]) -> list[ClaimVerification]:
    results = []
    for claim in claims:
        tool_result = verify_research_claim(claim)
        results.append(ClaimVerification(
            claim=claim,
            status=VerificationStatus(tool_result.get("status", "Needs Review")),
            confidence=float(tool_result.get("confidence", 0.5)),
            supporting_evidence=tool_result.get("supporting_evidence", []),
            notes=tool_result.get("note", ""),
        ))
    return results
