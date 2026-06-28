"""
mcp/tools.py
Implementations of the 7 MCP tools required by the spec:

    search_arxiv, search_semantic_scholar, retrieve_citation_graph,
    verify_research_claim, compare_papers, generate_bibliography,
    extract_metadata

Each tool calls a real public API (arXiv / Semantic Scholar) when network
access is available. If the request fails (no network, rate-limited,
offline grading environment, etc.) every tool degrades gracefully to a
clearly-labeled mock response instead of crashing the pipeline -- this
mirrors the LLM mock-mode strategy in core/llm_client.py.

These functions are plain Python callables. mcp/server.py exposes them
over FastAPI/JSON-RPC-style HTTP endpoints; agents/skills can also call
them directly in-process (faster, no HTTP round-trip) via this module.
"""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Optional

import requests

from core.config import get_logger
from security.validation import validate_mcp_tool_request

logger = get_logger("mcp.tools")

ARXIV_API = "http://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"
HTTP_TIMEOUT = 10.0


def _mock_flag(payload: dict) -> dict:
    payload["mock"] = True
    payload["note"] = "[MOCK] Network unavailable or API error — returning offline placeholder data."
    return payload


# --------------------------------------------------------------------------- #
# search_arxiv
# --------------------------------------------------------------------------- #

