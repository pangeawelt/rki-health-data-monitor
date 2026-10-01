"""Test setup: point the app at a throw-away SQLite file before any ``src`` module is imported.

Tests must never touch the real ``data/rki_monitor.db``, so the environment variable is set at import time of
this file, which pytest loads before the test modules.
"""
import atexit
import os
import shutil
import tempfile
from pathlib import Path

import pytest

_TMP_DIR = tempfile.mkdtemp(prefix="rki-monitor-tests-")
os.environ["DATABASE_PATH"] = str(Path(_TMP_DIR) / "test.db")
atexit.register(shutil.rmtree, _TMP_DIR, ignore_errors=True)

# Same structure as the real RKI file: Germany from 2012-W40, the states from 2022-W40, up to 2026-W39.
REGIONS = {"Bundesweit": (0, (2012, 40)), "Baden-Wuerttemberg": (8, (2022, 40)), "Bayern": (9, (2022, 40))}
AGE_GROUPS = ("00+", "60+")
LAST_WEEK = (2026, 39)
HEADER = "Saison\tKalenderwoche\tBundesland\tBundesland_ID\tAltersgruppe\tARE_Konsultationsinzidenz"


def synthetic_value(region_id: int, age_group: str, year: int, week: int) -> int:
    """A reproducible incidence that differs by region, age group, year and week."""
    return 300 + 9 * week + 17 * (year - 2000) + 40 * region_id + (25 if age_group == "60+" else 0) + 11 * (week % 7)


def synthetic_tsv() -> str:
    from src.core.weeks import iso_weeks_in_year

    lines = [HEADER]
    for region, (region_id, first) in REGIONS.items():
        for year in range(first[0], LAST_WEEK[0] + 1):
            for week in range(1, iso_weeks_in_year(year) + 1):
                if (year, week) < first or (year, week) > LAST_WEEK:
                    continue
                season_start = year if week >= 40 else year - 1
                season = f"{season_start}/{(season_start + 1) % 100:02d}"
                for age_group in AGE_GROUPS:
                    value = synthetic_value(region_id, age_group, year, week)
                    lines.append(f"{season}\t{year}-W{week:02d}\t{region}\t{region_id}\t{age_group}\t{value}")
    return "\n".join(lines) + "\n"


@pytest.fixture(scope="session")
def rki_tsv(tmp_path_factory) -> Path:
    """A generated TSV in the RKI format (no network access, no real data)."""
    path = tmp_path_factory.mktemp("rki") / "ARE-Konsultationsinzidenz.tsv"
    path.write_text(synthetic_tsv(), encoding="utf-8", newline="\n")
    return path


@pytest.fixture(scope="session")
def rki_db(rki_tsv) -> None:
    """Temporary database filled through the regular ETL from the generated TSV."""
    from src.etl.pipeline import run_etl

    run_etl(force=True, local_file=rki_tsv)
