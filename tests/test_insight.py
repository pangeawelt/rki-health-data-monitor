from src.services.export.insight import trend_headline, trend_insight, year_headline, year_insight


def _year(**overrides) -> dict:
    values = {
        "latest_week": "2026-W39", "latest_week_value": 968.0,
        "week_change_percent": 35.4, "week_change_vs_previous_year_percent": 4.5,
        "previous_year_week": "2025-W39", "previous_year_week_value": 926.0,
        "deviation_vs_history_percent": -22.0, "history_years_text": "2022–2025", "basis_label": "Ø KW36–KW39 2026",
    }
    values.update(overrides)
    return values


def test_year_insight_puts_week_year_and_history_into_context() -> None:
    text = year_insight(_year())
    assert text.startswith("Einordnung: Die aktuelle Konsultationsinzidenz (2026-W39: 968 je 100.000 Einwohner)")
    assert "35,4 % über der Vorwoche" in text
    assert "4,5 % über dem Vorjahr (2025-W39: 926)" in text
    assert "liegt das Niveau jedoch deutlich unter dem durchschnittlichen Niveau der Vergleichsjahre 2022–2025" in text


def test_year_insight_wording_follows_the_size_of_the_difference() -> None:
    assert "leicht über dem durchschnittlichen Niveau" in year_insight(_year(deviation_vs_history_percent=8.0))
    assert "auf dem durchschnittlichen Niveau der Vergleichsjahre 2022–2025 (+1,2 %)" in year_insight(
        _year(deviation_vs_history_percent=1.2)
    )
    same = year_insight(_year(week_change_vs_previous_year_percent=0.5, week_change_percent=-0.4))
    assert "auf dem Niveau der Vorwoche (-0,4 %)" in same and "auf dem Niveau des Vorjahres (+0,5 %)" in same
    assert " jedoch " not in year_insight(_year(deviation_vs_history_percent=20.0))  # same direction: no contrast


def test_year_insight_survives_missing_values() -> None:
    assert "keine Konsultationsinzidenz" in year_insight(_year(latest_week_value=None))
    text = year_insight(
        _year(week_change_vs_previous_year_percent=None, previous_year_week=None, deviation_vs_history_percent=None)
    )
    assert "über der Vorwoche" in text and "Vergleichsjahre" not in text


def _trend(values: list[float], change: float | None = 12.0) -> dict:
    return {
        "latest_value": values[-1], "latest_week": "2026-W39", "change_percent": change,
        "period_label": "Letzter Monat (4 Wochen)", "from_week": "2026-W36", "to_week": "2026-W39",
        "series": [{"value": v} for v in values],
    }


def test_trend_insight_names_the_direction_within_the_period() -> None:
    rising = trend_insight(_trend([600.0, 700.0, 800.0, 1000.0], 25.0))
    assert "25,0 % über der Vorwoche" in rising
    assert "deutlich steigend (von 600 auf 1.000 je 100.000 Einwohner)" in rising
    falling = trend_insight(_trend([1000.0, 900.0, 800.0], -11.1))
    assert "fallend" in falling and "deutlich" not in falling
    assert "weitgehend stabil" in trend_insight(_trend([1000.0, 1010.0, 1020.0], 1.0))


def test_trend_insight_without_enough_points_has_no_trend_sentence() -> None:
    assert "Trend im Zeitraum" not in trend_insight(_trend([900.0, 1000.0], 11.1))
    assert "kann nicht mit der Vorwoche verglichen werden" in trend_insight(_trend([900.0, 1000.0], None))


def test_year_headline_is_one_line_with_directions() -> None:
    assert year_headline(_year()) == (
        "▲ 35,4 % zur Vorwoche · ▲ 4,5 % zum Vorjahr · ▼ deutlich unter Ø 2022–2025"
    )
    assert year_headline(_year(week_change_percent=0.4, deviation_vs_history_percent=1.0)).startswith(
        "● unverändert zur Vorwoche (+0,4 %)"
    )
    assert year_headline(_year(week_change_percent=None, week_change_vs_previous_year_percent=None,
                               deviation_vs_history_percent=None)) == "Kein Vergleichswert verfügbar"


def test_trend_headline_names_change_and_trend() -> None:
    assert trend_headline(_trend([600.0, 700.0, 800.0, 1000.0], 25.0)) == "▲ 25,0 % zur Vorwoche · Trend: deutlich steigend"
    assert trend_headline(_trend([900.0, 1000.0], -11.1)) == "▼ 11,1 % zur Vorwoche"
