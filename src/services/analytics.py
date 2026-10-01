"""Read-side analytics service. The SQL stays explicit (window functions) so the queries are easy to read."""
from sqlalchemy import text

from src.core.constants import (
    AGE_GROUP_DISPLAY_NAMES,
    DEFAULT_COMPARISON_YEARS,
    MAX_COMPARISON_YEARS,
    REGION_DISPLAY_NAMES,
)
from src.core.periods import DEFAULT_PERIOD, PERIODS_BY_KEY, get_period, resolve_weeks
from src.core.weeks import month_name, shift_week, week_label, week_number, week_year
from src.db.connection import SessionLocal


REGIONS_SQL = text("""
SELECT DISTINCT r.region_name
FROM fact_are_incidence f
JOIN dim_region r ON r.region_id = f.region_id
ORDER BY CASE WHEN r.region_name = 'Bundesweit' THEN 0 ELSE 1 END, r.region_name
""")

AGE_GROUPS_SQL = text("""
SELECT DISTINCT a.age_group_code, a.display_name, a.sort_order
FROM fact_are_incidence f
JOIN dim_region r ON r.region_id = f.region_id
JOIN dim_age_group a ON a.age_group_id = f.age_group_id
WHERE r.region_name = :region
ORDER BY a.sort_order
""")

SERIES_SQL = text("""
WITH latest AS (
    SELECT
        f.calendar_week,
        f.incidence_value
    FROM fact_are_incidence f
    JOIN dim_region r ON r.region_id = f.region_id
    JOIN dim_age_group a ON a.age_group_id = f.age_group_id
    WHERE r.region_name = :region
      AND a.age_group_code = :age_group
    ORDER BY f.calendar_week DESC
    LIMIT :weeks
), ordered AS (
    SELECT calendar_week, incidence_value
    FROM latest
    ORDER BY calendar_week
)
SELECT
    calendar_week,
    incidence_value,
    LAG(incidence_value) OVER (ORDER BY calendar_week) AS previous_value,
    AVG(incidence_value) OVER (
        ORDER BY calendar_week
        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ) AS moving_average_4w
FROM ordered
ORDER BY calendar_week
""")

WEEKS_SQL = text("""
SELECT f.calendar_week, f.incidence_value
FROM fact_are_incidence f
JOIN dim_region r ON r.region_id = f.region_id
JOIN dim_age_group a ON a.age_group_id = f.age_group_id
WHERE r.region_name = :region AND a.age_group_code = :age_group
ORDER BY f.calendar_week
""")

STATUS_SQL = text("""
SELECT
    (SELECT COUNT(*) FROM fact_are_incidence) AS total_rows,
    (SELECT MAX(calendar_week) FROM fact_are_incidence) AS latest_week,
    e.etl_run_id,
    e.status,
    e.source_type,
    e.started_at,
    e.finished_at,
    e.rows_downloaded,
    e.rows_valid,
    e.rows_rejected,
    e.rows_inserted,
    e.rows_updated,
    e.error_message
FROM etl_run e
ORDER BY e.etl_run_id DESC
LIMIT 1
""")

# Rows before the first shown week that the 4-week moving average and the "previous week" need.
MOVING_AVERAGE_WARMUP = 3
YEAR_TO_DATE = PERIODS_BY_KEY["year"]
NATIONAL_REGION = "Bundesweit"


def get_regions() -> list[dict]:
    with SessionLocal() as session:
        rows = session.execute(REGIONS_SQL).mappings().all()
    return [
        {
            "code": row["region_name"],
            "display_name": REGION_DISPLAY_NAMES.get(row["region_name"], row["region_name"]),
        }
        for row in rows
    ]


def get_age_groups(region: str) -> list[dict]:
    with SessionLocal() as session:
        rows = session.execute(AGE_GROUPS_SQL, {"region": region}).mappings().all()
    return [
        {
            "code": row["age_group_code"],
            "display_name": row["display_name"],
        }
        for row in rows
    ]


