"""
tests/test_agents.py
Tests for agent routing/orchestration, fact checking, related work discovery,
presentation generation, and literature review generation. All run in
FORCE_MOCK_MODE (set in conftest.py), so no API key or network is required
and outputs are deterministic-shaped (mock text), but every code path —
plan/execute/verify/reflect, MCP tool calls with mock fallback, and
aggregation — is genuinely exercised.
"""
from unittest.mock import patch

from agents.coordinator import CoordinatorAgent
from agents.fact_checker import FactCheckerAgent
from agents.literature_review import LiteratureReviewAgent
from agents.presentation import PresentationAgent
from agents.related_work import RelatedWorkAgent
from core.event_bus import event_bus
from core.models import AgentName


class TestBaseAgentLifecycle:
    def test_fact_checker_runs_full_lifecycle(self, sample_paper_text):
        agent = FactCheckerAgent()
        result = agent.run({"paper_text": sample_paper_text})
        assert result.agent == AgentName.FACT_CHECKER
        assert result.data["claims_checked"] > 0
        assert len(result.data["verifications"]) > 0
        assert result.reflection is not None


class TestFactChecker:
    def test_extracts_and_verifies_claims(self, sample_paper_text):
        agent = FactCheckerAgent()
        result = agent.execute({"paper_text": sample_paper_text}, {})
        assert result["claims_checked"] > 0
        for v in result["verifications"]:
            assert v["status"] in ("Verified", "Questionable", "Needs Review")
            assert 0.0 <= v["confidence"] <= 1.0


class TestRelatedWork:
    def test_discovers_related_papers(self):
        agent = RelatedWorkAgent()
        result = agent.execute({"topic": "transformer attention mechanisms", "max_results": 4}, {})
        assert len(result["related_papers"]) > 0
        assert "research_map" in result

    def test_verify_fails_on_empty_results(self):
        agent = RelatedWorkAgent()
        ok, warnings = agent.verify({}, {"related_papers": [], "research_map": {}})
        assert ok is False
        assert len(warnings) > 0


class TestPresentation:
    def test_generates_slides_and_scripts(self, sample_paper_text):
        agent = PresentationAgent()
        result = agent.execute({"paper_text": sample_paper_text, "n_slides": 6}, {})
        assert len(result["slides"]) > 0
        assert result["conference_talk_summary"]
        assert result["poster_summary"]


class TestLiteratureReview:
    def test_synthesizes_across_papers(self, sample_paper_text):
        agent = LiteratureReviewAgent()
        papers = [
            {"metadata": {"title": "Paper One"}, "abstract": sample_paper_text},
            {"metadata": {"title": "Paper Two"}, "abstract": "A different approach using CNNs for vision tasks."},
        ]
        result = agent.execute({"papers": papers}, {})
        assert result["synthesis"]
        assert "Paper One" in result["papers_considered"]
        assert "Paper Two" in result["papers_considered"]


class TestCoordinatorRouting:
    def test_full_analysis_workflow_delegates_to_all_agents(self, sample_pdf_bytes):
        event_bus.clear()
        coordinator = CoordinatorAgent()
        result = coordinator.run({
            "workflow": "full_analysis",
            "pdf_bytes": sample_pdf_bytes,
            "filename": "test_paper.pdf",
        })
        assert "structured_paper" in result.data
        assert "summaries" in result.data
        assert "fact_check" in result.data
        assert "related_work" in result.data
        assert "research_gap" in result.data
        assert "study_pack" in result.data
        assert "presentation" in result.data
        assert result.data["human_review_notice"]

        # Confirm real agent-to-agent messages were published for this run
        history = event_bus.history()
        senders_receivers = {(m.sender, m.receiver) for m in history}
        assert (AgentName.COORDINATOR, AgentName.PAPER_READER) in senders_receivers

    def test_literature_review_workflow(self, sample_paper_text):
        coordinator = CoordinatorAgent()
        papers = [{"metadata": {"title": "Paper A"}, "abstract": sample_paper_text}]
        result = coordinator.run({"workflow": "literature_review", "papers": papers})
        assert "literature_review" in result.data

    def test_rejects_invalid_pdf(self):
        coordinator = CoordinatorAgent()
        result = coordinator.run({
            "workflow": "full_analysis",
            "pdf_bytes": b"not a real pdf",
            "filename": "bad.pdf",
        })
        assert "error" in result.data

    def test_surfaces_real_error_when_paper_reader_throws(self, sample_pdf_bytes):
        """Regression test: an unexpected exception inside any agent's execute()
        must not silently produce an empty result.data with the real cause
        buried only in a warning the caller might never reach. The Coordinator
        must (1) report overall success=False when the foundational Paper
        Reader fails, and (2) surface the actual exception message in
        result.warnings so it's visible to the UI instead of disappearing."""
        coordinator = CoordinatorAgent()
        with patch.object(coordinator.paper_reader, "execute",
                           side_effect=RuntimeError("simulated real-world failure")):
            result = coordinator.run({
                "workflow": "full_analysis",
                "pdf_bytes": sample_pdf_bytes,
                "filename": "test.pdf",
            })

        assert result.success is False
        assert any("simulated real-world failure" in w for w in result.warnings)
        # structured_paper key must still be present (even if empty) so the
        # UI's `result.data.get("structured_paper")` never raises a KeyError.
        assert "structured_paper" in result.data

    def test_survives_memory_backend_failure_during_reflect(self, sample_pdf_bytes):
        """Regression test for a real production bug: every agent's default
        reflect() step writes to memory. If the memory backend raises (e.g.
        ChromaDB's embedding function hitting a ConnectTimeout trying to
        download its model on a restricted network), that write happens
        completely outside the EXECUTE-stage try/except -- it must not be
        allowed to abort the whole pipeline."""
        import memory.memory_store as ms

        with patch.object(ms.memory_store.backend, "store",
                           side_effect=ConnectionError(
                               "ConnectTimeout: _ssl.c:1063: The handshake operation timed out in upsert.")):
            coordinator = CoordinatorAgent()
            result = coordinator.run({
                "workflow": "full_analysis",
                "pdf_bytes": sample_pdf_bytes,
                "filename": "test.pdf",
            })

        assert result.data.get("structured_paper", {}).get("paper_id")
        assert result.data.get("summaries")
        assert result.data.get("presentation")
