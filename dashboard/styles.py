"""Compact page layout so the main dashboard fits on one screen without scrolling."""
import html

import streamlit as st

# Vertical space taken by everything except the chart on the overview page (padding, title, tab bar, toolbar,
# KPI cards, status text, note and footer). Each chart fills the rest of the viewport. The year tab needs more
# room because it shows two groups of cards (its summary table sits below the chart).
TREND_FIXED_HEIGHT_PX = 558
YEAR_FIXED_HEIGHT_PX = 665
# On narrower windows the note and status text wrap onto more lines, so reserve more space.
NARROW_WIDTH_PX = 1250
NARROW_EXTRA_HEIGHT_PX = 65
# Below this height the page scrolls instead of squeezing the chart further.
CHART_MIN_HEIGHT_PX = 300

_COMPACT_CSS = f"""
<style>
/* Streamlit's default page padding (6rem top, 10rem bottom) wastes most of a laptop screen.
   The top padding must stay above the 3.75rem fixed header, otherwise the title is cut off. */
[data-testid="stMainBlockContainer"], .block-container {{
    padding-top: 4rem;
    padding-bottom: 0.5rem;
}}
[data-testid="stMain"] [data-testid="stVerticalBlock"] {{
    gap: 0.5rem;
}}
[data-testid="stMain"] h1 {{
    font-size: 2rem;
    padding: 0;
    line-height: 1.25;
}}
[data-testid="stMetricValue"] {{
    font-size: 1.7rem;
}}
/* Gradient banner at the top of the content pages (glossary, project, source). */
.page-hero {{
    background: linear-gradient(120deg, #4f46e5 0%, #0ea5e9 55%, #14b8a6 100%);
    color: #fff;
    border-radius: 16px;
    padding: 1rem 1.5rem;
    margin-bottom: 0.4rem;
    box-shadow: 0 6px 18px rgba(79, 70, 229, 0.25);
}}
.page-hero-title {{ font-size: 1.9rem; font-weight: 800; line-height: 1.25; letter-spacing: -0.01em; }}
.page-hero-sub {{ opacity: 0.92; font-size: 0.98rem; margin-top: 0.1rem; }}
/* KPI cards: short title, large value, small line for period and unit. */
.kpi-group-title {{
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    opacity: 0.65;
    margin: 0.2rem 0 0.25rem;
}}
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.6rem;
    margin-bottom: 0.4rem;
}}
.kpi-card {{
    border: 1px solid rgba(128, 128, 128, 0.25);
    border-top: 3px solid rgba(128, 128, 128, 0.35);
    border-radius: 12px;
    padding: 0.5rem 0.8rem 0.55rem;
    background: rgba(128, 128, 128, 0.05);
}}
.kpi-title {{ font-size: 0.82rem; font-weight: 600; opacity: 0.85; }}
.kpi-value {{ font-size: 1.55rem; font-weight: 800; line-height: 1.2; }}
.kpi-sub {{ font-size: 0.7rem; opacity: 0.6; margin-top: 0.05rem; }}
.kpi-up {{ border-top-color: #dc2626; }}
.kpi-up .kpi-value {{ color: #dc2626; }}
.kpi-down {{ border-top-color: #16a34a; }}
.kpi-down .kpi-value {{ color: #16a34a; }}
.kpi-flat {{ border-top-color: #64748b; }}
.kpi-flat .kpi-value {{ color: #64748b; }}
/* Let each chart use the remaining viewport height instead of a fixed size. */
[data-testid="stPlotlyChart"] {{
    min-height: {CHART_MIN_HEIGHT_PX}px;
}}
.st-key-trend_chart [data-testid="stPlotlyChart"] {{
    height: calc(100vh - {TREND_FIXED_HEIGHT_PX}px);
}}
.st-key-year_chart [data-testid="stPlotlyChart"] {{
    height: calc(100vh - {YEAR_FIXED_HEIGHT_PX}px);
}}
@media (max-width: {NARROW_WIDTH_PX}px) {{
    .st-key-trend_chart [data-testid="stPlotlyChart"] {{
        height: calc(100vh - {TREND_FIXED_HEIGHT_PX + NARROW_EXTRA_HEIGHT_PX}px);
    }}
    .st-key-year_chart [data-testid="stPlotlyChart"] {{
        height: calc(100vh - {YEAR_FIXED_HEIGHT_PX + NARROW_EXTRA_HEIGHT_PX}px);
    }}
}}
[data-testid="stPlotlyChart"] .js-plotly-plot,
[data-testid="stPlotlyChart"] .plot-container,
[data-testid="stPlotlyChart"] .svg-container {{
    height: 100% !important;
}}
/* The live search field of the glossary (st_keyup) is an iframe with a fixed 300px width. */
iframe[title="st_keyup.st_keyup"] {{
    width: 100%;
}}
/* The <style> block itself must not add an empty row to the flex layout. */
[data-testid="stElementContainer"]:has(style), .element-container:has(style) {{
    display: none;
}}
</style>
"""


def hero_html(title: str, subtitle: str) -> str:
    """Banner HTML for ``st.markdown(..., unsafe_allow_html=True)``."""
    return (
        f'<div class="page-hero"><div class="page-hero-title">{html.escape(title)}</div>'
        f'<div class="page-hero-sub">{html.escape(subtitle)}</div></div>'
    )


def apply_compact_layout() -> None:
    st.markdown(_COMPACT_CSS, unsafe_allow_html=True)
