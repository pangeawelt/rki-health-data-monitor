"""Footer shown below every dashboard page."""
import html

import streamlit as st

from src.core.config import settings

PROJECT_NAME = "RKI Health Data Monitor"


def render_footer() -> None:
    # The author is optional and comes from APP_AUTHOR in .env, so no personal name is part of the code.
    credit = f" · Erstellt von <strong>{html.escape(settings.app_author)}</strong>" if settings.app_author else ""
    st.markdown(
        f"<div style='text-align: center; opacity: 0.75; font-size: 0.9rem; "
        f"border-top: 1px solid rgba(128, 128, 128, 0.25); padding-top: 0.4rem;'>"
        f"{PROJECT_NAME}{credit}"
        f"</div>",
        unsafe_allow_html=True,
    )
