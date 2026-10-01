"""Main dashboard page: KPIs, trend chart, year comparison and ETL status. Data comes only from the local API."""
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

from dashboard.api_client import api_get, api_is_available, api_post
from dashboard.cards import render_kpi_groups
from dashboard.toolbar import render_toolbar
from src.core.constants import DEFAULT_COMPARISON_YEARS, MAX_COMPARISON_YEARS, SOURCE_TYPE_LABELS
from src.core.periods import DEFAULT_PERIOD, PERIODS, PERIODS_BY_KEY
from src.services.export.emphasis import emphasize
from src.services.export.figure import build_figure
from src.services.export.model import ChartExport, trend_export, year_export


@st.cache_data(ttl=30)
def load_status():
    return api_get("/api/status")


@st.cache_data(ttl=30)
def load_regions():
    return api_get("/api/regions")


@st.cache_data(ttl=30)
def load_age_groups(region: str):
    return api_get("/api/age-groups", {"region": region})


@st.cache_data(ttl=30)
def load_incidence(region: str, age_group: str, period: str):
    return api_get("/api/incidence", {"region": region, "age_group": age_group, "period": period})


@st.cache_data(ttl=30)
def load_years(region: str, age_group: str):
    return api_get("/api/years", {"region": region, "age_group": age_group})


@st.cache_data(ttl=30)
def load_coverage(region: str, age_group: str):
    return api_get("/api/coverage", {"region": region, "age_group": age_group})


@st.cache_data(ttl=30)
def load_comparison(region: str, age_group: str, period: str, years: tuple[int, ...]):
    return api_get(
        "/api/incidence/compare",
        {"region": region, "age_group": age_group, "period": period, "years": list(years)},
    )


def _error_detail(exc: requests.RequestException) -> str:
    response = getattr(exc, "response", None)
    return response.text if response is not None else str(exc)


def _run_import() -> None:
    with st.spinner("RKI-Daten werden heruntergeladen, validiert und in SQLite aktualisiert …"):
        try:
            result = api_post("/api/refresh")
        except requests.RequestException as exc:
            st.error(f"RKI-Aktualisierung fehlgeschlagen: {_error_detail(exc)}")
            st.info("Die bereits gespeicherten Daten bleiben unverändert nutzbar.")
            return
    if result["status"] == "NO_CHANGE":
        st.success("RKI-Quelle geprüft: keine Änderungen seit dem letzten Import.")
    else:
        st.success(f"Import erfolgreich: {result['rows_inserted']} neu, {result['rows_updated']} aktualisiert.")
    st.cache_data.clear()


def _render_data_sidebar() -> None:
    with st.sidebar:
        st.header("Daten")
        if st.button(
            "🔄 Aktuelle RKI-Daten laden",
            type="primary",
            use_container_width=True,
            help="Lädt die aktuelle Datei direkt vom RKI (Internetverbindung erforderlich).",
        ):
            _run_import()


def _render_trend(chart: ChartExport, region: str, age_group: str, period: str) -> None:
    if not chart.categories:
        st.info("Für diese Filterkombination sind keine Daten vorhanden.")
        return
    render_toolbar(
        "trend",
        "/api/incidence/export",
        {"region": region, "age_group": age_group, "period": period},
        chart.headline,
        chart.insight,
    )
    render_kpi_groups(chart.kpi_groups)
    st.plotly_chart(build_figure(chart), use_container_width=True, key="trend_chart")


def _render_year_comparison(region: str, age_group: str, period: str, years: list[int], status: dict) -> None:
    if len(years) < 2:
        st.info("Für den Jahresvergleich werden mindestens zwei Jahre benötigt (Auswahl in der Seitenleiste).")
        return
    try:
        comparison = load_comparison(region, age_group, period, tuple(years))
    except requests.RequestException as exc:
        st.error(f"Jahresvergleich konnte nicht geladen werden: {_error_detail(exc)}")
        return

    chart = year_export(comparison, status, datetime.now())
    if comparison["mode"] == "annual":
        basis = f"Ganze Jahre im Vergleich · Kennzahlen: gleiche Wochen bis {comparison['window_end']}"
    else:
        basis = f"Gleiche Kalenderwochen in jedem Jahr · {comparison['basis_label']}"
    render_toolbar(
        "years",
        "/api/incidence/compare/export",
        {"region": region, "age_group": age_group, "period": period, "years": comparison["years"]},
        chart.headline,
        chart.insight,
        basis=basis,
        notes=chart.notes,
    )
    render_kpi_groups(chart.kpi_groups)
    st.plotly_chart(build_figure(chart), use_container_width=True, key="year_chart")

    st.caption("Kennzahlen je Jahr (im dargestellten Zeitraum)")
    st.dataframe(
        pd.DataFrame(chart.summary_rows, columns=chart.summary_header),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Ø Inzidenz": st.column_config.NumberColumn(format="%.1f"),
            "Spitzenwert": st.column_config.NumberColumn(format="%.0f"),
        },
    )


