"""SQLite loading and UPSERT logic using SQLAlchemy Core."""
from datetime import datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from src.core.constants import UPSERT_CHUNK_SIZE
from src.db.models import AgeGroupModel, AreIncidence, Region


def _chunks(items: list[dict], size: int):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def upsert_dimensions(session, df: pd.DataFrame) -> tuple[dict[str, int], dict[str, int]]:  # noqa: ANN001
    regions_df = df[["rki_region_id", "region_name"]].drop_duplicates()
    for row in regions_df.to_dict("records"):
        stmt = sqlite_insert(Region).values(
            rki_region_id=int(row["rki_region_id"]),
            region_name=row["region_name"],
            is_national=int(row["rki_region_id"]) == 0,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[Region.rki_region_id],
            set_={"region_name": stmt.excluded.region_name, "is_national": stmt.excluded.is_national},
        )
        session.execute(stmt)

    session.flush()
    region_map = dict(session.execute(select(Region.region_name, Region.region_id)).all())
    age_map = dict(session.execute(select(AgeGroupModel.age_group_code, AgeGroupModel.age_group_id)).all())
    return region_map, age_map


def upsert_fact_rows(
    session,  # noqa: ANN001
    df: pd.DataFrame,
    region_map: dict[str, int],
    age_map: dict[str, int],
    run_id: int,
    source_hash: str,
) -> tuple[int, int]:
    existing = set(
        session.execute(
            select(AreIncidence.region_id, AreIncidence.age_group_id, AreIncidence.calendar_week)
        ).all()
    )

    now = datetime.utcnow()
    records: list[dict] = []
    inserted = 0
    updated = 0

    for row in df.itertuples(index=False):
        region_id = region_map[row.region_name]
        age_group_id = age_map[row.age_group_code]
        key = (region_id, age_group_id, row.calendar_week)
        if key in existing:
            updated += 1
        else:
            inserted += 1
            existing.add(key)

        value = None if pd.isna(row.incidence_value) else float(row.incidence_value)
        records.append(
            {
                "region_id": region_id,
                "age_group_id": age_group_id,
                "season": row.season,
                "calendar_week": row.calendar_week,
                "incidence_value": value,
                "source_hash": source_hash,
                "imported_at": now,
                "updated_at": now,
                "imported_by_run_id": run_id,
            }
        )

    # Compile the statement once and run it as executemany; a multi-row VALUES clause per chunk
    # made SQLAlchemy recompile a 9000-parameter statement every time (~10 s for the full dataset).
    stmt = sqlite_insert(AreIncidence)
    stmt = stmt.on_conflict_do_update(
        index_elements=[
            AreIncidence.region_id,
            AreIncidence.age_group_id,
            AreIncidence.calendar_week,
        ],
        set_={
            "season": stmt.excluded.season,
            "incidence_value": stmt.excluded.incidence_value,
            "source_hash": stmt.excluded.source_hash,
            "updated_at": stmt.excluded.updated_at,
            "imported_by_run_id": stmt.excluded.imported_by_run_id,
        },
    )
    for chunk in _chunks(records, UPSERT_CHUNK_SIZE):
        session.execute(stmt, chunk)

    return inserted, updated
