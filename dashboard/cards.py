"""KPI cards: a short title, a large value and a small line for period and unit."""
import html

import streamlit as st

from src.services.export.model import Kpi, KpiGroup

TONE_ARROWS = {"up": "▲ ", "down": "▼ ", "flat": "● "}


def _card(kpi: Kpi) -> str:
    tone = f" kpi-{kpi.tone}" if kpi.tone else ""
    sub = f'<div class="kpi-sub">{html.escape(kpi.sub)}</div>' if kpi.sub else ""
    return (
        f'<div class="kpi-card{tone}"><div class="kpi-title">{html.escape(kpi.title)}</div>'
        f'<div class="kpi-value">{TONE_ARROWS.get(kpi.tone, "")}{html.escape(kpi.value)}</div>{sub}</div>'
    )


def render_kpi_groups(groups: list[KpiGroup]) -> None:
    """One labelled row of cards per group (styles in ``styles.py``)."""
    for group in groups:
        cards = "".join(_card(kpi) for kpi in group.items)
        # No blank lines or indentation: Markdown would otherwise end the HTML block early.
        st.markdown(
            f'<div class="kpi-group-title">{html.escape(group.title)}</div><div class="kpi-grid">{cards}</div>',
            unsafe_allow_html=True,
        )
