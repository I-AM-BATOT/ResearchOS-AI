"""
core/ui_theme.py
Shared design system for the Streamlit frontend: a minimal icon set
(Material Symbols, used sparingly -- one icon per page/section/action, not
one per bullet point), a CSS theme with subtle motion (fade-in on page
load, hover lift on cards/buttons/metrics, animated progress bars), and a
small status-badge component used instead of colored emoji circles.

Every page calls `apply_theme()` once near the top (Streamlit multipage
apps execute each page as an independent script, so the CSS has to be
(re-)injected per page -- it's cheap and idempotent).
"""
from __future__ import annotations

import streamlit as st

# --------------------------------------------------------------------------- #
# Icon set -- Material Symbols via Streamlit's ":material/name:" shorthand.
# Kept to ONE icon per concept. Use sparingly: a page title, a tab, a button,
# a status message -- not every line of body text.
# --------------------------------------------------------------------------- #
ICONS: dict[str, str] = {
    "app": ":material/science:",
    "home": ":material/home:",
    "workspace": ":material/upload_file:",
    "analysis": ":material/article:",
    "related": ":material/link:",
    "literature": ":material/menu_book:",
    "fact_check": ":material/fact_check:",
    "learning": ":material/school:",
    "presentation": ":material/slideshow:",
    "memory": ":material/memory:",
    "security": ":material/security:",
    "architecture": ":material/account_tree:",
    "chat": ":material/chat:",
    "search": ":material/search:",
    "delete": ":material/delete:",
    "download": ":material/download:",
    "settings": ":material/tune:",
    "compare": ":material/compare_arrows:",
    "trend": ":material/trending_up:",
    "idea": ":material/lightbulb:",
    "flashcard": ":material/style:",
    "quiz": ":material/quiz:",
    "guide": ":material/description:",
    "slides": ":material/slideshow:",
    "notes": ":material/mic:",
    "poster": ":material/image:",
    "graph": ":material/share:",
    "send": ":material/send:",
    "refresh": ":material/refresh:",
    "check": ":material/check_circle:",
    "warn": ":material/warning:",
    "error": ":material/error:",
    "info": ":material/info:",
    "live": ":material/bolt:",
    "mock": ":material/cloud_off:",
}


def icon(key: str) -> str:
    """Returns the Material Symbol shortcode for a known icon key, or '' if unknown."""
    return ICONS.get(key, "")


def titled(key: str, text: str) -> str:
    """e.g. titled('workspace', 'Research Workspace') -> ':material/upload_file: Research Workspace'"""
    ic = icon(key)
    return f"{ic} {text}".strip()


# --------------------------------------------------------------------------- #
# Theme CSS
# --------------------------------------------------------------------------- #
_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    /* Pull from Streamlit's theme CSS variables when available, with safe
       fallbacks -- this is what makes these colors correct in BOTH light
       and dark mode rather than assuming a white background. */
    --rosai-primary: var(--st-primary-color, var(--primary-color, #4F46E5));
    --rosai-border:  var(--st-border-color, rgba(120, 120, 120, 0.28));

    /* Badge colors: a mid-saturation hue for text (readable on both very
       light and very dark backgrounds) + a low-opacity tint of the same
       hue for the background (opacity makes it adapt to whatever sits
       behind it, instead of a fixed pastel that only works on white). */
    --rosai-success-fg: #22C55E; --rosai-success-bg: rgba(34, 197, 94, 0.16);
    --rosai-warning-fg: #F59E0B; --rosai-warning-bg: rgba(245, 158, 11, 0.16);
    --rosai-error-fg:   #EF4444; --rosai-error-bg:   rgba(239, 68, 68, 0.16);
    --rosai-info-fg:    #3B82F6; --rosai-info-bg:    rgba(59, 130, 246, 0.16);
    --rosai-neutral-fg: var(--st-text-color, var(--text-color, inherit));
    --rosai-neutral-bg: rgba(120, 120, 120, 0.14);
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* Gentle fade-in + rise on every page render */
.main .block-container {
    animation: rosaiFadeIn 0.45s ease-out;
}
@keyframes rosaiFadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* Buttons: subtle lift + colored glow on hover */
.stButton > button, .stDownloadButton > button {
    border-radius: 8px;
    border: 1px solid var(--rosai-border);
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(79, 70, 229, 0.25);
    border-color: var(--rosai-primary);
}
.stButton > button:active, .stDownloadButton > button:active {
    transform: translateY(0px);
}

/* Bordered containers (cards) lift gently on hover */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    transition: box-shadow 0.25s ease, transform 0.25s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
}

/* Metrics styled as soft cards with a hover lift.
   Deliberately does NOT override background-color -- Streamlit's own
   metric container is already correctly themed for light/dark; we only
   add the border, radius, and motion on top of it. */
div[data-testid="stMetric"] {
    border: 1px solid var(--rosai-border);
    border-radius: 12px;
    padding: 14px 18px 10px 18px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.16);
}

