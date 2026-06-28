"""
agents/paper_reader.py
Paper Reader Agent: extracts PDF text, parses sections (Abstract,
Introduction, Methods, Results, Discussion, Conclusion), and produces a
StructuredPaper -- the canonical representation every downstream agent
consumes.
"""
from __future__ import annotations

import io
import re
import uuid
from typing import Any

from agents.base import BaseAgent
from core.models import AgentName, PaperMetadata, StructuredPaper
from mcp.tools import extract_metadata
from security.pii import mask_pii
from security.prompt_injection import scan_text

_SECTION_PATTERNS = {
    "abstract": r"abstract",
    "introduction": r"introduction|background",
    "methods": r"methods?|methodology|materials and methods|approach",
    "results": r"results?|findings|experiments?(\s+and\s+results)?|evaluation",
    "discussion": r"discussion",
    "conclusion": r"conclusions?|concluding remarks|summary and conclusion",
}


class PaperReaderAgent(BaseAgent):
    name = AgentName.PAPER_READER

    def plan(self, task_input: dict[str, Any]) -> dict[str, Any]:
        return {"summary": "Extract text from PDF and segment into standard sections."}

    def execute(self, task_input: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        pdf_bytes: bytes = task_input["pdf_bytes"]
        filename: str = task_input.get("filename", "uploaded.pdf")

        raw_text, page_count = self._extract_text(pdf_bytes)

        # Run injection + PII checks on the extracted text before anything
        # downstream ever sees it -- a malicious PDF is just as much an
        # attack surface as a chat message.
        injection_scan = scan_text(raw_text)
        pii_result = mask_pii(raw_text)

        sections = self._segment_sections(raw_text)
        metadata_dict = extract_metadata(pdf_bytes, filename=filename)

        structured = StructuredPaper(
            paper_id=str(uuid.uuid4()),
            metadata=PaperMetadata(
                title=metadata_dict.get("title") or filename,
                authors=metadata_dict.get("authors", []),
                keywords=metadata_dict.get("keywords", []),
                publication_year=metadata_dict.get("publication_year"),
                venue=metadata_dict.get("venue"),
                source_filename=filename,
            ),
            abstract=sections.get("abstract", ""),
            introduction=sections.get("introduction", ""),
            methods=sections.get("methods", ""),
            results=sections.get("results", ""),
            discussion=sections.get("discussion", ""),
            conclusion=sections.get("conclusion", ""),
            raw_text=raw_text,
            sections_detected=list(sections.keys()),
            page_count=page_count,
        )

        return {
            "structured_paper": structured.model_dump(),
            "injection_flagged": injection_scan.is_suspicious,
            "injection_categories": injection_scan.matched_categories,
            "pii_found": pii_result.found,
        }

    def verify(self, task_input: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
        warnings = []
        paper = result.get("structured_paper", {})
        if not paper.get("raw_text"):
            warnings.append("No text could be extracted from this PDF (it may be scanned/image-only).")
        if len(paper.get("sections_detected", [])) < 2:
            warnings.append("Fewer than 2 standard sections were detected; this may not be a typical research paper.")
        if result.get("injection_flagged"):
            warnings.append(
                f"Potential prompt-injection patterns detected inside the PDF text: "
                f"{result.get('injection_categories')}. Content will be sandboxed before reaching the LLM."
            )
        ok = bool(paper.get("raw_text"))
        return ok, warnings

    # ------------------------------------------------------------------ #
    @staticmethod
    def _extract_text(pdf_bytes: bytes) -> tuple[str, int]:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(pdf_bytes))
        text_parts = []
        for page in reader.pages:
            try:
                text_parts.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(text_parts), len(reader.pages)

    @staticmethod
    def _segment_sections(raw_text: str) -> dict[str, str]:
        """Splits raw text into sections using heading-line detection.
        Heuristic, not perfect -- handles the common case of a heading on
        its own line (typical of arXiv-style single-column PDFs)."""
        if not raw_text.strip():
            return {}

        lines = raw_text.splitlines()
        heading_positions: list[tuple[int, str]] = []

        for idx, line in enumerate(lines):
            stripped = line.strip().strip(":").lower()
            if not stripped or len(stripped) > 40:
                continue
            for section, pattern in _SECTION_PATTERNS.items():
                if re.fullmatch(rf"({pattern})", stripped) or re.fullmatch(rf"\d+\.?\s*({pattern})", stripped):
                    heading_positions.append((idx, section))
                    break

        if not heading_positions:
            # Fallback: no clear headings found -- treat the whole document
            # as a single "abstract"-like blob so summarization can still run.
            return {"abstract": raw_text[:4000]}

        sections: dict[str, str] = {}
        for i, (line_idx, section) in enumerate(heading_positions):
            end_idx = heading_positions[i + 1][0] if i + 1 < len(heading_positions) else len(lines)
            content = "\n".join(lines[line_idx + 1:end_idx]).strip()
            if content:
                sections[section] = (sections.get(section, "") + "\n" + content).strip()
        return sections
