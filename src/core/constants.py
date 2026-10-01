"""Domain constants for the RKI ARE dataset.

Python 3.10 compatible: deliberately uses ``Enum`` rather than ``StrEnum``.
"""
from enum import Enum


class AgeGroup(str, Enum):
    ALL = "00+"
    AGE_0_4 = "0-4"
    AGE_5_14 = "5-14"
    AGE_15_34 = "15-34"
    AGE_35_59 = "35-59"
    AGE_60_PLUS = "60+"


AGE_GROUP_DISPLAY_NAMES = {
    AgeGroup.ALL.value: "Alle Altersgruppen",
    AgeGroup.AGE_0_4.value: "0 bis 4 Jahre",
    AgeGroup.AGE_5_14.value: "5 bis 14 Jahre",
    AgeGroup.AGE_15_34.value: "15 bis 34 Jahre",
    AgeGroup.AGE_35_59.value: "35 bis 59 Jahre",
    AgeGroup.AGE_60_PLUS.value: "60 Jahre und älter",
}

SUPPORTED_AGE_GROUPS = tuple(AGE_GROUP_DISPLAY_NAMES.keys())

REQUIRED_RKI_COLUMNS = (
    "Saison",
    "Kalenderwoche",
    "Bundesland",
    "Bundesland_ID",
    "Altersgruppe",
    "ARE_Konsultationsinzidenz",
)

COLUMN_MAPPING = {
    "Saison": "season",
    "Kalenderwoche": "calendar_week",
    "Bundesland": "region_name",
    "Bundesland_ID": "rki_region_id",
    "Altersgruppe": "age_group_code",
    "ARE_Konsultationsinzidenz": "incidence_value",
}

# RKI publishes ASCII names in the dataset. UI names are independent from DB keys.
REGION_DISPLAY_NAMES = {
    "Baden-Wuerttemberg": "Baden-Württemberg",
    "Thueringen": "Thüringen",
}

SOURCE_NAME_RKI = "Robert Koch-Institut – ARE-Konsultationsinzidenz"
SOURCE_TYPE_LIVE = "RKI_LIVE"
SOURCE_TYPE_LOCAL_TEST = "LOCAL_TEST"

SOURCE_TYPE_LABELS = {
    SOURCE_TYPE_LIVE: "RKI LIVE",
    SOURCE_TYPE_LOCAL_TEST: "Testdatei",
}

LICENSE_TEXT = "CC BY 4.0"

VALID_REGION_ID_MIN = 0
VALID_REGION_ID_MAX = 16
ISO_WEEK_PATTERN = r"^\d{4}-W(?:0[1-9]|[1-4]\d|5[0-3])$"
DEFAULT_COMPARISON_YEARS = 5
MAX_COMPARISON_YEARS = 5
UPSERT_CHUNK_SIZE = 1000
