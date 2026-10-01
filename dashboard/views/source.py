"""RKI-Quelle: the GitHub page of the data source, shown from an offline copy (works without internet)."""
import html
import json
from datetime import datetime

import streamlit as st

from dashboard.styles import hero_html
from src.etl.source_copy import (
    DATA_FILE,
    clean_readme,
    extract_citation,
    format_size,
    load_source_copy,
    read_bytes,
    read_text,
)

README_FILE = "Readme.md"
DOCUMENTATION_FILE = "[Dokumentation]_ARE-Konsultationsinzidenz.pdf"
METADATA_FILES = (
    "datapackage.json",
    "Metadaten/schemas/tableschema_ARE-Konsultationsinzidenz.json",
    "Metadaten/zenodo.json",
    "Metadaten/zenodo-invenio.json",
    "Metadaten/nfdi4health.json",
    "Metadaten/govdata.ttl",
    "Metadaten/citation.bib",
    "Metadaten/citation.ris",
)
CODE_LANGUAGES = {".json": "json", ".ttl": "turtle", ".bib": "bibtex", ".ris": "text", ".cff": "yaml"}

_CSS = """
<style>
.q-repo { font-size: 1.35rem; margin: 0.6rem 0 0.2rem; }
.q-owner { opacity: 0.7; }
.q-name { font-weight: 800; }
.q-badge { font-size: 0.72rem; font-weight: 700; padding: 0.1rem 0.6rem; border-radius: 999px;
  border: 1px solid rgba(128, 128, 128, 0.45); margin-left: 0.5rem; vertical-align: middle; opacity: 0.8; }
.q-files { border: 1px solid rgba(128, 128, 128, 0.3); border-radius: 12px; overflow: hidden; margin: 0.5rem 0 0.8rem; }
.q-commit { display: flex; justify-content: space-between; gap: 1rem; padding: 0.55rem 0.9rem; font-size: 0.85rem;
  background: rgba(128, 128, 128, 0.1); border-bottom: 1px solid rgba(128, 128, 128, 0.3); }
.q-commit span { opacity: 0.7; white-space: nowrap; }
.q-file { display: flex; align-items: center; gap: 0.6rem; padding: 0.42rem 0.9rem; font-size: 0.9rem;
  border-bottom: 1px solid rgba(128, 128, 128, 0.18); }
.q-file:last-child { border-bottom: none; }
.q-fname { flex: 1; font-weight: 600; word-break: break-all; }
.q-fnote { font-size: 0.72rem; font-weight: 700; padding: 0.08rem 0.55rem; border-radius: 999px; white-space: nowrap; }
.q-ok { color: #16a34a; background: rgba(22, 163, 74, 0.12); }
.q-db { color: #2563eb; background: rgba(37, 99, 235, 0.12); }
.q-skip { color: #64748b; background: rgba(100, 116, 139, 0.14); }
.q-fsize { min-width: 4.5rem; text-align: right; font-size: 0.8rem; opacity: 0.65; }
.q-about { border: 1px solid rgba(128, 128, 128, 0.3); border-radius: 12px; padding: 0.8rem 1rem; }
.q-about h4 { margin: 0 0 0.4rem; font-size: 1rem; }
.q-about p { font-size: 0.85rem; line-height: 1.45; margin: 0.2rem 0 0.6rem; }
.q-fact { font-size: 0.85rem; margin: 0.25rem 0; }
.q-topics { display: flex; flex-wrap: wrap; gap: 0.3rem; margin: 0.4rem 0 0.7rem; }
.q-topic { font-size: 0.72rem; font-weight: 600; padding: 0.1rem 0.55rem; border-radius: 999px;
  color: #2563eb; background: rgba(37, 99, 235, 0.12); }
</style>
"""


def _date(iso: str) -> str:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone().strftime("%d.%m.%Y")


def _file_row(entry: dict) -> str:
    icon = "📁" if entry["type"] == "dir" else "📄"
    if entry["name"] == DATA_FILE:
        note = '<span class="q-fnote q-db">Daten in der lokalen Datenbank</span>'
    elif entry["copied"]:
        note = '<span class="q-fnote q-ok">offline verfügbar</span>'
    else:
        note = '<span class="q-fnote q-skip">nicht in der Kopie</span>'
    size = format_size(entry["size"]) if entry["size"] is not None else ""
    return (
        f'<div class="q-file"><span>{icon}</span><span class="q-fname">{html.escape(entry["name"])}</span>'
        f'{note}<span class="q-fsize">{size}</span></div>'
    )


def _files_html(manifest: dict) -> str:
    commit = manifest["latest_commit"]
    head = (
        f'<div class="q-commit"><b>{html.escape(commit["message"])}</b>'
        f'<span>{html.escape(commit["sha"])} · {_date(commit["date"])}</span></div>'
    )
    return f'<div class="q-files">{head}{"".join(_file_row(entry) for entry in manifest["entries"])}</div>'


