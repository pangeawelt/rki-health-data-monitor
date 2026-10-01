from pathlib import Path

from src.etl.extract import load_local_tsv
from src.etl.transform import transform_data
from src.etl.validate import validate_data

FIXTURE = Path(__file__).parent / "fixtures" / "rki_sample.tsv"


def test_transform_maps_columns():
    df, _ = load_local_tsv(FIXTURE)
    validation = validate_data(df)
    result = transform_data(df, validation.rejected_indices)
    assert "region_name" in result.columns
    assert "age_group_code" in result.columns
    assert "incidence_value" in result.columns
    assert result.iloc[0]["region_name"] == "Baden-Wuerttemberg"