def search_arxiv(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search arXiv for papers matching `query`.
    Returns: title, authors, abstract, link, publication date for each hit."""
    validation = validate_mcp_tool_request("search_arxiv", {"query": query})
    if not validation.is_valid:
        return {"error": validation.reason}

    try:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
        }
        resp = requests.get(ARXIV_API, params=params, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        return {"results": _parse_arxiv_atom(resp.text), "source": "arxiv.org"}
    except Exception as exc:
        logger.warning("search_arxiv live call failed: %s", exc)
        return _mock_flag({"results": _mock_arxiv_results(query, max_results), "source": "arxiv.org"})


def _parse_arxiv_atom(xml_text: str) -> list[dict]:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    out = []
    for entry in root.findall("atom:entry", ns):
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
        published = entry.findtext("atom:published", default="", namespaces=ns)
        link = ""
        for link_el in entry.findall("atom:link", ns):
            if link_el.attrib.get("rel") == "alternate":
                link = link_el.attrib.get("href", "")
        authors = [
            (a.findtext("atom:name", default="", namespaces=ns) or "").strip()
            for a in entry.findall("atom:author", ns)
        ]
        out.append({
            "title": title,
            "authors": authors,
            "abstract": summary,
            "link": link,
            "published": published,
        })
    return out


def _mock_arxiv_results(query: str, n: int) -> list[dict]:
    return [
        {
            "title": f"Advances in {query.title()}: A Survey (Mock Entry {i + 1})",
            "authors": ["A. Researcher", "B. Scholar"],
            "abstract": f"This is a placeholder abstract about {query} generated offline.",
            "link": f"https://arxiv.org/abs/mock.{i + 1:04d}",
            "published": datetime.utcnow().isoformat(),
        }
        for i in range(n)
    ]


# --------------------------------------------------------------------------- #
# search_semantic_scholar
# --------------------------------------------------------------------------- #

def search_semantic_scholar(query: str, limit: int = 5) -> dict[str, Any]:
    """Find related work via Semantic Scholar.
    Returns: citation information, authors, research influence (citationCount)."""
    validation = validate_mcp_tool_request("search_semantic_scholar", {"query": query})
    if not validation.is_valid:
        return {"error": validation.reason}

    try:
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,citationCount,influentialCitationCount,url",
        }
        resp = requests.get(f"{SEMANTIC_SCHOLAR_API}/paper/search", params=params, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        results = [
            {
                "title": p.get("title"),
                "authors": [a.get("name") for a in p.get("authors", [])],
                "year": p.get("year"),
                "citation_count": p.get("citationCount"),
                "influential_citation_count": p.get("influentialCitationCount"),
                "url": p.get("url"),
            }
            for p in data
        ]
        return {"results": results, "source": "semanticscholar.org"}
    except Exception as exc:
        logger.warning("search_semantic_scholar live call failed: %s", exc)
        return _mock_flag({"results": _mock_semantic_scholar_results(query, limit), "source": "semanticscholar.org"})


def _mock_semantic_scholar_results(query: str, n: int) -> list[dict]:
    return [
        {
            "title": f"{query.title()}: Related Approaches (Mock {i + 1})",
            "authors": ["C. Investigator"],
            "year": 2023 - i,
            "citation_count": 50 - i * 5,
            "influential_citation_count": 5 - i,
            "url": f"https://www.semanticscholar.org/paper/mock{i + 1}",
        }
        for i in range(n)
    ]


# --------------------------------------------------------------------------- #
# retrieve_citation_graph
# --------------------------------------------------------------------------- #

def retrieve_citation_graph(paper_title_or_id: str) -> dict[str, Any]:
    """Analyze the citation network of a paper.
    Returns: citing papers, referenced papers, relationships."""
    validation = validate_mcp_tool_request("retrieve_citation_graph", {"paper": paper_title_or_id})
    if not validation.is_valid:
        return {"error": validation.reason}

    try:
        search_resp = requests.get(
            f"{SEMANTIC_SCHOLAR_API}/paper/search",
            params={"query": paper_title_or_id, "limit": 1, "fields": "paperId,title"},
            timeout=HTTP_TIMEOUT,
        )
        search_resp.raise_for_status()
        hits = search_resp.json().get("data", [])
        if not hits:
            raise ValueError("paper not found on Semantic Scholar")
        paper_id = hits[0]["paperId"]

        citations_resp = requests.get(
            f"{SEMANTIC_SCHOLAR_API}/paper/{paper_id}/citations",
            params={"fields": "title,year", "limit": 10},
            timeout=HTTP_TIMEOUT,
        )
        references_resp = requests.get(
            f"{SEMANTIC_SCHOLAR_API}/paper/{paper_id}/references",
            params={"fields": "title,year", "limit": 10},
            timeout=HTTP_TIMEOUT,
        )
        citing = [c["citingPaper"]["title"] for c in citations_resp.json().get("data", []) if c.get("citingPaper")]
        referenced = [r["citedPaper"]["title"] for r in references_resp.json().get("data", []) if r.get("citedPaper")]
        return {
            "paper": hits[0]["title"],
            "citing_papers": citing,
            "referenced_papers": referenced,
            "source": "semanticscholar.org",
        }
    except Exception as exc:
        logger.warning("retrieve_citation_graph live call failed: %s", exc)
        return _mock_flag({
            "paper": paper_title_or_id,
            "citing_papers": [f"Citing Work {i + 1} (Mock)" for i in range(3)],
            "referenced_papers": [f"Prior Work {i + 1} (Mock)" for i in range(3)],
        })


# --------------------------------------------------------------------------- #
# verify_research_claim
# --------------------------------------------------------------------------- #

def verify_research_claim(claim: str) -> dict[str, Any]:
    """Cross-reference a claim against scholarly sources via Semantic Scholar
    search relevance as a lightweight evidentiary signal.
    Returns: verification result, confidence score, supporting evidence."""
    validation = validate_mcp_tool_request("verify_research_claim", {"claim": claim})
    if not validation.is_valid:
        return {"error": validation.reason}

    try:
        resp = requests.get(
            f"{SEMANTIC_SCHOLAR_API}/paper/search",
            params={"query": claim, "limit": 5, "fields": "title,abstract,year"},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        papers = resp.json().get("data", [])
        evidence = [p["title"] for p in papers if p.get("title")]
        confidence = min(0.95, 0.4 + 0.12 * len(evidence))
        status = "Verified" if len(evidence) >= 3 else ("Questionable" if evidence else "Needs Review")
        return {
            "claim": claim,
            "status": status,
            "confidence": round(confidence, 2),
            "supporting_evidence": evidence,
            "source": "semanticscholar.org",
        }
    except Exception as exc:
        logger.warning("verify_research_claim live call failed: %s", exc)
        return _mock_flag({
            "claim": claim,
            "status": "Needs Review",
            "confidence": 0.5,
            "supporting_evidence": [],
        })


# --------------------------------------------------------------------------- #
# compare_papers
# --------------------------------------------------------------------------- #

def compare_papers(paper_a: dict, paper_b: dict) -> dict[str, Any]:
    """Compare two papers' methods/results/strengths/weaknesses.
    `paper_a` / `paper_b` are dicts with at least `title` and ideally
    `methods`/`results` text (e.g. from a StructuredPaper). This tool itself
    does light structural comparison; an agent layer uses the LLM to turn
    this into prose."""
    def summarize(p: dict) -> dict:
        return {
            "title": p.get("title", "Untitled"),
            "methods_excerpt": (p.get("methods") or "")[:400],
            "results_excerpt": (p.get("results") or "")[:400],
        }

    a, b = summarize(paper_a), summarize(paper_b)
    shared_terms = sorted(
        set(re.findall(r"[a-zA-Z]{5,}", a["methods_excerpt"].lower()))
        & set(re.findall(r"[a-zA-Z]{5,}", b["methods_excerpt"].lower()))
    )[:15]

    return {
        "paper_a": a,
        "paper_b": b,
        "shared_terminology": shared_terms,
        "note": "Structural diff only; pair with ResearchExplainer/LiteratureReview agent for prose comparison.",
    }


# --------------------------------------------------------------------------- #
# generate_bibliography
# --------------------------------------------------------------------------- #

def generate_bibliography(papers: list[dict]) -> dict[str, Any]:
    """Create APA / MLA / BibTeX references for a list of paper metadata dicts."""
    apa, mla, bibtex = [], [], []

    for i, p in enumerate(papers):
        title = p.get("title", "Untitled")
        authors = p.get("authors") or []
        year = p.get("year") or p.get("publication_year") or "n.d."
        author_str = ", ".join(authors) if authors else "Unknown Author"

        apa.append(f"{author_str} ({year}). {title}.")
        mla.append(f"{author_str}. \"{title}.\" {year}.")

        first_author_key = (authors[0].split()[-1] if authors else "unknown").lower()
        cite_key = re.sub(r"[^a-z0-9]", "", first_author_key) + str(year)
        bibtex.append(
            "@article{" + cite_key + f"{i},\n"
            f"  title={{ {title} }},\n"
            f"  author={{ {' and '.join(authors) if authors else 'Unknown'} }},\n"
            f"  year={{ {year} }}\n"
            "}"
        )

    return {"apa": apa, "mla": mla, "bibtex": bibtex}


# --------------------------------------------------------------------------- #
# extract_metadata
# --------------------------------------------------------------------------- #

_PLACEHOLDER_METADATA_VALUES = {
    "untitled", "untitled document", "untitled1", "document", "document1",
    "anonymous", "(anonymous)", "unknown", "n/a", "none", "title", "author",
}


def _is_meaningful(value: str) -> bool:
    """Many PDF generators (including reportlab, used in this project's own
    tests) stamp generic placeholder metadata like Title='untitled' or
    Author='anonymous'. Treat those as absent rather than trusting them over
    a real filename."""
    cleaned = value.strip().lower()
    return bool(cleaned) and len(cleaned) > 2 and cleaned not in _PLACEHOLDER_METADATA_VALUES


def extract_metadata(pdf_bytes: bytes, filename: Optional[str] = None) -> dict[str, Any]:
    """Extract title/authors/keywords/year/venue from a PDF's embedded
    document metadata (not OCR/NLP — that's the Paper Reader Agent's job)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            return _mock_flag({
                "title": filename or "Untitled",
                "authors": [],
                "keywords": [],
                "publication_year": None,
                "venue": None,
            })

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        meta = reader.metadata or {}

        raw_title = (meta.get("/Title") or "").strip()
        title = raw_title if _is_meaningful(raw_title) else (
            filename.rsplit(".", 1)[0] if filename else "Untitled"
        )

        author_field = (meta.get("/Author") or "").strip()
        authors = (
            [a.strip() for a in re.split(r",| and ", author_field) if a.strip()]
            if _is_meaningful(author_field) else []
        )

        keywords_field = meta.get("/Keywords") or ""
        keywords = [k.strip() for k in re.split(r",|;", keywords_field) if k.strip()]
        creation_date = meta.get("/CreationDate") or ""
        year_match = re.search(r"(19|20)\d{2}", creation_date)
        year = int(year_match.group(0)) if year_match else None

        return {
            "title": title,
            "authors": authors,
            "keywords": keywords,
            "publication_year": year,
            "venue": None,
            "page_count": len(reader.pages),
        }
    except Exception as exc:
        logger.warning("extract_metadata failed: %s", exc)
        return _mock_flag({
            "title": filename or "Untitled",
            "authors": [],
            "keywords": [],
            "publication_year": None,
            "venue": None,
        })


# Registry used by mcp/server.py to expose these as named HTTP endpoints,
# and by skills/research.py for direct in-process calls.
TOOL_REGISTRY = {
    "search_arxiv": search_arxiv,
    "search_semantic_scholar": search_semantic_scholar,
    "retrieve_citation_graph": retrieve_citation_graph,
    "verify_research_claim": verify_research_claim,
    "compare_papers": compare_papers,
    "generate_bibliography": generate_bibliography,
    "extract_metadata": extract_metadata,
}
