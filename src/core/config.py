"""Central application configuration using pydantic-settings."""
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "RKI Health Data Monitor"
    app_author: str = ""  # optional name in the dashboard footer
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_base_url: str = "http://127.0.0.1:8000"
    database_path: str = "./data/rki_monitor.db"
    rki_data_url: str = (
        "https://raw.githubusercontent.com/robert-koch-institut/"
        "ARE-Konsultationsinzidenz/refs/heads/main/ARE-Konsultationsinzidenz.tsv"
    )
    # Offline copy of the RKI repository page (README, licence, metadata) for the "RKI-Quelle" page.
    source_copy_dir: str = "./data/quelle/ARE-Konsultationsinzidenz"
    # Hosting: the dashboard starts the API in its own process if none answers at API_BASE_URL (a local address),
    # and an empty database is filled from the RKI source on API start. Both help on hosts that run only Streamlit.
    embedded_api: bool = True
    auto_import_if_empty: bool = True
    http_timeout_seconds: int = Field(default=60, ge=5, le=300)
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_file(self) -> Path:
        path = Path(self.database_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_file.as_posix()}"


settings = Settings()
