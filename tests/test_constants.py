from enum import Enum

from src.core.constants import AgeGroup, SUPPORTED_AGE_GROUPS


def test_python_310_compatible_enum_design():
    assert issubclass(AgeGroup, str)
    assert issubclass(AgeGroup, Enum)
    assert AgeGroup.ALL.value == "00+"
    assert "60+" in SUPPORTED_AGE_GROUPS
