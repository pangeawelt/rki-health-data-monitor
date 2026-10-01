"""Streamlit client entry point: navigation around the dashboard pages.

The pages communicate only with the local FastAPI backend.
"""
import sys
from pathlib import Path

# `streamlit run dashboard/app.py` only puts dashboard/ on sys.path, so add the project root.
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st  # noqa: E402

from dashboard.footer import render_footer  # noqa: E402
from dashboard.styles import apply_compact_layout  # noqa: E402
from dashboard.views import about, glossary, overview, source  # noqa: E402

st.set_page_config(page_title="RKI Health Data Monitor", page_icon="📊", layout="wide")
apply_compact_layout()

source_page = st.Page(source.render, title="RKI-Quelle", icon="📦", url_path="quelle")


def render_about() -> None:
    about.render(source_page)  # the project page links to the offline copy of the data source


navigation = st.navigation(
    {
        "Dashboard": [
            st.Page(overview.render, title="Übersicht", icon="📊", url_path="uebersicht", default=True),
        ],
        "Wissen": [
            st.Page(glossary.render, title="Glossar", icon="📖", url_path="glossar"),
            source_page,
            st.Page(render_about, title="Projekt", icon="ℹ️", url_path="projekt"),
        ],
    }
)
navigation.run()
render_footer()
