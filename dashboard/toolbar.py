"""Chart toolbar: one-line headline, symbols that open the details on click, and PDF/Excel download.

The details (Einordnung, data notes) stay out of the way until the symbol is clicked. The files are generated
by the local API.
"""
import requests
import streamlit as st

from dashboard.api_client import api_get_file
from src.services.export.emphasis import emphasize

FORMATS = (
    ("pdf", "📄 PDF", "application/pdf"),
    ("xlsx", "📊 Excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
)
COLUMN_WIDTHS = {True: [5.5, 1.5, 1.5, 1.1, 1.1], False: [7, 1.5, 1.1, 1.1]}  # keyed by "has notes"


@st.cache_data(ttl=30, show_spinner=False)
def _load_file(path: str, params: dict) -> tuple[bytes, str]:
    return api_get_file(path, params)


def render_toolbar(
    key: str,
    path: str,
    params: dict,
    headline: str,
    insight: str,
    basis: str = "",
    notes: list[str] | None = None,
) -> None:
    """Headline on the left; ℹ️ Einordnung, ⚠️ Hinweise (only if there are notes), PDF and Excel on the right."""
    notes = notes or []
    head, info, *rest = st.columns(COLUMN_WIDTHS[bool(notes)])
    head.markdown(f"**{headline}**")

    with info.popover("ℹ️ Einordnung", use_container_width=True):
        st.markdown(emphasize(insight))
        if basis:
            st.caption(basis)

    if notes:
        warning, *rest = rest
        with warning.popover(f"⚠️ Hinweise ({len(notes)})", use_container_width=True):
            st.markdown("**Hinweise zur Datenverfügbarkeit**")
            for note in notes:
                st.markdown(f"- {emphasize(note)}")

    for column, (file_format, label, mime) in zip(rest, FORMATS):
        try:
            data, file_name = _load_file(path, {**params, "format": file_format})
        except requests.RequestException as exc:
            column.button(label, key=f"{key}_{file_format}", disabled=True, use_container_width=True,
                          help=f"Export derzeit nicht möglich: {exc}")
            continue
        column.download_button(
            label, data, file_name=file_name, mime=mime, key=f"{key}_{file_format}",
            use_container_width=True, help=f"Diagramm als {label.split()[-1]}-Datei herunterladen",
        )
