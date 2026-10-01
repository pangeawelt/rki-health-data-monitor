from pathlib import Path

from src.etl.extract import load_local_tsv
from src.etl.validate import validate_data, validate_schema

FIXTURE = Path(__file__).parent / "fixtures" / "rki_sample.tsv"


def test_fixture_schema_and_data_are_valid():
    df, _ = load_local_tsv(FIXTURE)
    validate_schema(df)
    result = validate_data(df)
    assert result.valid_rows == 6
    assert result.rejected_rows == 0


def test_missing_column_is_rejected():
    df, _ = load_local_tsv(FIXTURE)
    df = df.drop(columns=["Bundesland"])
    try:
        validate_schema(df)
    except ValueError as exc:
        assert "Bundesland" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