def _load_weeks(region: str, age_group: str) -> list[tuple[str, float | None]]:
    """All (calendar week, incidence) pairs of the filter combination, oldest first."""
    with SessionLocal() as session:
        rows = session.execute(WEEKS_SQL, {"region": region, "age_group": age_group}).all()
    return [(row[0], row[1]) for row in rows]


def _percent_change(current: float | None, reference: float | None) -> float | None:
    if current is None or reference in (None, 0):
        return None
    return round((current - reference) / reference * 100, 1)


def get_incidence(region: str, age_group: str, period: str = DEFAULT_PERIOD) -> dict:
    spec = get_period(period)
    covered = resolve_weeks(spec, [week for week, _ in _load_weeks(region, age_group)])
    count = len(covered)

    rows = []
    if count:
        with SessionLocal() as session:
            rows = session.execute(
                SERIES_SQL,
                {"region": region, "age_group": age_group, "weeks": count + MOVING_AVERAGE_WARMUP},
            ).mappings().all()

    points = [
        {
            "calendar_week": row["calendar_week"],
            "month": month_name(row["calendar_week"]),
            "value": row["incidence_value"],
            "previous_value": row["previous_value"],
            "moving_average_4w": row["moving_average_4w"],
        }
        for row in rows
    ]
    shown = points[-count:] if count else []

    latest = points[-1] if points else None
    previous = points[-2] if len(points) >= 2 else None
    current_value = latest["value"] if latest else None
    previous_value = previous["value"] if previous else None

    return {
        "region": region,
        "region_display_name": REGION_DISPLAY_NAMES.get(region, region),
        "age_group": age_group,
        "age_group_display_name": AGE_GROUP_DISPLAY_NAMES.get(age_group, age_group),
        "period": spec.key,
        "period_label": spec.label,
        "weeks": count,
        "from_week": shown[0]["calendar_week"] if shown else None,
        "to_week": shown[-1]["calendar_week"] if shown else None,
        "latest_week": latest["calendar_week"] if latest else None,
        "latest_value": current_value,
        "previous_value": previous_value,
        "change_percent": _percent_change(current_value, previous_value),
        "series": shown,
    }


def get_years(region: str, age_group: str) -> list[int]:
    """Calendar years with data for the filter combination, newest first."""
    return sorted({week_year(week) for week, _ in _load_weeks(region, age_group)}, reverse=True)


def _window_average(values: dict[str, float | None], window: list[str], years_back: int) -> float | None:
    """Mean of the window shifted back by whole years; None if any of its weeks has no value."""
    shifted = [week for week in (shift_week(w, years_back) for w in window) if week is not None]
    found = [values.get(week) for week in shifted]
    if not found or any(value is None for value in found):
        return None
    return sum(found) / len(found)


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 1)


def _window_span(window: list[str]) -> str:
    """``KW36–KW39``, ``KW39`` or ``KW52–KW02 (Jahreswechsel)``."""
    first, last = window[0], window[-1]
    if len(window) == 1:
        return week_label(week_number(last))
    span = f"{week_label(week_number(first))}–{week_label(week_number(last))}"
    return span if week_year(first) == week_year(last) else f"{span} (Jahreswechsel)"


def _years_text(years: list[int]) -> str:
    """``2022–2025`` for consecutive years, otherwise ``2022, 2024, 2025``."""
    ordered = sorted(years)
    if not ordered:
        return "—"
    if len(ordered) > 2 and ordered == list(range(ordered[0], ordered[-1] + 1)):
        return f"{ordered[0]}–{ordered[-1]}"
    return ", ".join(map(str, ordered))


def _season_of(calendar_week: str) -> str:
    """RKI season (week 40 to week 39) a calendar week belongs to, e.g. ``2022/23``."""
    start = week_year(calendar_week) if week_number(calendar_week) >= 40 else week_year(calendar_week) - 1
    return f"{start}/{(start + 1) % 100:02d}"


