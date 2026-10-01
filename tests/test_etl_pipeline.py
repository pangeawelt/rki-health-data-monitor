from pathlib import Path

from sqlalchemy import func, select

from src.core.config import PROJECT_ROOT
from src.core.constants import SOURCE_TYPE_LOCAL_TEST
from src.db.connection import SessionLocal
from src.db.models import AreIncidence
from src.etl import pipeline
from src.etl.extract import load_local_tsv
from src.etl.pipeline import _portable_path, import_if_empty, run_etl


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


def test_first_start_imports_only_into_an_empty_database(rki_db, rki_tsv, monkeypatch) -> None:
    rows = _fact_rows()
    assert import_if_empty() is None  # data present: nothing is downloaded

    with SessionLocal() as session:
        session.query(AreIncidence).delete()
        session.commit()

    def unreachable():
        raise ConnectionError("no internet")

    monkeypatch.setattr(pipeline, "download_rki_data", unreachable)
    assert import_if_empty() is None  # a failed download must not stop the application
    assert _fact_rows() == 0

    monkeypatch.setattr(pipeline, "download_rki_data", lambda: load_local_tsv(rki_tsv))
    result = import_if_empty()
    assert result["status"] == "SUCCESS" and _fact_rows() == rows
