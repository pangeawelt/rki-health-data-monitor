import pytest

from src.core.periods import PERIODS_BY_KEY, get_period, resolve_weeks


def _weeks(first_year: int, last_year: int, last_week: int) -> list[str]:
    return [
        f"{year}-W{week:02d}"
        for year in range(first_year, last_year + 1)
        for week in range(1, (last_week if year == last_year else 52) + 1)
    ]


WEEKS = _weeks(2023, 2026, 39)


def test_week_based_periods_end_at_the_latest_week() -> None:
    assert resolve_weeks(get_period("week"), WEEKS) == ["2026-W38", "2026-W39"]  # last week plus the week before
    assert resolve_weeks(get_period("month"), WEEKS) == ["2026-W36", "2026-W37", "2026-W38", "2026-W39"]
    quarter = resolve_weeks(get_period("quarter"), WEEKS)
    assert (len(quarter), quarter[0]) == (13, "2026-W27")


def test_this_year_runs_from_january_to_the_latest_week() -> None:
    year = resolve_weeks(get_period("year"), WEEKS)
    assert (year[0], year[-1], len(year)) == ("2026-W01", "2026-W39", 39)


def test_multi_year_periods_start_in_january_of_the_first_year() -> None:
    three = resolve_weeks(get_period("three_years"), WEEKS)
    assert (three[0], three[-1]) == ("2024-W01", "2026-W39")
    five = resolve_weeks(get_period("five_years"), WEEKS)
    assert five[0] == "2023-W01"  # the data starts later than five years back


def test_period_can_end_at_an_earlier_week() -> None:
    assert resolve_weeks(get_period("month"), WEEKS, "2025-W10") == ["2025-W07", "2025-W08", "2025-W09", "2025-W10"]
    assert resolve_weeks(get_period("year"), WEEKS, "2025-W10")[0] == "2025-W01"


def test_month_window_can_span_the_turn_of_the_year() -> None:
    weeks = ["2026-W52", "2026-W53", "2027-W01", "2027-W02", "2027-W03"]
    assert resolve_weeks(get_period("month"), weeks) == ["2026-W53", "2027-W01", "2027-W02", "2027-W03"]


def test_empty_data_and_unknown_period() -> None:
    assert resolve_weeks(get_period("month"), []) == []
    with pytest.raises(ValueError):
        get_period("decade")


def test_only_multi_year_periods_are_annual() -> None:
    assert [p.key for p in PERIODS_BY_KEY.values() if p.is_multi_year] == ["three_years", "five_years"]
