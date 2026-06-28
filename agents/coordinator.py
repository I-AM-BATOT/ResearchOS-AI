"""
agents/coordinator.py
Coordinator Agent: the entry point for every user request.

Workflow: PLAN -> DELEGATE -> VERIFY -> REFLECT -> RESPOND

The Coordinator builds an execution plan, delegates to the appropriate
specialist agents in sequence (publishing real agent-to-agent handoff
messages to the event bus), aggregates their outputs, and produces the
final report. This is the only agent the Streamlit UI calls directly for
multi-step workflows (e.g. "Full Analysis" or "Build a Literature Review").
"""
from __future__ import annotations

from typing import Any, Optional

from agents.base import BaseAgent
from agents.fact_checker import FactCheckerAgent
from agents.literature_review import LiteratureReviewAgent
from agents.memory_agent import MemoryAgent
from agents.paper_reader import PaperReaderAgent
from agents.presentation import PresentationAgent
from agents.quiz_teaching import QuizTeachingAgent
from agents.related_work import RelatedWorkAgent
from agents.research_explainer import ResearchExplainerAgent
from agents.research_gap import ResearchGapAgent
from core.models import AgentName, AgentResult
from security.validation import validate_pdf_upload


class CoordinatorAgent(BaseAgent):
    name = AgentName.COORDINATOR

    def __init__(self) -> None:
        super().__init__()
        self.paper_reader = PaperReaderAgent()
        self.explainer = ResearchExplainerAgent()
        self.fact_checker = FactCheckerAgent()
        self.related_work = RelatedWorkAgent()
        self.lit_review = LiteratureReviewAgent()
        self.research_gap = ResearchGapAgent()
        self.quiz_teaching = QuizTeachingAgent()
        self.presentation = PresentationAgent()
        self.memory = MemoryAgent()

    def plan(self, task_input: dict[str, Any]) -> dict[str, Any]:
        workflow = task_input.get("workflow", "full_analysis")
        return {"summary": f"Coordinate '{workflow}' workflow across specialist agents."}

    def execute(self, task_input: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        workflow = task_input.get("workflow", "full_analysis")
        if workflow == "full_analysis":
            return self._full_analysis(task_input)
        if workflow == "literature_review":
            return self._literature_review(task_input)
        raise ValueError(f"Unknown workflow: {workflow}")

    def verify(self, task_input: dict[str, Any], result: dict[str, Any]) -> tuple[bool, list[str]]:
        agent_results: dict[str, AgentResult] = result.get("_agent_results", {})
        failed = [name for name, r in agent_results.items() if not r.success]

        warnings: list[str] = []
        for name in failed:
            sub_result = agent_results[name]
            detail = (
                (isinstance(sub_result.data, dict) and sub_result.data.get("error"))
                or (sub_result.warnings[0] if sub_result.warnings else "unknown issue")
            )
            warnings.append(f"{name} agent failed: {detail}")

        # The Paper Reader is foundational: every other agent in this workflow
        # consumes its output. If it failed, downstream agents may have
        # nominally "succeeded" while operating on empty/garbage input --
        # the overall result is not trustworthy even if most agents ran.
        paper_reader_result = agent_results.get("paper_reader")
        if paper_reader_result is not None and not paper_reader_result.success:
            return False, warnings

        if not agent_results:
            return True, warnings
        return len(failed) < len(agent_results), warnings

    # ------------------------------------------------------------------ #
    # Workflow: ingest a single PDF and run the full pipeline
    # ------------------------------------------------------------------ #
    def _full_analysis(self, task_input: dict[str, Any]) -> dict[str, Any]:
        pdf_bytes: bytes = task_input["pdf_bytes"]
        filename: str = task_input.get("filename", "uploaded.pdf")
        difficulty: str = task_input.get("difficulty", "Medium")
        n_slides: int = task_input.get("n_slides", 8)

        validation = validate_pdf_upload(filename, pdf_bytes)
        if not validation.is_valid:
            return {"error": validation.reason, "_agent_results": {}}

        agent_results: dict[str, AgentResult] = {}

        # Coordinator -> Paper Reader
        self.paper_reader.handoff(AgentName.COORDINATOR, "Coordinator dispatching PDF for extraction")
        reader_result = self.paper_reader.run({"pdf_bytes": pdf_bytes, "filename": filename}, sender=self.name)
        agent_results["paper_reader"] = reader_result
        structured_paper = reader_result.data.get("structured_paper", {})
        paper_text = structured_paper.get("raw_text", "")
        title = structured_paper.get("metadata", {}).get("title", filename)

        # Paper Reader -> Research Explainer
        self.explainer.handoff(AgentName.PAPER_READER, f"Paper Reader handing '{title}' to Research Explainer")
        explainer_result = self.explainer.run({"paper_text": paper_text}, sender=AgentName.PAPER_READER)
        agent_results["research_explainer"] = explainer_result

        # Paper Reader -> Fact Checker
        self.fact_checker.handoff(AgentName.PAPER_READER, f"Paper Reader handing '{title}' to Fact Checker")
        fact_result = self.fact_checker.run({"paper_text": paper_text}, sender=AgentName.PAPER_READER)
        agent_results["fact_checker"] = fact_result

        # Fact Checker -> Related Work
        self.related_work.handoff(AgentName.FACT_CHECKER, "Fact Checker handing off to Related Work discovery")
        related_result = self.related_work.run(
            {"topic": title, "max_results": task_input.get("max_related", 6)}, sender=AgentName.FACT_CHECKER
        )
        agent_results["related_work"] = related_result

        # Related Work -> Research Gap
        self.research_gap.handoff(AgentName.RELATED_WORK, "Related Work handing off to Research Gap analysis")
        gap_result = self.research_gap.run({"paper_text": paper_text}, sender=AgentName.RELATED_WORK)
        agent_results["research_gap"] = gap_result

        # Coordinator -> Quiz/Teaching (parallel-conceptually, run sequentially here)
        self.quiz_teaching.handoff(AgentName.COORDINATOR, "Coordinator dispatching to Quiz/Teaching")
        quiz_result = self.quiz_teaching.run({"paper_text": paper_text, "difficulty": difficulty}, sender=self.name)
        agent_results["quiz_teaching"] = quiz_result

        # Research Gap -> Presentation
        self.presentation.handoff(AgentName.RESEARCH_GAP, "Research Gap handing off to Presentation Agent")
        pres_result = self.presentation.run({"paper_text": paper_text, "n_slides": n_slides}, sender=AgentName.RESEARCH_GAP)
        agent_results["presentation"] = pres_result

        # Presentation -> Coordinator (final aggregation)
        self.handoff(AgentName.PRESENTATION, "Presentation Agent returning final materials to Coordinator")

        # Memory: remember this paper + its insights for future context-aware sessions
        self.memory.run({
            "operation": "store", "kind": "paper_summary",
            "text": f"{title}: {explainer_result.data.get('executive_summary', '')}",
            "metadata": {"paper_id": structured_paper.get("paper_id"), "filename": filename},
        }, sender=self.name)

        return {
            "structured_paper": structured_paper,
            "summaries": explainer_result.data,
            "fact_check": fact_result.data,
            "related_work": related_result.data,
            "research_gap": gap_result.data,
            "study_pack": quiz_result.data,
            "presentation": pres_result.data,
            "_agent_results": agent_results,
            "human_review_notice": "Research findings should be independently verified.",
        }

    # ------------------------------------------------------------------ #
    # Workflow: combine multiple already-read papers into a review
    # ------------------------------------------------------------------ #
    def _literature_review(self, task_input: dict[str, Any]) -> dict[str, Any]:
        papers: list[dict] = task_input["papers"]
        agent_results: dict[str, AgentResult] = {}

        self.lit_review.handoff(AgentName.COORDINATOR, f"Coordinator dispatching {len(papers)} papers to Literature Review Agent")
        review_result = self.lit_review.run({"papers": papers}, sender=self.name)
        agent_results["literature_review"] = review_result

        return {
            "literature_review": review_result.data,
            "_agent_results": agent_results,
            "human_review_notice": "Research findings should be independently verified.",
        }
