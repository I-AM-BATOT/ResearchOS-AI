"""
mcp/server.py
The ResearchOS MCP Server -- a FastAPI app exposing the 7 required tools
as JSON-RPC-style HTTP endpoints, plus a `/mcp/tools` discovery endpoint
that lists available tools and their schemas (the convention MCP clients
expect).

Run standalone:
    uvicorn mcp.server:app --host 0.0.0.0 --port 8765

The Streamlit app calls these tools in-process via mcp/tools.py for speed
(no HTTP round trip needed within the same Python process), but this server
is what makes the tool layer independently deployable / usable by any other
MCP-compatible client (Claude Desktop, another agent framework, etc.).
"""
from __future__ import annotations

import base64
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.config import settings, get_logger
from mcp.tools import TOOL_REGISTRY
from security.validation import validate_mcp_tool_request

logger = get_logger("mcp.server")

app = FastAPI(
    title="ResearchOS AI - MCP Server",
    description="MCP tool server for arXiv / Semantic Scholar research tools.",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_TOOL_SCHEMAS: dict[str, dict] = {
    "search_arxiv": {"description": "Search arXiv for papers.", "args": {"query": "str", "max_results": "int (optional)"}},
    "search_semantic_scholar": {"description": "Find related work via Semantic Scholar.", "args": {"query": "str", "limit": "int (optional)"}},
    "retrieve_citation_graph": {"description": "Analyze a paper's citation network.", "args": {"paper_title_or_id": "str"}},
    "verify_research_claim": {"description": "Cross-reference a claim against scholarly sources.", "args": {"claim": "str"}},
    "compare_papers": {"description": "Compare two papers.", "args": {"paper_a": "dict", "paper_b": "dict"}},
    "generate_bibliography": {"description": "Create APA/MLA/BibTeX references.", "args": {"papers": "list[dict]"}},
    "extract_metadata": {"description": "Extract metadata from a PDF.", "args": {"pdf_base64": "str", "filename": "str (optional)"}},
}


class ToolCallRequest(BaseModel):
    tool: str
    args: dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@app.get("/mcp/tools")
def list_tools() -> dict:
    """MCP-style tool discovery endpoint."""
    return {"tools": _TOOL_SCHEMAS}


@app.post("/mcp/call")
def call_tool(request: ToolCallRequest) -> dict:
    """Generic dispatcher: POST {"tool": "search_arxiv", "args": {"query": "..."}}"""
    validation = validate_mcp_tool_request(request.tool, request.args)
    if not validation.is_valid:
        raise HTTPException(status_code=400, detail=validation.reason)

    if request.tool not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {request.tool}")

    fn = TOOL_REGISTRY[request.tool]
    try:
        args = dict(request.args)
        if request.tool == "extract_metadata" and "pdf_base64" in args:
            args["pdf_bytes"] = base64.b64decode(args.pop("pdf_base64"))
        result = fn(**args)
        return {"tool": request.tool, "result": result}
    except TypeError as exc:
        raise HTTPException(status_code=400, detail=f"Bad arguments for {request.tool}: {exc}")
    except Exception as exc:
        logger.exception("Tool call failed: %s", request.tool)
        raise HTTPException(status_code=500, detail=str(exc))


# Convenience direct routes (nice for curl / quick testing / API docs at /docs)
@app.get("/mcp/search_arxiv")
def http_search_arxiv(query: str, max_results: int = 5) -> dict:
    return TOOL_REGISTRY["search_arxiv"](query=query, max_results=max_results)


@app.get("/mcp/search_semantic_scholar")
def http_search_semantic_scholar(query: str, limit: int = 5) -> dict:
    return TOOL_REGISTRY["search_semantic_scholar"](query=query, limit=limit)


@app.get("/mcp/verify_research_claim")
def http_verify_research_claim(claim: str) -> dict:
    return TOOL_REGISTRY["verify_research_claim"](claim=claim)


@app.get("/mcp/retrieve_citation_graph")
def http_retrieve_citation_graph(paper: str) -> dict:
    return TOOL_REGISTRY["retrieve_citation_graph"](paper_title_or_id=paper)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.mcp_host, port=settings.mcp_port)
