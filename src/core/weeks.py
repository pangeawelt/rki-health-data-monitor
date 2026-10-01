"""ISO calendar-week helpers for labels like ``2026-W39``."""
import re
from datetime import date

_WEEK = re.compile(r"^(\d{4})-W(\d{2})$")


def _parse(calendar_week: str) -> tuple[int, int]:
    match = _WEEK.match(calendar_week)
    if not match:
        raise ValueError(f"Invalid calendar week: {calendar_week!r}")
    return int(match.group(1)), int(match.group(2))


def week_year(calendar_week: str) -> int:
    return _parse(calendar_week)[0]


def week_number(calendar_week: str) -> int:
    """ISO week number (1..53)."""
    return _parse(calendar_week)[1]


def week_label(number: int) -> str:
    return f"KW{number:02d}"


def iso_weeks_in_year(year: int) -> int:
    """52 or 53; December 28th always lies in the last ISO week of its year."""
    return date(year, 12, 28).isocalendar()[1]


def shift_week(calendar_week: str, years_back: int) -> str | None:
    """The same ISO week ``years_back`` years earlier, or None if that year has no such week (week 53)."""
    year, week = _parse(calendar_week)
    year -= years_back
    return f"{year}-W{week:02d}" if week <= iso_weeks_in_year(year) else None


MONTHS = (
    "JANUAR", "FEBRUAR", "MÄRZ", "APRIL", "MAI", "JUNI",
    "JULI", "AUGUST", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DEZEMBER",
)
MONTHS_SHORT = ("JAN", "FEB", "MÄR", "APR", "MAI", "JUN", "JUL", "AUG", "SEP", "OKT", "NOV", "DEZ")


def month_name(calendar_week: str, short: bool = False) -> str:
    """Upper-case German month of an ISO week: the month that contains the week's Thursday."""
    year, week = _parse(calendar_week)
    month = date.fromisocalendar(year, week, 4).month
    return (MONTHS_SHORT if short else MONTHS)[month - 1]


def short_month(month: str) -> str:
    """Abbreviation for a month name from :data:`MONTHS`, e.g. ``SEPTEMBER`` -> ``SEP``."""
    return MONTHS_SHORT[MONTHS.index(month)]