def get_coverage(region: str, age_group: str) -> dict:
    """First and last week of the RKI data for a region, with a human readable availability note."""
    weeks = [week for week, _ in _load_weeks(region, age_group)]
    national = [week for week, _ in _load_weeks(NATIONAL_REGION, age_group)]
    display = REGION_DISPLAY_NAMES.get(region, region)
    if not weeks:
        return {"region": region, "region_display_name": display, "first_week": None, "last_week": None,
                "weeks_count": 0, "is_national": region == NATIONAL_REGION, "national_first_week": None,
                "first_full_year": None, "note": f"Für {display} liegen keine Daten vor."}

    first, last = weeks[0], weeks[-1]
    first_full_year = week_year(first) if week_number(first) <= 1 else week_year(first) + 1
    is_national = region == NATIONAL_REGION
    national_first = national[0] if national else None
    if is_national:
        note = (
            f"Deutschland gesamt: Das RKI veröffentlicht Daten ab {first} (Saison {_season_of(first)}). "
            f"Vollständige Kalenderjahre liegen ab {first_full_year} vor."
        )
    else:
        note = (
            f"{display}: Das RKI veröffentlicht Bundesland-Daten erst ab {first} (Saison {_season_of(first)}). "
            f"Frühere Jahre gibt es für Bundesländer nicht – {week_year(first)} ist daher unvollständig und "
            f"vollständige Kalenderjahre liegen ab {first_full_year} vor. Vergleiche mit früheren Jahren sind nur "
            f"für Deutschland gesamt möglich (ab {national_first})."
        )
    return {"region": region, "region_display_name": display, "first_week": first, "last_week": last,
            "weeks_count": len(weeks), "is_national": is_national, "national_first_week": national_first,
            "first_full_year": first_full_year, "note": note}


