"""
tests/test_mcp_tools.py
Tests for the 7 MCP tools, including the offline mock-fallback path
(these run with no network access, exactly like this sandbox).
"""
from mcp.tools import (
    search_arxiv, search_semantic_scholar, retrieve_citation_graph,
    verify_research_claim, compare_papers, generate_bibliography,
    extract_metadata, _parse_arxiv_atom,
)


class TestSearchArxiv:
    def test_returns_results_list(self):
        result = search_arxiv("transformers", max_results=3)
        assert "results" in result
        assert len(result["results"]) == 3

    def test_rejects_empty_query(self):
        result = search_arxiv("")
        assert "error" in result

    def test_parses_real_atom_xml(self):
        atom = (
            '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
            '<entry><title>Test Paper</title><summary>An abstract.</summary>'
            '<published>2020-01-01T00:00:00Z</published>'
            '<author><name>Jane Doe</name></author>'
            '<link rel="alternate" href="https://arxiv.org/abs/test"/></entry></feed>'
        )
        parsed = _parse_arxiv_atom(atom)
        assert parsed[0]["title"] == "Test Paper"
        assert parsed[0]["authors"] == ["Jane Doe"]
        assert parsed[0]["link"] == "https://arxiv.org/abs/test"


class TestSearchSemanticScholar:
    def test_returns_results_list(self):
        result = search_semantic_scholar("graph neural networks", limit=2)
        assert "results" in result
        assert len(result["results"]) == 2


class TestCitationGraph:
    def test_returns_citing_and_referenced(self):
        result = retrieve_citation_graph("Attention Is All You Need")
        assert "citing_papers" in result
        assert "referenced_papers" in result


class TestVerifyResearchClaim:
    def test_returns_status_and_confidence(self):
        result = verify_research_claim("Transformers outperform RNNs on long sequences")
        assert result["status"] in ("Verified", "Questionable", "Needs Review")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_rejects_empty_claim(self):
        result = verify_research_claim("")
        assert "error" in result


class TestComparePapers:
    def test_finds_shared_terminology(self):
        result = compare_papers(
            {"title": "A", "methods": "we use convolutional neural networks for vision"},
            {"title": "B", "methods": "we use convolutional neural networks with attention"},
        )
        assert "convolutional" in result["shared_terminology"]
        assert "networks" in result["shared_terminology"]


class TestGenerateBibliography:
    def test_generates_apa_mla_bibtex(self):
        result = generate_bibliography([
            {"title": "Deep Learning", "authors": ["Ian Goodfellow", "Yoshua Bengio"], "year": 2016}
        ])
        assert "Goodfellow" in result["apa"][0]
        assert "Deep Learning" in result["mla"][0]
        assert "@article" in result["bibtex"][0]

    def test_handles_missing_authors(self):
        result = generate_bibliography([{"title": "Untitled Work"}])
        assert "Unknown Author" in result["apa"][0]


class TestExtractMetadata:
    def test_extract_metadata_from_real_pdf(self, sample_pdf_bytes):
        result = extract_metadata(sample_pdf_bytes, filename="paper.pdf")
        assert "title" in result
        assert "page_count" in result or result.get("mock")

    def test_ignores_generic_placeholder_metadata(self, sample_pdf_bytes):
        """Regression test: reportlab (and many real-world PDF generators)
        stamp generic placeholder metadata like Title='untitled' and
        Author='anonymous'. These must not be trusted over the filename."""
        result = extract_metadata(sample_pdf_bytes, filename="my_real_paper.pdf")
        if not result.get("mock"):
            assert result["title"].lower() != "untitled"
            assert "anonymous" not in [a.lower() for a in result["authors"]]
