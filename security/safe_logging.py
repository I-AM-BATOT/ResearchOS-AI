"""
security/safe_logging.py
A logging filter that scrubs secrets, API keys, and PII before any record
is emitted -- including by third-party libraries that log through the
standard `logging` module.
"""
from __future__ import annotations

import logging
import re

from security.pii import mask_pii

_SECRET_PATTERNS = [
    re.compile(r"(api[_-]?key\s*[=:]\s*)([A-Za-z0-9\-_]{8,})", re.IGNORECASE),
    re.compile(r"(GEMINI_API_KEY\s*[=:]\s*)([A-Za-z0-9\-_]{8,})", re.IGNORECASE),
    re.compile(r"(Bearer\s+)([A-Za-z0-9\-_.]{10,})", re.IGNORECASE),
    re.compile(r"(sk-[A-Za-z0-9]{10,})"),
]


def scrub_secrets(message: str) -> str:
    scrubbed = message
    for pattern in _SECRET_PATTERNS:
        scrubbed = pattern.sub(lambda m: m.group(1) + "[REDACTED]" if m.lastindex and m.lastindex >= 2 else "[REDACTED]", scrubbed)
    return scrubbed


class SafeLoggingFilter(logging.Filter):
    """Attach to any logger/handler to scrub secrets + PII from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        msg = scrub_secrets(msg)
        msg = mask_pii(msg).masked_text
        record.msg = msg
        record.args = ()
        return True


def install_safe_logging() -> None:
    """Call once at app startup to scrub the root logger globally."""
    root = logging.getLogger()
    if not any(isinstance(f, SafeLoggingFilter) for f in root.filters):
        root.addFilter(SafeLoggingFilter())
