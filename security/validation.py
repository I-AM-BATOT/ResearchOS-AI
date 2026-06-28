"""
security/validation.py
Input validation for PDF uploads, free-text queries, and MCP tool requests.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.config import settings, get_logger

logger = get_logger("security.validation")

ALLOWED_PDF_MIME_PREFIXES = ("application/pdf",)
PDF_MAGIC_BYTES = b"%PDF-"
MAX_QUERY_LENGTH = 4000


@dataclass
class ValidationResult:
    is_valid: bool
    reason: str = "ok"


def validate_pdf_upload(filename: str, file_bytes: bytes) -> ValidationResult:
    """Rejects corrupt files, non-PDF files, and oversized files."""
    if not filename.lower().endswith(".pdf"):
        return ValidationResult(False, "File must have a .pdf extension")

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_pdf_mb:
        return ValidationResult(
            False, f"File is {size_mb:.1f}MB, exceeds the {settings.max_pdf_mb}MB limit"
        )

    if not file_bytes.startswith(PDF_MAGIC_BYTES):
        return ValidationResult(False, "File does not appear to be a valid PDF (bad magic bytes)")

    if len(file_bytes) < 100:
        return ValidationResult(False, "File is suspiciously small / likely corrupt")

    return ValidationResult(True)


def validate_query(query: str) -> ValidationResult:
    """Validates free-text chat/search queries."""
    if query is None or not query.strip():
        return ValidationResult(False, "Query cannot be empty")
    if len(query) > MAX_QUERY_LENGTH:
        return ValidationResult(False, f"Query exceeds max length of {MAX_QUERY_LENGTH} characters")
    return ValidationResult(True)


def validate_mcp_tool_request(tool_name: str, args: dict) -> ValidationResult:
    """Basic schema sanity-checking before dispatching to an MCP tool."""
    if not tool_name or not isinstance(tool_name, str):
        return ValidationResult(False, "Missing tool name")
    if not isinstance(args, dict):
        return ValidationResult(False, "Tool arguments must be a JSON object")
    for key, value in args.items():
        if isinstance(value, str) and len(value) > 8000:
            return ValidationResult(False, f"Argument '{key}' is too long")
    return ValidationResult(True)
