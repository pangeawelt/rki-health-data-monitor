import pytest

from src.core.weeks import week_label
from src.etl.extract import parse_tsv_bytes
from src.services.analytics import get_coverage, get_incidence, get_year_comparison, get_years


@pytest.fixture(scope="module")
def raw_values(rki_tsv) -> dict[str, float]:
    """Raw values of Bundesweit / all age groups by calendar week, read straight from the TSV."""
    frame = parse_tsv_bytes(rki_tsv.read_bytes())
    rows = frame[(frame["Bundesland"] == "Bundesweit") & (frame["Altersgruppe"] == "00+")]
    return dict(zip(rows["Kalenderwoche"], rows["ARE_Konsultationsinzidenz"].astype(float)))


def _mean(values: dict[str, float], weeks: list[str]) -> float:
    return sum(values[week] for week in weeks) / len(weeks)


def test_years_are_listed_newest_first_and_states_start_later(rki_db) -> None:
    national = get_years("Bundesweit", "00+")
    assert national[0] > national[-1]
    assert national[-1] == 2012
    assert get_years("Bayern", "00+")[-1] == 2022


def test_trend_follows_the_selected_period(rki_db, raw_values) -> None:
    week = get_incidence("Bundesweit", "00+", "week")
    assert (week["weeks"], len(week["series"]), week["from_week"]) == (2, 2, "2026-W38")  # two points make a line
    assert week["latest_value"] == raw_values["2026-W39"]
    assert week["previous_value"] == raw_values["2026-W38"]

    month = get_incidence("Bundesweit", "00+", "month")
    assert [p["calendar_week"] for p in month["series"]] == ["2026-W36", "2026-W37", "2026-W38", "2026-W39"]
    assert [p["month"] for p in month["series"]] == ["SEPTEMBER"] * 4
    # the moving average of the first shown week already includes the three weeks before it
    assert month["series"][0]["moving_average_4w"] == _mean(raw_values, ["2026-W33", "2026-W34", "2026-W35", "2026-W36"])

    year = get_incidence("Bundesweit", "00+", "year")
    assert (year["from_week"], year["to_week"], year["weeks"]) == ("2026-W01", "2026-W39", 39)
    assert get_incidence("Bundesweit", "00+", "three_years")["from_week"] == "2024-W01"

    with pytest.raises(ValueError):
        get_incidence("Bundesweit", "00+", "decade")


def test_one_month_is_compared_with_the_same_weeks_of_the_previous_years(rki_db, raw_values) -> None:
    result = get_year_comparison("Bundesweit", "00+", [2026, 2025, 2024, 2023], "month")

    assert result["mode"] == "window"
    assert result["years"] == [2026, 2025, 2024, 2023]
    assert (result["window_start"], result["window_end"]) == ("2026-W36", "2026-W39")
    averages = {year: _mean(raw_values, [f"{year}-W{w}" for w in (36, 37, 38, 39)]) for year in result["years"]}

    assert result["current_value"] == round(averages[2026], 1)
    assert result["previous_year_value"] == round(averages[2025], 1)
    assert result["change_vs_previous_percent"] == round((averages[2026] - averages[2025]) / averages[2025] * 100, 1)
    history = (averages[2025] + averages[2024] + averages[2023]) / 3
    assert result["historical_average"] == round(history, 1)
    assert result["deviation_vs_history_percent"] == round((averages[2026] - history) / history * 100, 1)

    for item in result["series"]:
        assert [p["position"] for p in item["points"]] == [1, 2, 3, 4]
        assert [p["calendar_week"] for p in item["points"]] == [f"{item['year']}-W{w}" for w in (36, 37, 38, 39)]


def test_axis_follows_calendar_week_order_with_months(rki_db) -> None:
    month = get_year_comparison("Bundesweit", "00+", None, "month")
    assert [(t["label"], t["month"]) for t in month["axis"]] == [
        ("KW36", "SEPTEMBER"), ("KW37", "SEPTEMBER"), ("KW38", "SEPTEMBER"), ("KW39", "SEPTEMBER"),
    ]

    year = get_year_comparison("Bundesweit", "00+", None, "year")
    positions = [t["position"] for t in year["axis"]]
    assert positions == list(range(1, 40))  # KW01 ... KW39, never wrapping around
    assert (year["axis"][0]["label"], year["axis"][0]["month"]) == ("KW01", "JANUAR")
    assert year["axis"][28]["label"] == week_label(29) and year["axis"][28]["month"] == "JULI"


def test_last_week_compares_two_calendar_weeks_as_a_line(rki_db, raw_values) -> None:
    result = get_year_comparison("Bundesweit", "00+", [2026, 2025], "week")
    assert [t["label"] for t in result["axis"]] == ["KW38", "KW39"]
    assert result["window_weeks"] == 2
    assert result["basis_label"] == "Ø KW38–KW39 2026"
    assert result["current_value"] == round((raw_values["2026-W38"] + raw_values["2026-W39"]) / 2, 1)


