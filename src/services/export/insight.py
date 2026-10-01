"""Short interpretation ("Einordnung") of the key figures, so the message is readable without the chart.

Each chart gets a one-line headline (always visible) and a longer Einordnung (opened on demand).
"""
from src.services.export.formatting import format_de, format_percent, format_value

UNIT = "je 100.000 Einwohner"
SAME_LEVEL_PERCENT = 2.0  # below this a change to the previous week or year counts as "auf dem Niveau"
CLOSE_TO_MEAN_PERCENT = 5.0  # below this the level counts as "auf dem durchschnittlichen Niveau"
STRONG_PERCENT = 15.0  # from here on the distance to the mean is "deutlich"
TREND_STABLE_PERCENT = 10.0
TREND_STRONG_PERCENT = 25.0


def _arrow(change: float | None) -> str:
    if change is None or abs(change) < SAME_LEVEL_PERCENT:
        return "●"
    return "▲" if change > 0 else "▼"


def _compare(change: float | None, dative: str, genitive: str) -> str | None:
    """``35,4 % über der Vorwoche`` or, for tiny changes, ``auf dem Niveau der Vorwoche (+0,5 %)``."""
    if change is None:
        return None
    if abs(change) < SAME_LEVEL_PERCENT:
        return f"auf dem Niveau {genitive} ({format_percent(change)})"
    return f"{format_de(abs(change), 1)} % {'über' if change > 0 else 'unter'} {dative}"


def _level(deviation: float | None, years: str) -> str | None:
    """``deutlich unter dem durchschnittlichen Niveau der Vergleichsjahre 2022–2025``."""
    if deviation is None:
        return None
    reference = f"der Vergleichsjahre {years}"
    if abs(deviation) < CLOSE_TO_MEAN_PERCENT:
        return f"auf dem durchschnittlichen Niveau {reference} ({format_percent(deviation)})"
    quality = "leicht" if abs(deviation) < STRONG_PERCENT else "deutlich"
    return f"{quality} {'über' if deviation > 0 else 'unter'} dem durchschnittlichen Niveau {reference}"


def _trend_word(values: list[float]) -> str | None:
    """``deutlich steigend``, ``fallend`` or ``weitgehend stabil`` for the first-to-last change of a series."""
    if len(values) < 3 or not values[0]:
        return None
    change = (values[-1] - values[0]) / values[0] * 100
    if abs(change) < TREND_STABLE_PERCENT:
        return "weitgehend stabil"
    return ("deutlich " if abs(change) >= TREND_STRONG_PERCENT else "") + ("steigend" if change > 0 else "fallend")


def _headline_change(change: float | None, reference: str) -> str | None:
    if change is None:
        return None
    if abs(change) < SAME_LEVEL_PERCENT:
        return f"● unverändert {reference} ({format_percent(change)})"
    return f"{_arrow(change)} {format_de(abs(change), 1)} % {reference}"


def trend_headline(incidence: dict) -> str:
    """One line: direction against the previous week and the trend within the period."""
    values = [point["value"] for point in incidence["series"] if point["value"] is not None]
    word = _trend_word(values)
    parts = [_headline_change(incidence["change_percent"], "zur Vorwoche"), f"Trend: {word}" if word else None]
    return " · ".join(part for part in parts if part) or "Kein Vergleichswert verfügbar"


def year_headline(comparison: dict) -> str:
    """One line: direction against the previous week, the previous year and the mean of the comparison years."""
    deviation = comparison["deviation_vs_history_percent"]
    level = None
    if deviation is not None:
        years = comparison["history_years_text"]
        if abs(deviation) < CLOSE_TO_MEAN_PERCENT:
            level = f"● auf dem Niveau des Ø {years}"
        else:
            quality = "leicht" if abs(deviation) < STRONG_PERCENT else "deutlich"
            level = f"{_arrow(deviation)} {quality} {'über' if deviation > 0 else 'unter'} Ø {years}"
    parts = [
        _headline_change(comparison["week_change_percent"], "zur Vorwoche"),
        _headline_change(comparison["week_change_vs_previous_year_percent"], "zum Vorjahr"),
        level,
    ]
    return " · ".join(part for part in parts if part) or "Kein Vergleichswert verfügbar"


def trend_insight(incidence: dict) -> str:
    """Einordnung for the trend chart: change to the previous week and the direction within the period."""
    latest = incidence["latest_value"]
    if latest is None:
        return "Einordnung: Für diese Auswahl liegt keine aktuelle Konsultationsinzidenz vor."
    text = f"Einordnung: Die aktuelle Konsultationsinzidenz ({incidence['latest_week']}: {format_value(latest)} {UNIT})"
    week = _compare(incidence["change_percent"], "der Vorwoche", "der Vorwoche")
    text += f" liegt {week}." if week else " kann nicht mit der Vorwoche verglichen werden."

    values = [point["value"] for point in incidence["series"] if point["value"] is not None]
    word = _trend_word(values)
    if word:
        text += (
            f" Trend im Zeitraum {incidence['period_label']} ({incidence['from_week']} bis {incidence['to_week']}): "
            f"{word} (von {format_value(values[0])} auf {format_value(values[-1])} {UNIT})."
        )
    return text


def year_insight(comparison: dict) -> str:
    """Einordnung for the year comparison: previous week, previous year and the mean of the comparison years."""
    value = comparison["latest_week_value"]
    if value is None:
        return "Einordnung: Für die aktuelle Woche liegt keine Konsultationsinzidenz vor."
    text = f"Einordnung: Die aktuelle Konsultationsinzidenz ({comparison['latest_week']}: {format_value(value)} {UNIT})"

    week = _compare(comparison["week_change_percent"], "der Vorwoche", "der Vorwoche")
    year = _compare(comparison["week_change_vs_previous_year_percent"], "dem Vorjahr", "des Vorjahres")
    if year and comparison["previous_year_week"]:
        year += f" ({comparison['previous_year_week']}: {format_value(comparison['previous_year_week_value'])})"
    parts = [part for part in (week, year) if part]
    if parts:
        text += f" liegt {' und '.join(parts)}."

    deviation = comparison["deviation_vs_history_percent"]
    level = _level(deviation, comparison["history_years_text"])
    if level:
        week_change = comparison["week_change_percent"]
        contrast = (
            week_change is not None
            and abs(week_change) >= SAME_LEVEL_PERCENT
            and abs(deviation) >= CLOSE_TO_MEAN_PERCENT
            and (week_change > 0) != (deviation > 0)
        )
        text += f" Im Zeitraum {comparison['basis_label']} liegt das Niveau{' jedoch' if contrast else ''} {level}."
    return text
