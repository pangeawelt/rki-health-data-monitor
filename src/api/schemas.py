from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    python_compatibility: str


class OptionResponse(BaseModel):
    code: str
    display_name: str


class PeriodResponse(BaseModel):
    key: str
    label: str


class SeriesPoint(BaseModel):
    calendar_week: str
    month: str
    value: float | None
    previous_value: float | None
    moving_average_4w: float | None


class IncidenceResponse(BaseModel):
    region: str
    region_display_name: str
    age_group: str
    age_group_display_name: str
    period: str
    period_label: str
    weeks: int
    from_week: str | None
    to_week: str | None
    latest_week: str | None
    latest_value: float | None
    previous_value: float | None
    change_percent: float | None
    series: list[SeriesPoint]


class AxisTick(BaseModel):
    position: int
    label: str
    month: str


class YearPoint(BaseModel):
    calendar_week: str
    month: str
    position: int
    value: float | None


class YearSeries(BaseModel):
    year: int
    points: list[YearPoint]


class HistoryPoint(AxisTick):
    value: float | None


class YearSummary(BaseModel):
    year: int
    weeks_count: int
    average: float | None
    peak: float | None
    peak_week: str | None


class YearComparisonResponse(BaseModel):
    region: str
    region_display_name: str
    age_group: str
    age_group_display_name: str
    period: str
    period_label: str
    mode: str
    years: list[int]
    current_year: int
    previous_year: int
    history_years: list[int]
    history_years_text: str
    window_start: str
    window_end: str
    window_weeks: int
    window_span: str
    basis_label: str
    current_value: float | None
    previous_year_value: float | None
    change_vs_previous_percent: float | None
    historical_average: float | None
    deviation_vs_history_percent: float | None
    latest_week: str
    latest_week_value: float | None
    previous_week: str | None
    previous_week_value: float | None
    week_change_percent: float | None
    previous_year_week: str | None
    previous_year_week_value: float | None
    week_change_vs_previous_year_percent: float | None
    same_week_history_average: float | None
    week_deviation_vs_history_percent: float | None
    notes: list[str]
    axis: list[AxisTick]
    series: list[YearSeries]
    history_mean: list[HistoryPoint]
    summaries: list[YearSummary]


class CoverageResponse(BaseModel):
    region: str
    region_display_name: str
    first_week: str | None
    last_week: str | None
    weeks_count: int
    is_national: bool
    national_first_week: str | None
    first_full_year: int | None
    note: str


class EtlResult(BaseModel):
    run_id: int
    status: str
    source_type: str
    source_url: str | None
    source_hash: str | None
    rows_downloaded: int
    rows_valid: int
    rows_rejected: int
    rows_inserted: int
    rows_updated: int
    started_at: datetime
    finished_at: datetime | None
    error_message: str | None
