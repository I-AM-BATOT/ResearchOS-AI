"""
core/models.py
Shared Pydantic models used across agents, MCP tools, memory, and the UI.

Keeping these in one place means every agent speaks the same "language"
when passing structured data through the Coordinator.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #

class VerificationStatus(str, Enum):
    VERIFIED = "Verified"
    QUESTIONABLE = "Questionable"
    NEEDS_REVIEW = "Needs Review"


class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class AgentName(str, Enum):
    COORDINATOR = "Coordinator"
    PAPER_READER = "PaperReader"
    RESEARCH_EXPLAINER = "ResearchExplainer"
    FACT_CHECKER = "FactChecker"
    RELATED_WORK = "RelatedWork"
    LITERATURE_REVIEW = "LiteratureReview"
    RESEARCH_GAP = "ResearchGap"
    QUIZ_TEACHING = "QuizTeaching"
    PRESENTATION = "Presentation"
    MEMORY = "Memory"


class WorkflowStage(str, Enum):
    PLAN = "PLAN"
    EXECUTE = "EXECUTE"
    VERIFY = "VERIFY"
    REFLECT = "REFLECT"
    RESPOND = "RESPOND"


# --------------------------------------------------------------------------- #
# Paper structures
# --------------------------------------------------------------------------- #

class PaperSection(BaseModel):
    name: str
    content: str = ""


class PaperMetadata(BaseModel):
    title: str = "Untitled"
    authors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    publication_year: Optional[int] = None
    venue: Optional[str] = None
    source_filename: Optional[str] = None


class StructuredPaper(BaseModel):
    """The canonical representation produced by the Paper Reader Agent."""
    paper_id: str
    metadata: PaperMetadata
    abstract: str = ""
    introduction: str = ""
    methods: str = ""
    results: str = ""
    discussion: str = ""
    conclusion: str = ""
    raw_text: str = ""
    sections_detected: list[str] = Field(default_factory=list)
    page_count: int = 0


# --------------------------------------------------------------------------- #
# Agent communication
# --------------------------------------------------------------------------- #

class AgentMessage(BaseModel):
    """A single hop of agent-to-agent communication, shown in logs + UI."""
    sender: AgentName
    receiver: AgentName
    stage: WorkflowStage
    summary: str
    payload_preview: str = ""
    confidence: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentReflection(BaseModel):
    """Stored self-critique produced at the REFLECT stage."""
    agent: AgentName
    task: str
    reasoning: str
    confidence: float
    quality_notes: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentResult(BaseModel):
    """Generic envelope every agent returns from .run()."""
    agent: AgentName
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    reflection: Optional[AgentReflection] = None
    warnings: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Fact checking
# --------------------------------------------------------------------------- #

class ClaimVerification(BaseModel):
    claim: str
    status: VerificationStatus
    confidence: float
    supporting_evidence: list[str] = Field(default_factory=list)
    notes: str = ""


# --------------------------------------------------------------------------- #
# Related work / literature review
# --------------------------------------------------------------------------- #

class RelatedPaper(BaseModel):
    title: str
    authors: list[str] = Field(default_factory=list)
    year: Optional[int] = None
    link: Optional[str] = None
    relation: str = "related"  # related | prior_work | competing_method | citing | referenced


class LiteratureReview(BaseModel):
    synthesis: str
    research_trends: list[str] = Field(default_factory=list)
    comparative_analysis: str = ""
    state_of_the_art: str = ""
    papers_considered: list[str] = Field(default_factory=list)


class ResearchGap(BaseModel):
    weaknesses: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    missing_experiments: list[str] = Field(default_factory=list)
    novel_ideas: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Teaching / presentation
# --------------------------------------------------------------------------- #

class Flashcard(BaseModel):
    front: str
    back: str
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM


class MCQ(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    explanation: str = ""


class StudyPack(BaseModel):
    flashcards: list[Flashcard] = Field(default_factory=list)
    mcqs: list[MCQ] = Field(default_factory=list)
    short_answer: list[str] = Field(default_factory=list)
    study_guide: str = ""


class SlideContent(BaseModel):
    title: str
    bullets: list[str] = Field(default_factory=list)
    speaker_notes: str = ""


class PresentationPack(BaseModel):
    slides: list[SlideContent] = Field(default_factory=list)
    conference_talk_summary: str = ""
    poster_summary: str = ""


# --------------------------------------------------------------------------- #
# Memory
# --------------------------------------------------------------------------- #

class MemoryRecord(BaseModel):
    record_id: str
    kind: str  # paper_summary | research_interest | generated_output | observation | conversation
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
