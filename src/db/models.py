"""SQLAlchemy database models."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Region(Base):
    __tablename__ = "dim_region"

    region_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rki_region_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    region_name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    is_national: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AgeGroupModel(Base):
    __tablename__ = "dim_age_group"

    age_group_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    age_group_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)


class EtlRun(Base):
    __tablename__ = "etl_run"

    etl_run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    rows_downloaded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_valid: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_inserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class AreIncidence(Base):
    __tablename__ = "fact_are_incidence"
    __table_args__ = (
        UniqueConstraint(
            "region_id", "age_group_id", "calendar_week",
            name="uq_are_region_age_week",
        ),
    )

    incidence_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("dim_region.region_id"), nullable=False, index=True)
    age_group_id: Mapped[int] = mapped_column(ForeignKey("dim_age_group.age_group_id"), nullable=False, index=True)
    season: Mapped[str] = mapped_column(String(16), nullable=False)
    calendar_week: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    incidence_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    imported_by_run_id: Mapped[int | None] = mapped_column(ForeignKey("etl_run.etl_run_id"), nullable=True)

    region: Mapped[Region] = relationship()
    age_group: Mapped[AgeGroupModel] = relationship()