def test_latest_week_is_compared_with_the_week_before_and_the_same_week_of_other_years(rki_db, raw_values) -> None:
    result = get_year_comparison("Bundesweit", "00+", [2026, 2025, 2024, 2023], "month")

    assert result["latest_week"] == "2026-W39"
    assert result["latest_week_value"] == raw_values["2026-W39"]
    assert (result["previous_week"], result["previous_week_value"]) == ("2026-W38", raw_values["2026-W38"])
    assert result["week_change_percent"] == round(
        (raw_values["2026-W39"] - raw_values["2026-W38"]) / raw_values["2026-W38"] * 100, 1
    )
    assert (result["previous_year_week"], result["previous_year_week_value"]) == ("2025-W39", raw_values["2025-W39"])
    same_week_mean = (raw_values["2025-W39"] + raw_values["2024-W39"] + raw_values["2023-W39"]) / 3
    assert result["same_week_history_average"] == round(same_week_mean, 1)
    assert result["week_deviation_vs_history_percent"] == round(
        (raw_values["2026-W39"] - same_week_mean) / same_week_mean * 100, 1
    )


def test_reference_years_are_named_explicitly(rki_db) -> None:
    result = get_year_comparison("Bundesweit", "00+", [2026, 2025, 2024, 2023, 2022], "month")
    assert result["history_years"] == [2025, 2024, 2023, 2022]
    assert result["history_years_text"] == "2022–2025"
    assert result["window_span"] == "KW36–KW39"
    assert get_year_comparison("Bundesweit", "00+", [2026, 2025, 2023], "month")["history_years_text"] == "2023, 2025"


def test_state_data_gets_an_availability_note_and_incomplete_years_are_flagged(rki_db) -> None:
    result = get_year_comparison("Bayern", "00+", [2026, 2025, 2022], "year")
    assert any("erst ab 2022-W40" in note for note in result["notes"])
    assert any(note.startswith("2022:") and "KW01–KW39" in note for note in result["notes"])
    assert get_year_comparison("Bundesweit", "00+", [2026, 2025], "month")["notes"] == []


def test_coverage_explains_when_the_rki_data_starts(rki_db) -> None:
    national = get_coverage("Bundesweit", "00+")
    assert (national["first_week"], national["is_national"], national["first_full_year"]) == ("2012-W40", True, 2013)

    state = get_coverage("Baden-Wuerttemberg", "00+")
    assert (state["first_week"], state["is_national"], state["first_full_year"]) == ("2022-W40", False, 2023)
    assert state["national_first_week"] == "2012-W40"
    assert "Saison 2022/23" in state["note"] and "Baden-Württemberg" in state["note"]

    assert get_coverage("Atlantis", "00+")["first_week"] is None


def test_multi_year_period_draws_whole_years_but_compares_year_to_date(rki_db, raw_values) -> None:
    result = get_year_comparison("Bundesweit", "00+", None, "three_years")

    assert result["mode"] == "annual"
    assert result["years"] == [2026, 2025, 2024]  # capped at three years
    assert [t["label"] for t in result["axis"]][:2] == ["KW01", "KW02"]
    assert result["axis"][-1]["label"] == "KW52"
    current = next(s for s in result["series"] if s["year"] == 2026)
    previous = next(s for s in result["series"] if s["year"] == 2025)
    assert len(current["points"]) == 39 and len(previous["points"]) == 52
    ytd = [f"2026-W{w:02d}" for w in range(1, 40)]
    assert result["current_value"] == round(_mean(raw_values, ytd), 1)
    assert result["previous_year_value"] == round(_mean(raw_values, [w.replace("2026", "2025") for w in ytd]), 1)


def test_history_mean_and_summaries(rki_db, raw_values) -> None:
    result = get_year_comparison("Bundesweit", "00+", [2026, 2025, 2024], "month")
    first = result["history_mean"][0]
    assert (first["position"], first["label"]) == (1, "KW36")
    assert first["value"] == round((raw_values["2025-W36"] + raw_values["2024-W36"]) / 2, 1)

    summary = next(s for s in result["summaries"] if s["year"] == 2025)
    values = {w: raw_values[f"2025-{w}"] for w in ("W36", "W37", "W38", "W39")}
    assert summary["weeks_count"] == 4
    assert summary["peak"] == max(values.values())
    assert summary["peak_week"] == f"2025-{max(values, key=values.get)}"


def test_invalid_requests(rki_db) -> None:
    result = get_year_comparison("Bundesweit", "00+", [2026, 2025, 1999], "month")
    assert result["years"] == [2026, 2025]  # unknown years are ignored
    assert len(get_year_comparison("Bundesweit", "00+", list(range(2012, 2027)), "month")["years"]) == 5

    with pytest.raises(ValueError):
        get_year_comparison("Bundesweit", "00+", [2026], "month")
    with pytest.raises(ValueError):
        get_year_comparison("Atlantis", "00+", None, "month")
    with pytest.raises(ValueError):
        get_year_comparison("Bundesweit", "00+", None, "decade")


def test_incomplete_windows_give_no_average(rki_db) -> None:
    # Bavaria starts in 2022-W40: its 2022 "year to date" window is incomplete and must not be averaged.
    result = get_year_comparison("Bayern", "00+", [2026, 2025, 2022], "year")
    assert result["current_value"] is not None
    previous_values = {s["year"]: s for s in result["summaries"]}
    assert previous_values[2022]["weeks_count"] < 39
    assert result["historical_average"] == result["previous_year_value"]  # 2022 does not enter the mean
