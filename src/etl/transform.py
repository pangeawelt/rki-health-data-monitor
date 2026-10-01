"""Transform RKI columns into application/domain columns."""
import pandas as pd

from src.core.constants import COLUMN_MAPPING


def transform_data(df: pd.DataFrame, rejected_indices: tuple[int, ...]) -> pd.DataFrame:
    if rejected_indices:
        transformed = df.drop(index=list(rejected_indices)).copy()
    else:
        transformed = df.copy()

    transformed = transformed.rename(columns=COLUMN_MAPPING)
    transformed = transformed[list(COLUMN_MAPPING.values())]

    transformed["region_name"] = transformed["region_name"].astype(str).str.strip()
    transformed["rki_region_id"] = pd.to_numeric(transformed["rki_region_id"]).astype(int)
    transformed["age_group_code"] = transformed["age_group_code"].astype(str).str.strip()
    transformed["season"] = transformed["season"].astype(str).str.strip()
    transformed["calendar_week"] = transformed["calendar_week"].astype(str).str.strip()
    transformed["incidence_value"] = pd.to_numeric(transformed["incidence_value"], errors="coerce")

    return transformed