def render() -> None:
    st.title("RKI Health Data Monitor")
    st.caption("RKI Open Data → ETL → SQLite → FastAPI → Streamlit")

    if not api_is_available():
        st.error("Die lokale FastAPI ist nicht erreichbar.")
        st.code("python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000")
        return

    _render_data_sidebar()
    status = load_status()
    regions = load_regions()

    if not regions:
        st.info(
            "Die lokale Datenbank ist noch leer. Klicke links auf „Aktuelle RKI-Daten laden“. "
            "Die Daten werden dann direkt aus der offiziellen RKI-Open-Data-Quelle geladen (Internet erforderlich)."
        )
        st.subheader("Datenstatus")
        st.metric("Datensätze", status.get("total_rows", 0))
        return

    with st.sidebar:
        st.header("Filter")
        region_labels = {item["display_name"]: item["code"] for item in regions}
        default_region = "Baden-Württemberg" if "Baden-Württemberg" in region_labels else list(region_labels)[0]
        selected_region_label = st.selectbox(
            "Bundesland",
            list(region_labels.keys()),
            index=list(region_labels.keys()).index(default_region),
        )
        selected_region = region_labels[selected_region_label]

        age_groups = load_age_groups(selected_region)
        age_labels = {item["display_name"]: item["code"] for item in age_groups}
        default_age = "Alle Altersgruppen" if "Alle Altersgruppen" in age_labels else list(age_labels)[0]
        selected_age_label = st.selectbox(
            "Altersgruppe",
            list(age_labels.keys()),
            index=list(age_labels.keys()).index(default_age),
        )
        selected_age = age_labels[selected_age_label]
        period_keys = [p.key for p in PERIODS]
        period = st.selectbox(
            "Zeitraum",
            period_keys,
            index=period_keys.index(DEFAULT_PERIOD),
            format_func=lambda key: PERIODS_BY_KEY[key].label,
            help="Gilt für den Zeitlichen Verlauf und den Jahresvergleich. „Dieses Jahr“ läuft von der ersten "
            "Kalenderwoche des Jahres bis zur neuesten Woche.",
        )
        available_years = load_years(selected_region, selected_age)
        selected_years = st.multiselect(
            "Jahre (Jahresvergleich)",
            available_years,
            default=available_years[:DEFAULT_COMPARISON_YEARS],
            max_selections=MAX_COMPARISON_YEARS,
            help="Das neueste gewählte Jahr gilt als aktuell. Bundesländer liegen erst ab 2022 vor.",
        )

        coverage = load_coverage(selected_region, selected_age)
        with st.popover("ℹ️ Datenverfügbarkeit", use_container_width=True):
            st.markdown(f"**{coverage['region_display_name']}**")
            st.markdown(emphasize(coverage["note"]))
            if coverage["first_week"]:
                st.caption(f"Daten: {coverage['first_week']} bis {coverage['last_week']} · {coverage['weeks_count']} Wochen")

    try:
        data = load_incidence(selected_region, selected_age, period)
    except requests.RequestException as exc:
        st.error(f"Daten konnten nicht geladen werden: {_error_detail(exc)}")
        return

    trend = trend_export(data, status, datetime.now())

    trend_tab, year_tab = st.tabs(["📈 Zeitlicher Verlauf", "📅 Jahresvergleich"])
    with trend_tab:
        _render_trend(trend, selected_region, selected_age, period)
    with year_tab:
        _render_year_comparison(selected_region, selected_age, period, selected_years, status)

    status = load_status()
    last_etl = status.get("last_etl") or {}
    source = SOURCE_TYPE_LABELS.get(last_etl.get("source_type"), last_etl.get("source_type") or "—")
    st.markdown(
        f"**Datenstatus:** {status.get('total_rows', 0):,} Datensätze · neueste KW "
        f"{status.get('latest_week') or '—'} · letzter ETL {last_etl.get('status') or '—'} · Quelle {source}"
    )
    st.markdown(
        ":gray[**Fachlicher Hinweis:** Die ARE-Konsultationsinzidenz beschreibt Arztkonsultationen wegen akuter "
        "respiratorischer Erkrankungen pro 100.000 Einwohner. Sie ist keine individuelle Krankheitsprognose und "
        "keine Grundlage für automatische medizinische Entscheidungen. Quelle: Robert Koch-Institut, "
        "ARE-Konsultationsinzidenz, öffentliche aggregierte Daten (CC BY 4.0).]"
    )
