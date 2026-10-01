import pytest

from src.core.weeks import iso_weeks_in_year, month_name, shift_week, short_month, week_label, week_number, week_year


def test_week_parts() -> None:
    assert week_year("2026-W39") == 2026
    assert week_number("2026-W05") == 5
    assert week_label(5) == "KW05"


def test_iso_years_have_52_or_53_weeks() -> None:
    assert iso_weeks_in_year(2025) == 52
    assert iso_weeks_in_year(2026) == 53
    assert iso_weeks_in_year(2020) == 53


def test_shift_week_keeps_the_week_number_and_skips_missing_week_53() -> None:
    assert shift_week("2026-W39", 1) == "2025-W39"
    assert shift_week("2026-W39", 4) == "2022-W39"
    assert shift_week("2026-W53", 1) is None  # 2025 has no week 53
    assert shift_week("2026-W53", 6) == "2020-W53"


def test_month_is_the_one_containing_the_thursday_of_the_week() -> None:
    assert month_name("2026-W29") == "JULI"
    assert month_name("2026-W36") == "SEPTEMBER"  # Monday is 31 August, Thursday is 3 September
    assert month_name("2026-W01") == "JANUAR"
    assert month_name("2025-W01") == "JANUAR"  # starts on Monday 30 December 2024, Thursday is 2 January
    assert month_name("2020-W53") == "DEZEMBER"
    assert month_name("2026-W03", short=True) == "JAN"
    assert short_month("MÄRZ") == "MÄR"


@pytest.mark.parametrize("value", ["2025-40", "2025-W4", "W40", ""])
def test_invalid_calendar_week_is_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        week_number(value)
