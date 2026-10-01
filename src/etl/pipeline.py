"""End-to-end ETL orchestration."""
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from src.core.config import PROJECT_ROOT, settings
from src.core.constants import SOURCE_TYPE_LIVE, SOURCE_TYPE_LOCAL_TEST
from src.db.connection import SessionLocal, init_database
from src.db.models import AreIncidence, EtlRun
from src.db.seed import seed_age_groups
from src.etl.extract import download_rki_data, load_local_tsv
from src.etl.load import upsert_dimensions, upsert_fact_rows
from src.etl.transform import transform_data
from src.etl.validate import validate_data

logger = logging.getLogger(__name__)


def _latest_success_hash(session) -> str | None:  # noqa: ANN001
    return session.scalar(
        select(EtlRun.source_hash)
        .where(EtlRun.status.in_(["SUCCESS", "NO_CHANGE"]))
        .where(EtlRun.source_type == SOURCE_TYPE_LIVE)
        .order_by(EtlRun.etl_run_id.desc())
        .limit(1)
    )


def _portable_path(path: Path) -> str:
    """Project-relative path for the audit log, so a copied project does not keep a stale absolute path."""
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def run_etl(force: bool = False, local_file: Path | None = None) -> dict:
    """Run the ETL from the live RKI source, or from a local TSV file (tests and the CLI helper)."""
    init_database()
    source_type = SOURCE_TYPE_LOCAL_TEST if local_file else SOURCE_TYPE_LIVE
    source_url = _portable_path(local_file) if local_file else settings.rki_data_url

    with SessionLocal() as session:
        run = EtlRun(status="IN_PROGRESS", source_type=source_type, source_url=source_url)
        session.add(run)
        session.commit()
        session.refresh(run)
        run_id = run.etl_run_id

    try:
        if local_file:
            raw_df, source_hash = load_local_tsv(local_file)
        else:
            raw_df, source_hash = download_rki_data()

        with SessionLocal() as session:
            if not force and source_type == SOURCE_TYPE_LIVE:
                previous_hash = _latest_success_hash(session)
                # Exclude current IN_PROGRESS run because it has no hash yet.
                if previous_hash == source_hash:
                    run = session.get(EtlRun, run_id)
                    run.status = "NO_CHANGE"
                    run.finished_at = datetime.utcnow()
                    run.source_hash = source_hash
                    run.rows_downloaded = len(raw_df)
                    run.rows_valid = len(raw_df)
                    session.commit()
                    return _result_dict(run)

        validation = validate_data(raw_df)
        transformed = transform_data(raw_df, validation.rejected_indices)

        with SessionLocal() as session:
            seed_age_groups(session)
            region_map, age_map = upsert_dimensions(session, transformed)
            inserted, updated = upsert_fact_rows(
                session,
                transformed,
                region_map,
                age_map,
                run_id,
                source_hash,
            )

            run = session.get(EtlRun, run_id)
            run.status = "SUCCESS"
            run.finished_at = datetime.utcnow()
            run.source_hash = source_hash
            run.rows_downloaded = len(raw_df)
            run.rows_valid = validation.valid_rows
            run.rows_rejected = validation.rejected_rows
            run.rows_inserted = inserted
            run.rows_updated = updated
            session.commit()
            session.refresh(run)
            return _result_dict(run)

    except Exception as exc:
        logger.exception("ETL failed")
        with SessionLocal() as session:
            run = session.get(EtlRun, run_id)
            if run is not None:
                run.status = "FAILED"
                run.finished_at = datetime.utcnow()
                run.error_message = str(exc)[:4000]
                session.commit()
        raise


def import_if_empty() -> dict | None:
    """Download the RKI file when the database has no data yet (first start). Never raises."""
    with SessionLocal() as session:
        if session.scalar(select(AreIncidence.incidence_id).limit(1)) is not None:
            return None
    logger.info("Database is empty - importing the current RKI data")
    try:
        return run_etl(force=True)
    except Exception:  # no internet or RKI unreachable: the dashboard still offers the manual import button
        logger.warning("Automatic import failed; use 'Aktuelle RKI-Daten laden' in the dashboard", exc_info=True)
        return None


def _result_dict(run: EtlRun) -> dict:
    return {
        "run_id": run.etl_run_id,
        "status": run.status,
        "source_type": run.source_type,
        "source_url": run.source_url,
        "source_hash": run.source_hash,
        "rows_downloaded": run.rows_downloaded,
        "rows_valid": run.rows_valid,
        "rows_rejected": run.rows_rejected,
        "rows_inserted": run.rows_inserted,
        "rows_updated": run.rows_updated,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "error_message": run.error_message,
    }
