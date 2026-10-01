"""Selectable evaluation periods of the dashboard (last week, last month, year to date, ...)."""
from typing import NamedTuple

KIND_WEEKS = "weeks"  # the last N calendar weeks
KIND_YEAR_TO_DATE = "year_to_date"  # from week 1 of the latest year up to the latest week
KIND_YEARS = "years"  # from week 1 of the year N-1 years before the latest year up to the latest week


class Period(NamedTuple):
    key: str
    label: str
    kind: str
    amount: int

    @property
    def is_multi_year(self) -> bool:
        return self.kind == KIND_YEARS


PERIODS = (
    Period("week", "Letzte Woche (mit Vorwoche)", KIND_WEEKS, 2),  # two points make a line
    Period("month", "Letzter Monat (4 Wochen)", KIND_WEEKS, 4),
    Period("quarter", "Letzte 3 Monate (13 Wochen)", KIND_WEEKS, 13),
    Period("year", "Dieses Jahr (seit Januar)", KIND_YEAR_TO_DATE, 1),
    Period("three_years", "Letzte 3 Jahre", KIND_YEARS, 3),
    Period("five_years", "Letzte 5 Jahre", KIND_YEARS, 5),
)
PERIODS_BY_KEY = {period.key: period for period in PERIODS}
DEFAULT_PERIOD = "month"


def get_period(key: str) -> Period:
    try:
        return PERIODS_BY_KEY[key]
    except KeyError:
        raise ValueError(f"period must be one of {tuple(PERIODS_BY_KEY)}") from None


def resolve_weeks(period: Period, weeks: list[str], end_week: str | None = None) -> list[str]:
    """Calendar weeks (ISO ``YYYY-Www``) of the period, oldest first, ending at ``end_week``.

    ``weeks`` are all available weeks; ``end_week`` defaults to the latest one.
    """
    available = sorted(weeks)
    if not available:
        return []
    end = end_week or available[-1]
    until = [week for week in available if week <= end]
    if period.kind == KIND_WEEKS:
        return until[-period.amount :]
    first_year = int(end[:4]) - (period.amount - 1)
    return [week for week in until if week >= f"{first_year}-W01"]
