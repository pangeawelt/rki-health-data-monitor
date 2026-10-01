"""HTTP helpers for the local FastAPI backend."""
import re

import requests

from src.core.config import settings

API_BASE_URL = settings.api_base_url.rstrip("/")
REQUEST_TIMEOUT = 10
REFRESH_TIMEOUT = 120
EXPORT_TIMEOUT = 60


def api_get(path: str, params: dict | None = None):
    response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def api_get_file(path: str, params: dict | None = None) -> tuple[bytes, str]:
    """Download a generated file (PDF/Excel export) and return its bytes and file name."""
    response = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=EXPORT_TIMEOUT)
    response.raise_for_status()
    match = re.search(r'filename="([^"]+)"', response.headers.get("content-disposition", ""))
    return response.content, match.group(1) if match else "export"


def api_post(path: str, params: dict | None = None):
    response = requests.post(f"{API_BASE_URL}{path}", params=params, timeout=REFRESH_TIMEOUT)
    response.raise_for_status()
    return response.json()


def api_is_available() -> bool:
    try:
        api_get("/health")
        return True
    except requests.RequestException:
        return False
