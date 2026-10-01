"""Vectorized validation for the RKI ARE dataset."""
import re
from dataclasses import dataclass

import pandas as pd

from src.core.constants import (
    ISO_WEEK_PATTERN,
    REQUIRED_RKI_COLUMNS,
    SUPPORTED_AGE_GROUPS,
    VALID_REGION_ID_MAX,
    VALID_REGION_ID_MIN,
)


@dataclass(frozen=True)
class ValidationSummary:
    valid_rows: int
    rejected_rows: int
    rejected_indices: tuple[int, ...]


def validate_schema(df: pd.DataFrame) -> None:
    missing = set(REQUIRED_RKI_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"RKI schema changed. Missing columns: {sorted(missing)}")


def validate_data(df: pd.DataFrame) -> ValidationSummary:
    validate_schema(df)

    region_ids = pd.to_numeric(df["Bundesland_ID"], errors="coerce")
    incidence = pd.to_numeric(df["ARE_Konsultationsinzidenz"], errors="coerce")
    weeks = df["Kalenderwoche"].astype("string")
    age_groups = df["Altersgruppe"].astype("string")
    region_names = df["Bundesland"].astype("string")

    invalid_region = region_ids.isna() | ~region_ids.between(VALID_REGION_ID_MIN, VALID_REGION_ID_MAX)
    invalid_age = age_groups.isna() | ~age_groups.isin(SUPPORTED_AGE_GROUPS)
    invalid_week = weeks.isna() | ~weeks.str.match(ISO_WEEK_PATTERN, na=False)
    invalid_region_name = region_names.isna() | (region_names.str.strip() == "")
    # RKI officially allows missing incidence values (NA); only negative/non-numeric non-null values are invalid.
    raw_incidence = df["ARE_Konsultationsinzidenz"]
    invalid_incidence = (raw_incidence.notna() & incidence.isna()) | (incidence.notna() & (incidence < 0))

    invalid_mask = invalid_region | invalid_age | invalid_week | invalid_region_name | invalid_incidence
    rejected_indices = tuple(df.index[invalid_mask].tolist())

    return ValidationSummary(
        valid_rows=int((~invalid_mask).sum()),
        rejected_rows=int(invalid_mask.sum()),
        rejected_indices=rejected_indices,
    )
