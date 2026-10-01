"""Plotly figure of a chart. The dashboard and the PDF report share this one definition."""
import math
import threading

import plotly.graph_objects as go
from plotly.colors import qualitative

from src.core.weeks import short_month
from src.services.export.model import ChartExport

MAX_TICKS = 13
MAX_FULL_MONTH_TICKS = 8  # beyond this the full month names would overlap, so they are abbreviated
MARKER_LIMIT = 30  # markers clutter long series
REFERENCE_COLOR = "#8b95a1"
PNG_WIDTH, PNG_HEIGHT, PNG_SCALE = 1000, 440, 2

# Kaleido drives one browser process and is not safe to call from several threads at once.
_PNG_LOCK = threading.Lock()


def _colors(chart: ChartExport) -> list[str]:
    palette = iter(qualitative.Plotly)
    return [REFERENCE_COLOR if name in chart.reference_series else next(palette) for name in chart.series]


def _tick_labels(chart: ChartExport) -> tuple[list[str], list[str]]:
    """Every n-th week with its month in capitals below, e.g. ``KW29<br>JULI``."""
    step = max(1, math.ceil(len(chart.categories) / MAX_TICKS))
    values = chart.categories[::step]
    months = chart.months[::step]
    abbreviate = len(values) > MAX_FULL_MONTH_TICKS
    return values, [f"{value}<br>{short_month(month) if abbreviate else month}" for value, month in zip(values, months)]


def build_figure(chart: ChartExport, *, light: bool = False, title: bool = True) -> go.Figure:
    colors = _colors(chart)
    fig = go.Figure()

    for index, (name, values) in enumerate(chart.series.items()):
        reference = name in chart.reference_series
        fig.add_trace(
            go.Scatter(
                x=chart.categories,
                y=values,
                name=name,
                mode="lines+markers" if len(chart.categories) <= MARKER_LIMIT and not reference else "lines",
                line={"color": colors[index], "width": 2.5 if index == 0 else 1.8,
                      "dash": "dash" if reference else "solid"},
                customdata=chart.months,
                hovertemplate="%{x} · %{customdata}: %{y:,.0f}<extra>" + name + "</extra>",
            )
        )
    tick_values, tick_text = _tick_labels(chart)
    fig.update_xaxes(
        title_text=chart.x_title, type="category", categoryorder="array", categoryarray=chart.categories,
        tickmode="array", tickvals=tick_values, ticktext=tick_text, tickangle=0,
    )

    fig.update_layout(
        title={"text": chart.title.split(" – ")[0], "font": {"size": 16}} if title else None,
        yaxis_title=chart.y_title,
        autosize=True,
        margin={"l": 10, "r": 10, "t": 40 if title else 20, "b": 10},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.0, "xanchor": "right", "x": 1.0},
        legend_title=None,
        template="plotly_white" if light else None,
    )
    fig.update_yaxes(rangemode="tozero", automargin=True)
    fig.update_xaxes(automargin=True)
    return fig


def figure_png(chart: ChartExport) -> bytes:
    """Static image of the chart for the PDF report (rendered by Plotly's Kaleido engine)."""
    figure = build_figure(chart, light=True, title=False)
    with _PNG_LOCK:
        return figure.to_image(format="png", width=PNG_WIDTH, height=PNG_HEIGHT, scale=PNG_SCALE)
