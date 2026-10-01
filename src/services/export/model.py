"""Chart-neutral export model.

Both dashboard charts reduce to categories (x axis, each with its month) plus named series, so the PDF
and Excel writers do not need to know which chart they render.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import NamedTuple

from src.core.constants import LICENSE_TEXT, SOURCE_NAME_RKI, SOURCE_TYPE_LABELS
from src.core.weeks import week_label, week_number
from src.services.export.formatting import format_de, format_percent, format_value  # noqa: F401 (re-exported)
from src.services.export.insight import (
    SAME_LEVEL_PERCENT,
    trend_headline,
    trend_insight,
    year_headline,
    year_insight,
)

TREND_SERIES_NAME = "ARE-Konsultationsinzidenz"
MOVING_AVERAGE_NAME = "4-Wochen-Mittel"
Y_AXIS_TITLE = "Konsultationen pro 100.000 Einwohner"
UNIT = "je 100.000 Einw."  # shown under every key figure that is an incidence


class Kpi(NamedTuple):
    """One key figure card: a short title, the value and a small line for period and unit."""

    title: str
    value: str
    sub: str = ""
    tone: str = ""  # "up" / "down" / "flat" for changes (an increase is the unfavourable direction)


class KpiGroup(NamedTuple):
    title: str
    items: list[Kpi]


@dataclass(frozen=True)
class ChartExport:
    title: str
    subtitle: str
    x_title: str
    y_title: str
    categories: list[str]
    months: list[str]  # upper-case month of every category, shown below the week label
    series: dict[str, list[float | None]]
    kpi_groups: list[KpiGroup]
    info: list[tuple[str, str]]
    source_note: str
    filename: str
    reference_series: tuple[str, ...] = ()  # drawn grey and dashed (e.g. the mean of the comparison years)
    headline: str = ""  # one line with the direction of the change, always visible
    insight: str = ""  # one or two sentences that put the numbers into context, opened on demand
    notes: list[str] = field(default_factory=list)  # data availability warnings
    summary_header: list[str] = field(default_factory=list)
    summary_rows: list[list[str | float | None]] = field(default_factory=list)


def _tone(percent: float | None) -> str:
    if percent is None:
        return ""
    if abs(percent) < SAME_LEVEL_PERCENT:
        return "flat"
    return "up" if percent > 0 else "down"


def _change(title: str, percent: float | None, sub: str) -> Kpi:
    return Kpi(title, format_percent(percent), sub, _tone(percent))


def _slug(*parts: str) -> str:
    joined = "_".join(parts).replace("+", "plus")
    return re.sub(r"[^A-Za-z0-9]+", "-", joined).strip("-")


def _source_texts(status: dict, generated_at: datetime) -> tuple[str, list[tuple[str, str]]]:
    """Source note for footers and the metadata rows shared by every export."""
    last_etl = status.get("last_etl") or {}
    source = SOURCE_TYPE_LABELS.get(last_etl.get("source_type"), last_etl.get("source_type") or "—")
    latest_week = status.get("latest_week") or "—"
    note = (
        f"Quelle: {SOURCE_NAME_RKI} ({LICENSE_TEXT}) · Datenquelle im Monitor: {source} · "
        f"Datenstand: {latest_week} · Erstellt am {generated_at:%d.%m.%Y %H:%M}"
    )
    info = [
        ("Datenquelle", SOURCE_NAME_RKI),
        ("Bezug im Monitor", source),
        ("Datenstand (neueste Kalenderwoche)", latest_week),
        ("Lizenz", LICENSE_TEXT),
        ("Erstellt am", f"{generated_at:%d.%m.%Y %H:%M}"),
    ]
    return note, info


def trend_export(incidence: dict, status: dict, generated_at: datetime) -> ChartExport:
    points = incidence["series"]
    weeks = [p["calendar_week"] for p in points]
    span = f"{incidence['from_week']} bis {incidence['to_week']}" if weeks else "—"
    region, age = incidence["region_display_name"], incidence["age_group_display_name"]
    latest = incidence["latest_week"] or "—"
    note, source_info = _source_texts(status, generated_at)
    return ChartExport(
        title="Zeitlicher Verlauf – ARE-Konsultationsinzidenz",
        subtitle=f"{region} · {age} · {incidence['period_label']} ({span})",
        x_title="Kalenderwoche",
        y_title=Y_AXIS_TITLE,
        categories=weeks,
        months=[p["month"] for p in points],
        series={
            TREND_SERIES_NAME: [p["value"] for p in points],
            MOVING_AVERAGE_NAME: [p["moving_average_4w"] for p in points],
        },
        kpi_groups=[
            KpiGroup(
                f"Aktuelle Woche · {latest}",
                [
                    Kpi("Aktuell", format_value(incidence["latest_value"]), f"{latest} · {UNIT}"),
                    Kpi("Vorwoche", format_value(incidence["previous_value"]), f"Woche davor · {UNIT}"),
                    _change("Veränderung", incidence["change_percent"], "zur Vorwoche"),
                ],
            )
        ],
        headline=trend_headline(incidence),
        insight=trend_insight(incidence),
        info=[
            ("Bundesland", region),
            ("Altersgruppe", age),
            ("Zeitraum", f"{incidence['period_label']} ({span})"),
            ("Einheit", "Konsultationen wegen ARE pro 100.000 Einwohner"),
            *source_info,
        ],
        source_note=note,
        filename=_slug("ARE-Verlauf", incidence["region"], incidence["age_group"], incidence["period"],
                       f"{generated_at:%Y%m%d}"),
    )


def year_export(comparison: dict, status: dict, generated_at: datetime) -> ChartExport:
    axis = comparison["axis"]
    positions = [tick["position"] for tick in axis]
    history_years = comparison["history_years_text"]
    history_name = f"Ø {history_years}"  # the reference line names the years it is made of
    series = {
        str(item["year"]): [
            next((p["value"] for p in item["points"] if p["position"] == position), None)
            for position in positions
        ]
        for item in comparison["series"]
    }
    series[history_name] = [point["value"] for point in comparison["history_mean"]]

    region, age = comparison["region_display_name"], comparison["age_group_display_name"]
    current, previous = comparison["current_year"], comparison["previous_year"]
    span = comparison["window_span"]
    average = "Ø " if comparison["window_weeks"] > 1 else ""
    latest = comparison["latest_week"]
    annual = comparison["mode"] == "annual"
    note, source_info = _source_texts(status, generated_at)
    window_sub = f"{average}{span} · {UNIT}"
    return ChartExport(
        title="Jahresvergleich – ARE-Konsultationsinzidenz",
        subtitle=f"{region} · {age} · {comparison['period_label']} · Jahre {', '.join(map(str, comparison['years']))}",
        x_title="Kalenderwoche",
        y_title=Y_AXIS_TITLE,
        categories=[tick["label"] for tick in axis],
        months=[tick["month"] for tick in axis],
        series=series,
        reference_series=(history_name,),
        kpi_groups=[
            KpiGroup(
                f"Aktuelle Woche · {latest}",
                [
                    Kpi("Diese Woche", format_value(comparison["latest_week_value"]), f"{latest} · {UNIT}"),
                    Kpi("Vorjahr", format_value(comparison["previous_year_week_value"]),
                        f"{comparison['previous_year_week'] or '—'} · {UNIT}"),
                    _change("Veränderung", comparison["week_change_vs_previous_year_percent"], "zum Vorjahr"),
                    Kpi("Ø Vergleichsjahre", format_value(comparison["same_week_history_average"]),
                        f"{history_years} · {week_label(week_number(latest))} · {UNIT}"),
                ],
            ),
            KpiGroup(
                f"Zeitraum · {average}{span}",
                [
                    Kpi(str(current), format_value(comparison["current_value"]), window_sub),
                    Kpi(str(previous), format_value(comparison["previous_year_value"]), window_sub),
                    _change("Veränderung", comparison["change_vs_previous_percent"], f"{current} zu {previous}"),
                    Kpi("Ø Vergleichsjahre", format_value(comparison["historical_average"]),
                        f"{history_years} · {UNIT}"),
                    _change("Abweichung", comparison["deviation_vs_history_percent"],
                            f"{current} vom Ø {history_years}"),
                ],
            ),
        ],
        headline=year_headline(comparison),
        insight=year_insight(comparison),
        notes=list(comparison["notes"]),
        info=[
            ("Bundesland", region),
            ("Altersgruppe", age),
            ("Zeitraum", comparison["period_label"]),
            ("Verglichene Jahre", ", ".join(map(str, comparison["years"]))),
            ("Referenzjahre (Ø)", f"{history_years}, jeweils gleiche Kalenderwochen"),
            ("Kennzahlen basieren auf", f"{comparison['basis_label']} – jeweils gleiche Kalenderwochen"),
            ("Diagramm zeigt",
             "ganze Kalenderjahre (KW01 bis KW53)" if annual
             else f"Kalenderwochen {comparison['window_start']} bis {comparison['window_end']}"),
            ("Einheit", "Konsultationen wegen ARE pro 100.000 Einwohner"),
            *source_info,
        ],
        source_note=note,
        summary_header=["Jahr", "Wochen", "Ø Inzidenz", "Spitzenwert", "Spitzenwoche"],
        summary_rows=[
            [str(s["year"]), s["weeks_count"], s["average"], s["peak"], s["peak_week"]]
            for s in comparison["summaries"]
        ],
        filename=_slug("ARE-Jahresvergleich", comparison["region"], comparison["age_group"],
                       comparison["period"], f"{generated_at:%Y%m%d}"),
    )