/* Tabs: animated underline on the active tab */
.stTabs [data-baseweb="tab-list"] button {
    transition: color 0.15s ease;
}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    border-bottom: 2.5px solid var(--rosai-primary);
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: var(--rosai-primary) !important;
    transition: left 0.25s ease, width 0.25s ease;
}

/* Progress bars: smooth animated fill with a soft gradient */
div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #818CF8, var(--rosai-primary));
    transition: width 0.5s ease;
    border-radius: 6px;
}

/* Expanders: rounded, gentle hover */
details {
    border-radius: 10px !important;
    transition: box-shadow 0.2s ease;
}
details:hover {
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.14);
}

/* Chat messages: soft fade-in */
[data-testid="stChatMessage"] {
    animation: rosaiFadeIn 0.3s ease-out;
    border-radius: 14px !important;
}

/* Sidebar: subtle divider */
section[data-testid="stSidebar"] {
    border-right: 1px solid var(--rosai-border);
}

/* Status badges (pill-shaped, used instead of colored circle emoji) */
.rosai-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 12px; border-radius: 999px;
    font-size: 0.8rem; font-weight: 600;
    line-height: 1.6;
    transition: transform 0.15s ease;
}
.rosai-badge:hover { transform: translateY(-1px); }
.rosai-badge-success { background: var(--rosai-success-bg); color: var(--rosai-success-fg); }
.rosai-badge-warning { background: var(--rosai-warning-bg); color: var(--rosai-warning-fg); }
.rosai-badge-error   { background: var(--rosai-error-bg);   color: var(--rosai-error-fg); }
.rosai-badge-info    { background: var(--rosai-info-bg);    color: var(--rosai-info-fg); }
.rosai-badge-neutral { background: var(--rosai-neutral-bg); color: var(--rosai-neutral-fg); }

/* Material icon sizing/alignment fix inside badges */
.rosai-badge img, .rosai-badge svg {
    height: 0.95em; width: 0.95em; vertical-align: -0.12em;
}
</style>
"""


def apply_theme() -> None:
    """Injects the shared CSS theme. Call once near the top of every page."""
    st.markdown(_THEME_CSS, unsafe_allow_html=True)


_BADGE_KIND_TO_ICON = {
    "success": "check_circle",
    "warning": "warning",
    "error": "error",
    "info": "info",
    "neutral": "radio_button_unchecked",
}


def badge(text: str, kind: str = "neutral", *, show_icon: bool = True) -> str:
    """Returns Markdown (with an inline Material Symbol) for a small pill-shaped
    status badge, e.g. badge("Verified", "success"). Pass the result to
    st.markdown(..., unsafe_allow_html=True) -- Streamlit expands the
    ':material/name:' shortcode the same way it does everywhere else, so the
    icon matches the rest of the app exactly."""
    icon_part = f":material/{_BADGE_KIND_TO_ICON.get(kind, 'radio_button_unchecked')}: " if show_icon else ""
    return f'<span class="rosai-badge rosai-badge-{kind}">{icon_part}{text}</span>'
