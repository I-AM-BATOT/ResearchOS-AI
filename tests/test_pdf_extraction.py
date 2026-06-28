"""
tests/test_pdf_extraction.py
Tests for the Paper Reader Agent's PDF text extraction and section
segmentation, using a real (small, generated) PDF.
"""
from agents.paper_reader import PaperReaderAgent


class TestPaperReaderAgent:
    def test_extracts_text_and_sections(self, sample_pdf_bytes):
        agent = PaperReaderAgent()
        plan = agent.plan({})
        result = agent.execute({"pdf_bytes": sample_pdf_bytes, "filename": "test_paper.pdf"}, plan)

        paper = result["structured_paper"]
        assert paper["raw_text"].strip() != ""
        assert paper["page_count"] == 1
        # At least some of the standard sections should be detected
        assert len(paper["sections_detected"]) >= 2

    def test_verify_flags_short_papers_gracefully(self, sample_pdf_bytes):
        agent = PaperReaderAgent()
        result = agent.execute({"pdf_bytes": sample_pdf_bytes, "filename": "test_paper.pdf"}, {})
        ok, warnings = agent.verify({}, result)
        assert ok is True  # text was extracted, so verification should pass

    def test_full_run_through_base_agent_lifecycle(self, sample_pdf_bytes):
        agent = PaperReaderAgent()
        agent_result = agent.run({"pdf_bytes": sample_pdf_bytes, "filename": "test_paper.pdf"})
        assert agent_result.success is True
        assert agent_result.confidence > 0
        assert agent_result.reflection is not None
