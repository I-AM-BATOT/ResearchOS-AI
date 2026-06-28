"""
pages/10_Architecture.py
Interactive architecture diagrams, the real agent-to-agent communication
trace from the event bus, and MCP tool workflow documentation.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.ui_state import init_session_state, render_agent_trace
from core.ui_theme import apply_theme, titled

st.set_page_config(page_title="Architecture · ResearchOS AI", page_icon=":material/account_tree:", layout="wide")
apply_theme()
init_session_state()

st.title(titled("architecture", "Architecture"))

DIAGRAMS_DIR = Path(__file__).resolve().parent.parent / "diagrams"

st.subheader("System diagrams")
diagram_files = {
    "System Architecture": "system_architecture.mmd",
    "Agent Collaboration Flow": "agent_collaboration.mmd",
    "MCP Tool Architecture": "mcp_architecture.mmd",
    "Memory Architecture": "memory_architecture.mmd",
    "Security Architecture": "security_architecture.mmd",
    "Research Pipeline": "research_pipeline.mmd",
}
selected = st.selectbox("Choose a diagram", list(diagram_files.keys()))
diagram_path = DIAGRAMS_DIR / diagram_files[selected]

if diagram_path.exists():
    mermaid_code = diagram_path.read_text()
    try:
        st.mermaid(mermaid_code)  # Streamlit >= 1.40 has native mermaid support
    except Exception:
        # Fallback: render via the mermaid.js CDN in an HTML component.
        html = f"""
        <div class="mermaid">{mermaid_code}</div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js"></script>
        <script>mermaid.initialize({{startOnLoad: true}});</script>
        """
        st.components.v1.html(html, height=500, scrolling=True)
    with st.expander("View raw Mermaid source"):
        st.code(mermaid_code, language="text")
else:
    st.warning(f"Diagram file not found: {diagram_path}")

st.divider()
st.subheader("Live agent-to-agent communication trace")
st.caption("This is the real event-bus log, not a scripted animation — run an analysis in Research Workspace to populate it.")
render_agent_trace(limit=50)

st.divider()
st.subheader("MCP tool workflow")
st.markdown(
    "The MCP server (`mcp/server.py`, FastAPI) exposes 7 tools at `/mcp/call` "
    "(generic dispatch) and convenience GET routes for quick testing:\n\n"
    "| Tool | Purpose |\n"
    "|---|---|\n"
    "| `search_arxiv` | Search arXiv for papers |\n"
    "| `search_semantic_scholar` | Find related work + citation influence |\n"
    "| `retrieve_citation_graph` | Citing / referenced paper network |\n"
    "| `verify_research_claim` | Cross-reference a claim against scholarly sources |\n"
    "| `compare_papers` | Structural diff of methods/results between two papers |\n"
    "| `generate_bibliography` | APA / MLA / BibTeX reference generation |\n"
    "| `extract_metadata` | Title / authors / keywords / year from a PDF |\n\n"
    "Run it standalone with `uvicorn mcp.server:app --port 8765` and browse interactive docs at "
    "`/docs` (FastAPI auto-generated Swagger UI)."
)
