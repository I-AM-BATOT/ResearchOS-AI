"""
security/pii.py
PII detection and masking.

Used in two places:
1. Before logging anything (see security/safe_logging.py) — so emails,
   phone numbers, and other identifiers never hit log files / stdout.
2. Optionally on extracted PDF text before it's sent to external MCP tools
   (e.g. search_semantic_scholar), so author contact details in a paper's
   header don't leak into third-party API query strings.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(\+?\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
IP_ADDRESS_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

_PATTERNS = {
    "email": EMAIL_RE,
    "phone": PHONE_RE,
    "ssn": SSN_RE,
    "credit_card": CREDIT_CARD_RE,
    "ip_address": IP_ADDRESS_RE,
}


@dataclass
class PIIMaskResult:
    masked_text: str
    found: dict[str, int] = field(default_factory=dict)


def mask_pii(text: str) -> PIIMaskResult:
    """Replaces detected PII with category tags, e.g. user@x.com -> [EMAIL_REDACTED]."""
    if not text:
        return PIIMaskResult(masked_text=text)

    found: dict[str, int] = {}
    masked = text

    for category, pattern in _PATTERNS.items():
        matches = pattern.findall(masked)
        count = len(matches) if matches else 0
        if count:
            found[category] = count
            masked = pattern.sub(f"[{category.upper()}_REDACTED]", masked)

    return PIIMaskResult(masked_text=masked, found=found)


def contains_pii(text: str) -> bool:
    return any(p.search(text) for p in _PATTERNS.values()) if text else False
