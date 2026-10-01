from pathlib import Path

from sqlalchemy import func, select

from src.core.config import PROJECT_ROOT
from src.core.constants import SOURCE_TYPE_LOCAL_TEST
from src.db.connection import SessionLocal
from src.db.models import AreIncidence
from src.etl.pipeline import _portable_path, run_etl


def _fact_rows() -> int:
    with SessionLocal() as session:
        return session.scalar(select(func.count()).select_from(AreIncidence))


def test_etl_imports_a_tsv_and_a_second_run_only_updates(rki_db, rki_tsv) -> None:
    rows = _fact_rows()
    assert rows > 1000

    result = run_etl(force=True, local_file=rki_tsv)
    assert result["status"] == "SUCCESS"
    assert result["source_type"] == SOURCE_TYPE_LOCAL_TEST
    assert (result["rows_inserted"], result["rows_updated"]) == (0, rows)  # UPSERT: same keys, no duplicates
    assert _fact_rows() == rows


def test_audit_log_stores_project_relative_paths() -> None:
    assert _portable_path(PROJECT_ROOT / "data" / "x.tsv") == "data/x.tsv"
    outside = Path(PROJECT_ROOT.anchor) / "elsewhere" / "x.tsv"
    assert _portable_path(outside) == str(outside)
