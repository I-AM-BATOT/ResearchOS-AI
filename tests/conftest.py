"""
tests/conftest.py
Shared pytest fixtures. Forces MOCK mode for all tests (deterministic,
no API keys / network required) and provides a minimal real PDF fixture
generated on the fly with reportlab.
"""
import io
import os

import pytest

os.environ["FORCE_MOCK_MODE"] = "true"
os.environ.setdefault("MEMORY_DIR", "./.test_researchos_memory")


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Generates a tiny real PDF with section headings, so PaperReaderAgent's
    section-segmentation logic is exercised against an actual PDF, not a stub."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    lines = [
        "Abstract",
        "This paper demonstrates a novel method that achieves state-of-the-art results.",
        "Introduction",
        "Prior work has explored related approaches with limited success.",
        "Methods",
        "We use a transformer-based architecture trained on a large corpus.",
        "Results",
        "Our method improves accuracy by 15% over the previous best baseline.",
        "Discussion",
        "These results suggest the approach generalizes well across domains.",
        "Conclusion",
        "We presented a new method and showed significant improvements.",
    ]
    y = 750
    for line in lines:
        c.drawString(72, y, line)
        y -= 20
    c.save()
    return buf.getvalue()


@pytest.fixture
def sample_paper_text() -> str:
    return (
        "This paper demonstrates a novel transformer-based method that "
        "achieves state-of-the-art results, improving accuracy by 15% over "
        "the previous best baseline on three benchmark datasets. We show that "
        "the approach generalizes well across domains and outperforms prior work."
    )