def get_year_comparison(
    region: str,
    age_group: str,
    years: list[int] | None = None,
    period: str = DEFAULT_PERIOD,
) -> dict:
    """Compare calendar years on the same calendar weeks.

    Periods up to "this year" compare the same calendar weeks of every selected year (for example
    2026-W36..W39 with 2025-W36..W39). Multi-year periods draw each selected year completely (KW01..KW53);
    the key figures then compare the same weeks up to the latest week (year to date) of every year.
    The newest selected year is "current", the second newest the previous year.
    """
    spec = get_period(period)
    data = _load_weeks(region, age_group)
    values = dict(data)
    all_weeks = list(values)

    available = sorted({week_year(week) for week in all_weeks}, reverse=True)
    requested = available[:DEFAULT_COMPARISON_YEARS] if not years else years
    selected = [year for year in available if year in set(requested)][:MAX_COMPARISON_YEARS]
    if spec.is_multi_year:
        selected = selected[: spec.amount]
    if len(selected) < 2:
        raise ValueError("At least two years with data are required for a comparison")

    current_year, previous_year = selected[0], selected[1]
    latest_week = max(week for week in all_weeks if week_year(week) == current_year)
    window = resolve_weeks(YEAR_TO_DATE if spec.is_multi_year else spec, all_weeks, latest_week)

    series = []
    for year in selected:
        if spec.is_multi_year:
            weeks = [(week, week_number(week)) for week in all_weeks if week_year(week) == year]
        else:
            weeks = [
                (shifted, position)
                for position, week in enumerate(window, start=1)
                if (shifted := shift_week(week, current_year - year)) is not None
            ]
        series.append(
            {
                "year": year,
                "points": [
                    {
                        "calendar_week": week,
                        "month": month_name(week),
                        "position": position,
                        "value": values.get(week),
                    }
                    for week, position in weeks
                ],
            }
        )

    # Axis: one tick per week position; the first series (current year) provides the month.
    ticks: dict[int, dict] = {}
    for item in series:
        for point in item["points"]:
            ticks.setdefault(
                point["position"],
                {"position": point["position"], "label": week_label(week_number(point["calendar_week"])),
                 "month": point["month"]},
            )
    axis = [ticks[position] for position in sorted(ticks)]

    history_mean = []
    for tick in axis:
        history = [
            point["value"]
            for item in series[1:]
            for point in item["points"]
            if point["position"] == tick["position"] and point["value"] is not None
        ]
        history_mean.append({**tick, "value": _round(sum(history) / len(history)) if history else None})

    summaries = []
    for item in series:
        known = [(p["value"], p["calendar_week"]) for p in item["points"] if p["value"] is not None]
        peak = max(known, default=None)
        summaries.append(
            {
                "year": item["year"],
                "weeks_count": len(known),
                "average": _round(sum(v for v, _ in known) / len(known)) if known else None,
                "peak": peak[0] if peak else None,
                "peak_week": peak[1] if peak else None,
            }
        )

    # Key figures over the window (average of its weeks) ...
    metric = {year: _window_average(values, window, current_year - year) for year in selected}
    current_value, previous_value = metric[current_year], metric[previous_year]
    history_years = [year for year in selected[1:] if metric[year] is not None]
    history_values = [metric[year] for year in history_years]
    historical_average = sum(history_values) / len(history_values) if history_values else None

    # ... and for the single latest week against the same week of the other years.
    previous_week = all_weeks[all_weeks.index(latest_week) - 1] if all_weeks.index(latest_week) > 0 else None
    week_value = values.get(latest_week)
    previous_year_week = shift_week(latest_week, current_year - previous_year)
    previous_year_week_value = values.get(previous_year_week) if previous_year_week else None
    same_week_history = [
        values.get(shifted)
        for year in selected[1:]
        if (shifted := shift_week(latest_week, current_year - year)) is not None and values.get(shifted) is not None
    ]
    same_week_average = sum(same_week_history) / len(same_week_history) if same_week_history else None

    span = _window_span(window)
    notes = []
    coverage = get_coverage(region, age_group)
    if not coverage["is_national"]:
        notes.append(coverage["note"])
    for year in selected[1:]:
        if metric[year] is None:
            notes.append(
                f"{year}: Für {span} liegen keine vollständigen RKI-Daten vor (die Daten beginnen "
                f"{coverage['first_week']}). Dieses Jahr geht nicht in den Ø der Vergleichsjahre ein."
            )

    return {
        "region": region,
        "region_display_name": REGION_DISPLAY_NAMES.get(region, region),
        "age_group": age_group,
        "age_group_display_name": AGE_GROUP_DISPLAY_NAMES.get(age_group, age_group),
        "period": spec.key,
        "period_label": spec.label,
        "mode": "annual" if spec.is_multi_year else "window",
        "years": selected,
        "current_year": current_year,
        "previous_year": previous_year,
        "history_years": history_years,
        "history_years_text": _years_text(history_years),
        "window_start": window[0],
        "window_end": window[-1],
        "window_weeks": len(window),
        "window_span": span,
        "basis_label": f"Ø {span} {current_year}" if len(window) > 1 else f"{span} {current_year}",
        "current_value": _round(current_value),
        "previous_year_value": _round(previous_value),
        "change_vs_previous_percent": _percent_change(current_value, previous_value),
        "historical_average": _round(historical_average),
        "deviation_vs_history_percent": _percent_change(current_value, historical_average),
        "latest_week": latest_week,
        "latest_week_value": week_value,
        "previous_week": previous_week,
        "previous_week_value": values.get(previous_week) if previous_week else None,
        "week_change_percent": _percent_change(week_value, values.get(previous_week) if previous_week else None),
        "previous_year_week": previous_year_week,
        "previous_year_week_value": previous_year_week_value,
        "week_change_vs_previous_year_percent": _percent_change(week_value, previous_year_week_value),
        "same_week_history_average": _round(same_week_average),
        "week_deviation_vs_history_percent": _percent_change(week_value, same_week_average),
        "notes": notes,
        "axis": axis,
        "series": series,
        "history_mean": history_mean,
        "summaries": summaries,
    }


def get_status() -> dict:
    with SessionLocal() as session:
        row = session.execute(STATUS_SQL).mappings().first()
    if row is None:
        return {
            "total_rows": 0,
            "latest_week": None,
            "last_etl": None,
        }
    data = dict(row)
    return {
        "total_rows": data.pop("total_rows"),
        "latest_week": data.pop("latest_week"),
        "last_etl": data,
    }
