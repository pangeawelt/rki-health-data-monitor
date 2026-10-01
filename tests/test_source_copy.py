from src.core.config import settings
from src.etl import source_copy
from src.etl.source_copy import (
    DATA_FILE,
    clean_readme,
    copy_dir,
    extract_citation,
    format_size,
    load_source_copy,
    read_text,
    update_source_copy,
)


def test_bundled_copy_has_the_pages_content() -> None:
    manifest = load_source_copy()
    assert manifest is not None
    assert manifest["repository"] == "robert-koch-institut/ARE-Konsultationsinzidenz"
    assert manifest["license"]["spdx_id"] == "CC-BY-4.0"
    assert manifest["latest_commit"]["sha"] and manifest["topics"]
    for name in ("Readme.md", "LICENSE", "LIZENZ", "citation.cff", "datapackage.json"):
        assert (copy_dir() / name).is_file(), name
    assert "Creative Commons" in read_text("LICENSE")


def test_manifest_lists_the_repository_like_github() -> None:
    entries = load_source_copy()["entries"]
    assert [e["type"] for e in entries] == sorted((e["type"] for e in entries), key=lambda t: t != "dir")  # folders first
    by_name = {e["name"]: e for e in entries}
    assert by_name[DATA_FILE]["copied"] is False  # the data lives in the database
    assert not (copy_dir() / DATA_FILE).exists()
    assert by_name[".github"]["copied"] is False and not (copy_dir() / ".github").exists()
    for entry in entries:
        if entry["type"] == "file" and entry["copied"]:
            assert (copy_dir() / entry["name"]).stat().st_size == entry["size"], entry["name"]


def test_readme_is_cleaned_for_display() -> None:
    raw = read_text("Readme.md")
    cleaned = clean_readme(raw)
    assert "<!--" not in cleaned and "&sup1;" not in cleaned and "<br>" not in cleaned
    assert "# ARE-Konsultationsinzidenz" in cleaned
    assert "Hinweise zur Nachnutzung" in cleaned


def test_clean_readme_handles_comments_breaks_and_entities() -> None:
    text = "# Titel\n\n<br>\n\nA&sup1; &amp; B\n\n\n\n<!-- verborgen\nmehrzeilig -->\nEnde"
    assert clean_readme(text) == "# Titel\n\nA¹ & B\n\nEnde\n"


def test_ready_made_citation_is_extracted() -> None:
    citation = extract_citation(read_text("Readme.md"))
    assert citation and "doi.org" in citation and "ARE-Konsultationsinzidenz" in citation
    assert extract_citation("kein Marker") is None


def test_size_in_german_notation() -> None:
    assert format_size(775) == "775 B"
    assert format_size(93924) == "91,7 KB"
    assert format_size(1000524) == "977,1 KB"
    assert format_size(5 * 1024 * 1024) == "5,0 MB"


def test_update_copies_the_documentation_but_not_the_data_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "source_copy_dir", str(tmp_path))
    repository = {
        "full_name": "owner/repo", "html_url": "https://github.com/owner/repo", "description": "Beschreibung",
        "homepage": "https://example.org", "topics": ["rki"], "license": {"name": "CC BY 4.0", "spdx_id": "CC-BY-4.0"},
        "default_branch": "main", "created_at": "2023-01-01T00:00:00Z", "pushed_at": "2026-01-01T00:00:00Z",
        "stargazers_count": 3, "forks_count": 1,
    }
    commit = {"sha": "abcdef1234", "commit": {"committer": {"date": "2026-01-01T00:00:00Z"}, "message": "Update\n\nbody"}}
    tree = [
        {"path": ".github", "type": "tree"},
        {"path": ".github/workflows/ci.yml", "type": "blob", "size": 4},
        {"path": "Metadaten", "type": "tree"},
        {"path": "Metadaten/zenodo.json", "type": "blob", "size": 2},
        {"path": "Readme.md", "type": "blob", "size": 3},
        {"path": DATA_FILE, "type": "blob", "size": 1000},
    ]

    def fake_json(url: str):
        if "commits" in url:
            return [commit]
        return {"tree": tree} if "/git/trees/" in url else repository

    class Response:
        content = b"abc"

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(source_copy, "_get_json", fake_json)
    monkeypatch.setattr(source_copy.requests, "get", lambda url, **kwargs: Response())

    manifest = update_source_copy()

    assert [(e["name"], e["type"], e["copied"]) for e in manifest["entries"]] == [
        (".github", "dir", False), ("Metadaten", "dir", True), (DATA_FILE, "file", False), ("Readme.md", "file", True),
    ]
    assert manifest["latest_commit"] == {"sha": "abcdef1", "date": "2026-01-01T00:00:00Z", "message": "Update"}
    assert (tmp_path / "Readme.md").read_bytes() == b"abc"
    assert (tmp_path / "Metadaten" / "zenodo.json").exists()
    assert not (tmp_path / ".github").exists() and not (tmp_path / DATA_FILE).exists()
    assert load_source_copy()["repository"] == "owner/repo"
