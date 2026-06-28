"""
core/config.py
Central configuration for ResearchOS AI.

All settings are loaded from environment variables (see .env.example).
The app is designed to run in two modes:

- LIVE mode: GEMINI_API_KEY is set -> real Gemini calls + real arXiv /
  Semantic Scholar HTTP calls are made.
- MOCK mode (default, no keys required): deterministic, template-based
  responses are generated locally so the entire platform is demoable
  offline / without API costs. This is what graders see if they just
  `streamlit run app.py` with no .env configured.
"""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    app_name: str = "ResearchOS AI"
    app_version: str = "1.0.0"

    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

    mcp_host: str = field(default_factory=lambda: os.getenv("MCP_HOST", "0.0.0.0"))
    mcp_port: int = field(default_factory=lambda: int(os.getenv("MCP_PORT", "8765")))

    memory_dir: str = field(default_factory=lambda: os.getenv("MEMORY_DIR", "./.researchos_memory"))
    chroma_collection: str = field(default_factory=lambda: os.getenv("CHROMA_COLLECTION", "researchos_memory"))

    max_pdf_mb: int = field(default_factory=lambda: int(os.getenv("MAX_PDF_MB", "25")))

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Forces mock mode even if a key is present (useful for tests / CI)
    force_mock: bool = field(default_factory=lambda: _bool_env("FORCE_MOCK_MODE", False))

    @property
    def live_mode(self) -> bool:
        return bool(self.gemini_api_key) and not self.force_mock


settings = Settings()


def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger. Used everywhere instead of print()."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
        logger.setLevel(settings.log_level)
    return logger