def _about_html(manifest: dict) -> str:
    topics = "".join(f'<span class="q-topic">{html.escape(topic)}</span>' for topic in manifest["topics"])
    homepage = manifest["homepage"]
    return (
        '<div class="q-about"><h4>Über das Repository</h4>'
        f'<p>{html.escape(manifest["description"])}</p>'
        f'<div class="q-topics">{topics}</div>'
        f'<div class="q-fact">⚖️ {html.escape(manifest["license"]["name"])}</div>'
        f'<div class="q-fact">🌐 <a href="{html.escape(homepage)}" target="_blank">{html.escape(homepage)}</a></div>'
        f'<div class="q-fact">⭐ {manifest["stars"]} Sterne · 🍴 {manifest["forks"]} Forks</div>'
        f'<div class="q-fact">🗓️ erstellt {_date(manifest["created_at"])} · aktualisiert {_date(manifest["pushed_at"])}</div>'
        "</div>"
    )


def _show_file(relative_path: str) -> None:
    text = read_text(relative_path)
    extension = "." + relative_path.rsplit(".", 1)[-1]
    if extension == ".json":
        st.json(json.loads(text), expanded=1)
    else:
        st.code(text, language=CODE_LANGUAGES.get(extension, "text"))


def _readme_tab(readme: str) -> None:
    with st.container(border=True):
        st.caption("📄 README.md")
        st.markdown(clean_readme(readme))


def _license_tab() -> None:
    st.markdown("**Creative Commons Attribution 4.0 (CC BY 4.0)** – die Daten dürfen genutzt werden, wenn die Quelle genannt wird.")
    german, english = st.tabs(["Deutsch (LIZENZ)", "English (LICENSE)"])
    for tab, name in ((german, "LIZENZ"), (english, "LICENSE")):
        with tab, st.container(height=420, border=True):
            st.text(read_text(name))


def _metadata_tab() -> None:
    chosen = st.selectbox("Datei", METADATA_FILES, format_func=lambda path: path.split("/")[-1])
    _show_file(chosen)
    st.download_button("⬇️ Datei herunterladen", read_bytes(chosen), file_name=chosen.split("/")[-1], key="meta_download")


def _documentation_tab() -> None:
    data = read_bytes(DOCUMENTATION_FILE)
    st.markdown("Ausführliche **Dokumentation des Datensatzes** (PDF) vom Robert Koch-Institut.")
    st.download_button(
        f"📄 Dokumentation herunterladen ({format_size(len(data))})",
        data,
        file_name=DOCUMENTATION_FILE,
        mime="application/pdf",
        key="doc_download",
    )


def _citation_tab(readme: str) -> None:
    citation = extract_citation(readme)
    if citation:
        st.markdown("**Empfohlene Zitierweise (APA)**")
        st.markdown(citation)
    st.markdown("**citation.cff**")
    _show_file("citation.cff")


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)  # own element: styles.py hides containers that hold a <style> tag
    st.markdown(
        hero_html("📦 RKI-Quelle", "Die GitHub-Seite des Datensatzes – auch ohne Internet verfügbar."),
        unsafe_allow_html=True,
    )

    manifest = load_source_copy()
    if manifest is None:
        st.warning(
            "Die Offline-Kopie der Quellseite fehlt. Sie lässt sich mit `python -m src.cli update-source-copy` "
            "erstellen (Internetverbindung erforderlich)."
        )
        st.link_button("Original auf GitHub öffnen ↗", "https://github.com/robert-koch-institut/ARE-Konsultationsinzidenz")
        return

    owner, name = manifest["repository"].split("/")
    header, button = st.columns([4, 1.3])
    header.markdown(
        f'<div class="q-repo"><span class="q-owner">{html.escape(owner)} /</span> '
        f'<span class="q-name">{html.escape(name)}</span><span class="q-badge">Public</span></div>',
        unsafe_allow_html=True,
    )
    button.link_button("Original auf GitHub ↗", manifest["url"], use_container_width=True)
    st.info(
        f"📴 **Offline-Ansicht** – gespeicherter Stand vom **{_date(manifest['retrieved_at'])}**. "
        "Die Seite wird aus lokalen Dateien angezeigt und braucht keine Internetverbindung."
    )

    main, side = st.columns([3, 1.25])
    readme = read_text(README_FILE)
    with main:
        st.markdown(_files_html(manifest), unsafe_allow_html=True)
        readme_tab, license_tab, metadata_tab, documentation_tab, citation_tab = st.tabs(
            ["📖 README", "⚖️ Lizenz", "🧾 Metadaten", "📄 Dokumentation", "🔖 Zitieren"]
        )
        with readme_tab:
            _readme_tab(readme)
        with license_tab:
            _license_tab()
        with metadata_tab:
            _metadata_tab()
        with documentation_tab:
            _documentation_tab()
        with citation_tab:
            _citation_tab(readme)
    with side:
        st.markdown(_about_html(manifest), unsafe_allow_html=True)
