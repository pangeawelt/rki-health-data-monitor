"""Offline copy of the RKI GitHub repository page, shown on the "RKI-Quelle" page without internet access.

The copy holds the repository's documentation files (README, licence, metadata, documentation PDF) plus
``repository.json`` with the "About" information and the file list. The data file itself is not copied, because
the data lives in the SQLite database.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.core.config import PROJECT_ROOT, settings

REPOSITORY = "robert-koch-institut/ARE-Konsultationsinzidenz"
API_URL = f"https://api.github.com/repos/{REPOSITORY}"
RAW_URL = f"https://raw.githubusercontent.com/{REPOSITORY}/refs/heads/main/"
MANIFEST_NAME = "repository.json"
DATA_FILE = "ARE-Konsultationsinzidenz.tsv"  # listed, but not copied: the database holds the data
NOT_COPIED_FOLDERS = (".github",)  # CI configuration, irrelevant for readers
TIMEOUT_SECONDS = 60

_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_BREAK_LINE = re.compile(r"^\s*<br\s*/?>\s*$", re.MULTILINE)
_BREAK_INLINE = re.compile(r"\s*<br\s*/?>\s*")
_ENTITIES = {"&sup1;": "¹", "&emsp;": "    ", "&ensp;": "  ", "&nbsp;": " ", "&amp;": "&"}


def copy_dir() -> Path:
    path = Path(settings.source_copy_dir)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_source_copy() -> dict | None:
    """The saved repository information, or None if the copy has not been created."""
    manifest = copy_dir() / MANIFEST_NAME
    if not manifest.exists():
        return None
    return json.loads(manifest.read_text(encoding="utf-8"))


def read_text(relative_path: str) -> str:
    return (copy_dir() / relative_path).read_text(encoding="utf-8")


def read_bytes(relative_path: str) -> bytes:
    return (copy_dir() / relative_path).read_bytes()


def clean_readme(markdown: str) -> str:
    """README for display: without HTML comments (they hide the English version), <br> tags and entities."""
    text = _COMMENT.sub("", markdown.replace("\r\n", "\n"))
    text = _BREAK_LINE.sub("", text)
    text = _BREAK_INLINE.sub(" ", text)  # inside table cells
    for entity, replacement in _ENTITIES.items():
        text = text.replace(entity, replacement)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def format_size(size: int) -> str:
    """``976,9 KB`` / ``1,0 MB`` in German notation."""
    if size < 1024:
        return f"{size} B"
    value, unit = (size / 1024, "KB") if size < 1024 * 1024 else (size / 1024 / 1024, "MB")
    return f"{value:.1f} {unit}".replace(".", ",")


def _get_json(url: str):
    response = requests.get(url, timeout=TIMEOUT_SECONDS, headers={"User-Agent": "RKI-Health-Data-Monitor/1.0"})
    response.raise_for_status()
    return response.json()


def update_source_copy() -> dict:
    """Download the repository page content from GitHub (needs internet access) and save it locally."""
    repository = _get_json(API_URL)
    commit = _get_json(f"{API_URL}/commits?per_page=1")[0]
    tree = _get_json(f"{API_URL}/git/trees/{repository['default_branch']}?recursive=1")["tree"]

    target = copy_dir()
    target.mkdir(parents=True, exist_ok=True)
    entries: dict[str, dict] = {}  # what GitHub lists at the top level of the repository
    for item in tree:
        path = item["path"]
        top = path.split("/")[0]
        if top in NOT_COPIED_FOLDERS:
            entries.setdefault(top, {"name": top, "type": "dir", "size": None, "copied": False})
            continue
        if "/" in path or item["type"] == "tree":
            entries.setdefault(top, {"name": top, "type": "dir", "size": None, "copied": True})
        else:
            entries[path] = {"name": path, "type": "file", "size": item["size"], "copied": path != DATA_FILE}
        if item["type"] != "blob" or path == DATA_FILE:
            continue
        response = requests.get(RAW_URL + requests.utils.quote(path), timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        file = target / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(response.content)

    manifest = {
        "repository": repository["full_name"],
        "url": repository["html_url"],
        "description": repository["description"],
        "homepage": repository["homepage"],
        "topics": repository["topics"],
        "license": {"name": repository["license"]["name"], "spdx_id": repository["license"]["spdx_id"]},
        "default_branch": repository["default_branch"],
        "created_at": repository["created_at"],
        "pushed_at": repository["pushed_at"],
        "stars": repository["stargazers_count"],
        "forks": repository["forks_count"],
        "latest_commit": {
            "sha": commit["sha"][:7],
            "date": commit["commit"]["committer"]["date"],
            "message": commit["commit"]["message"].splitlines()[0],
        },
        "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        # folders first, like GitHub
        "entries": sorted(entries.values(), key=lambda e: (e["type"] != "dir", e["name"].casefold())),
    }
    (target / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


_CITATION = re.compile(r"<!--\s*CITATION_START[^>]*-->\s*(.*?)\s*<!--\s*CITATION_END\s*-->", re.DOTALL)


def extract_citation(markdown: str) -> str | None:
    """The ready-made citation (APA) that the RKI keeps between markers in its README."""
    match = _CITATION.search(markdown)
    return match.group(1).strip() if match else None
