"""Extract the official RKI TSV dataset via HTTPS."""
import hashlib
import io
import logging
from pathlib import Path

import pandas as pd
import requests

from src.core.config import settings

logger = logging.getLogger(__name__)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def parse_tsv_bytes(content: bytes) -> pd.DataFrame:
    return pd.read_csv(
        io.BytesIO(content),
        sep="\t",
        encoding="utf-8",
        na_values=["NA"],
        keep_default_na=True,
    )


def download_rki_data() -> tuple[pd.DataFrame, str]:
    logger.info("Downloading current RKI data from %s", settings.rki_data_url)
    response = requests.get(
        settings.rki_data_url,
        timeout=settings.http_timeout_seconds,
        headers={"User-Agent": "RKI-Health-Data-Monitor/1.0"},
    )
    response.raise_for_status()
    content = response.content
    return parse_tsv_bytes(content), sha256_bytes(content)


def load_local_tsv(path: Path) -> tuple[pd.DataFrame, str]:
    content = path.read_bytes()
    return parse_tsv_bytes(content), sha256_bytes(content)
