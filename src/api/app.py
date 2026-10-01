"""FastAPI application for the local RKI Health Data Monitor API."""
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Response

from src.api.schemas import (
    EtlResult,
    HealthResponse,
    CoverageResponse,
    IncidenceResponse,
    OptionResponse,
    PeriodResponse,
    YearComparisonResponse,
)
from src.core.config import settings
from src.core.logging_config import configure_logging
from src.core.periods import DEFAULT_PERIOD, PERIODS
from src.db.connection import init_database
from src.etl.pipeline import run_etl
from src.services.analytics import (
    get_age_groups,
    get_coverage,
    get_incidence,
    get_regions,
    get_status,
    get_year_comparison,
    get_years,
)
from src.services.export.excel import build_excel
from src.services.export.model import ChartExport, trend_export, year_export
from src.services.export.pdf import build_pdf

EXPORT_FORMATS = {
    "xlsx": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", build_excel),
    "pdf": ("application/pdf", build_pdf),
}
ExportFormat = Literal["xlsx", "pdf"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_database()
    yield


app = FastAPI(
    title="RKI Health Data Monitor API",
    version="1.1.0",
    description=(
        "Lokale REST API für öffentliche ARE-Konsultationsinzidenz-Daten des "
        "Robert Koch-Instituts. Keine personenbezogenen Gesundheitsdaten."
    ),
    lifespan=lifespan,
)


def _download(chart: ChartExport, file_format: ExportFormat) -> Response:
    media_type, build = EXPORT_FORMATS[file_format]
    return Response(
        content=build(chart),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{chart.filename}.{file_format}"'},
    )


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        python_compatibility="Python 3.10+ (tested target: 3.10)",
    )


@app.post("/api/refresh", response_model=EtlResult, tags=["ETL"])
def refresh(force: bool = Query(default=False)) -> EtlResult:
    """Download the current RKI file (needs internet) and import it."""
    try:
        return EtlResult(**run_etl(force=force))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RKI refresh failed: {exc}") from exc


@app.get("/api/status", tags=["ETL"])
def status() -> dict:
    return get_status()


@app.get("/api/regions", response_model=list[OptionResponse], tags=["Analytics"])
def regions() -> list[OptionResponse]:
    return [OptionResponse(**item) for item in get_regions()]


@app.get("/api/age-groups", response_model=list[OptionResponse], tags=["Analytics"])
def age_groups(region: str = Query(..., min_length=1)) -> list[OptionResponse]:
    return [OptionResponse(**item) for item in get_age_groups(region)]


@app.get("/api/periods", response_model=list[PeriodResponse], tags=["Analytics"])
def periods() -> list[PeriodResponse]:
    """Selectable evaluation periods (last week, last month, ..., last 5 years)."""
    return [PeriodResponse(key=period.key, label=period.label) for period in PERIODS]


@app.get("/api/coverage", response_model=CoverageResponse, tags=["Analytics"])
def coverage(region: str = Query(..., min_length=1), age_group: str = Query(default="00+")) -> CoverageResponse:
    """From when the RKI publishes data for a region (state data starts later than the national series)."""
    return CoverageResponse(**get_coverage(region, age_group))


@app.get("/api/years", response_model=list[int], tags=["Analytics"])
def years(region: str = Query(..., min_length=1), age_group: str = Query(default="00+")) -> list[int]:
    return get_years(region, age_group)


@app.get("/api/incidence", response_model=IncidenceResponse, tags=["Analytics"])
def incidence(
    region: str = Query(..., min_length=1),
    age_group: str = Query(default="00+"),
    period: str = Query(default=DEFAULT_PERIOD),
) -> IncidenceResponse:
    try:
        return IncidenceResponse(**get_incidence(region, age_group, period))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/incidence/compare", response_model=YearComparisonResponse, tags=["Analytics"])
def compare_years(
    region: str = Query(..., min_length=1),
    age_group: str = Query(default="00+"),
    period: str = Query(default=DEFAULT_PERIOD),
    years: list[int] = Query(default=[]),
) -> YearComparisonResponse:
    """Same calendar weeks across years; without ``years`` the newest five years are compared."""
    try:
        return YearComparisonResponse(**get_year_comparison(region, age_group, years or None, period))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/incidence/export", tags=["Export"])
def export_incidence(
    region: str = Query(..., min_length=1),
    age_group: str = Query(default="00+"),
    period: str = Query(default=DEFAULT_PERIOD),
    file_format: ExportFormat = Query(default="xlsx", alias="format"),
) -> Response:
    """Trend chart (Zeitlicher Verlauf) as Excel workbook or PDF report."""
    try:
        data = get_incidence(region, age_group, period)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not data["series"]:
        raise HTTPException(status_code=404, detail="No data for this filter combination")
    return _download(trend_export(data, get_status(), datetime.now()), file_format)


@app.get("/api/incidence/compare/export", tags=["Export"])
def export_year_comparison(
    region: str = Query(..., min_length=1),
    age_group: str = Query(default="00+"),
    period: str = Query(default=DEFAULT_PERIOD),
    years: list[int] = Query(default=[]),
    file_format: ExportFormat = Query(default="xlsx", alias="format"),
) -> Response:
    """Year comparison chart (Jahresvergleich) as Excel workbook or PDF report."""
    try:
        data = get_year_comparison(region, age_group, years or None, period)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _download(year_export(data, get_status(), datetime.now()), file_format)
