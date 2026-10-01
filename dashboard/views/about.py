"""Project page: what the project does, how the data flows, what it offers, the source, technology and privacy."""
import html

import streamlit as st

from dashboard.styles import hero_html

STEPS = (
    ("RKI Open Data", "Wöchentliche Zahlen des Robert Koch-Instituts (TSV-Datei)."),
    ("Import", "Laden, prüfen und umwandeln. Nachmeldungen aktualisieren bestehende Wochen."),
    ("Datenbank", "SQLite speichert alles lokal – ohne eigenen Datenbankserver."),
    ("Schnittstelle", "FastAPI liefert Auswertungen sowie PDF- und Excel-Berichte."),
    ("Dashboard", "Streamlit zeigt Diagramme und Kennzahlen – und spricht nur mit der API."),
)

FEATURES = (
    ("📈", "Zeitlicher Verlauf", "Entwicklung der Konsultationsinzidenz – von der letzten Woche bis zu 5 Jahren."),
    ("📅", "Jahresvergleich", "Dieselben Kalenderwochen mehrerer Jahre übereinander, mit Durchschnitt der Vergleichsjahre."),
    ("🧭", "Einordnung", "Kurzfassung in einer Zeile und Erklärung in Worten: über oder unter Vorwoche, Vorjahr und Durchschnitt."),
    ("📄", "PDF und Excel", "Jedes Diagramm mit Kennzahlen und Datentabelle zum Herunterladen."),
    ("⚠️", "Datenverfügbarkeit", "Hinweise, ab wann das RKI Daten je Bundesland veröffentlicht (Bundesländer ab 2022)."),
    ("📖", "Glossar", "Begriffe und Abkürzungen mit Live-Suche – Treffer im Begriff zuerst."),
)

TECH = (
    ("Daten", ("requests", "pandas", "SQLite", "SQLAlchemy")),
    ("Schnittstelle", ("FastAPI", "Pydantic", "Uvicorn")),
    ("Oberfläche", ("Streamlit", "Plotly", "streamlit-keyup")),
    ("Berichte", ("ReportLab", "XlsxWriter", "Kaleido")),
    ("Qualität", ("pytest", "Typer", "openpyxl")),
)

_CSS = """
<style>
.p-c0 { --accent: #4f46e5; --rgb: 79, 70, 229; }
.p-c1 { --accent: #0ea5e9; --rgb: 14, 165, 233; }
.p-c2 { --accent: #14b8a6; --rgb: 20, 184, 166; }
.p-c3 { --accent: #f59e0b; --rgb: 245, 158, 11; }
.p-c4 { --accent: #ec4899; --rgb: 236, 72, 153; }
.p-c5 { --accent: #16a34a; --rgb: 22, 163, 74; }
.p-title { display: flex; align-items: center; gap: 0.6rem; font-size: 1.2rem; font-weight: 800; margin: 1.4rem 0 0.6rem; }
.p-title::after { content: ""; flex: 1; height: 3px; border-radius: 3px; background: linear-gradient(90deg, rgba(99, 102, 241, 0.55), transparent); }
.p-intro { border: 1px solid rgba(128, 128, 128, 0.28); border-left: 6px solid #4f46e5; border-radius: 14px; padding: 0.9rem 1.1rem;
  line-height: 1.55; background: linear-gradient(135deg, rgba(79, 70, 229, 0.08), rgba(79, 70, 229, 0) 70%); }
.p-flow { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0.8rem; }
.p-step { position: relative; border: 1px solid rgba(128, 128, 128, 0.28); border-top: 4px solid var(--accent); border-radius: 14px;
  padding: 0.7rem 0.9rem 0.8rem; background: linear-gradient(135deg, rgba(var(--rgb), 0.1), rgba(var(--rgb), 0) 70%); }
.p-badge { width: 1.75rem; height: 1.75rem; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-weight: 800; color: #fff; background: var(--accent); margin-bottom: 0.4rem; }
.p-step-title { font-weight: 800; }
.p-step-text { font-size: 0.85rem; opacity: 0.8; line-height: 1.4; margin-top: 0.15rem; }
.p-features { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0.8rem; }
.p-feature { border: 1px solid rgba(128, 128, 128, 0.28); border-radius: 14px; padding: 0.75rem 1rem; background: rgba(128, 128, 128, 0.05); }
.p-icon { font-size: 1.6rem; line-height: 1.2; }
.p-feature-title { font-weight: 800; margin: 0.1rem 0 0.15rem; }
.p-feature-text { font-size: 0.88rem; opacity: 0.85; line-height: 1.45; }
.p-tech { display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; margin: 0.4rem 0; }
.p-tech-label { min-width: 8rem; font-weight: 700; font-size: 0.85rem; opacity: 0.8; }
.p-chip { font-size: 0.8rem; font-weight: 600; padding: 0.15rem 0.7rem; border-radius: 999px; color: var(--accent);
  background: rgba(var(--rgb), 0.12); border: 1px solid rgba(var(--rgb), 0.4); }
.p-privacy { border: 1px solid rgba(22, 163, 74, 0.4); border-left: 6px solid #16a34a; border-radius: 14px; padding: 0.8rem 1.1rem;
  line-height: 1.5; background: rgba(22, 163, 74, 0.08); }
</style>
"""


def _title(text: str) -> str:
    return f'<div class="p-title">{html.escape(text)}</div>'


def _steps_html() -> str:
    cards = "".join(
        f'<div class="p-step p-c{index % 6}"><div class="p-badge">{index + 1}</div>'
        f'<div class="p-step-title">{html.escape(title)}</div><div class="p-step-text">{html.escape(text)}</div></div>'
        for index, (title, text) in enumerate(STEPS)
    )
    return f'<div class="p-flow">{cards}</div>'


def _features_html() -> str:
    cards = "".join(
        f'<div class="p-feature"><div class="p-icon">{icon}</div><div class="p-feature-title">{html.escape(title)}</div>'
        f'<div class="p-feature-text">{html.escape(text)}</div></div>'
        for icon, title, text in FEATURES
    )
    return f'<div class="p-features">{cards}</div>'


def _tech_html() -> str:
    rows = "".join(
        f'<div class="p-tech p-c{index % 6}"><span class="p-tech-label">{html.escape(label)}</span>'
        + "".join(f'<span class="p-chip">{html.escape(name)}</span>' for name in names)
        + "</div>"
        for index, (label, names) in enumerate(TECH)
    )
    return rows


def render(source_page: st.Page) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)  # own element: styles.py hides containers that hold a <style> tag
    st.markdown(
        hero_html(
            "ℹ️ Über das Projekt",
            "Wöchentliche Atemwegs-Daten des Robert Koch-Instituts – geladen, geprüft und übersichtlich ausgewertet.",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(_title("Worum geht es?"), unsafe_allow_html=True)
    st.markdown(
        '<div class="p-intro">Das Dashboard zeigt, wie viele Menschen in Deutschland wegen <b>akuter Atemwegserkrankungen</b> '
        "(ARE) – etwa Erkältung, Grippe oder COVID-19 – eine Arztpraxis aufsuchen. Die Zahlen stammen vom "
        "<b>Robert Koch-Institut</b>, gelten je Bundesland und Altersgruppe und werden als <b>Konsultationsinzidenz "
        "pro 100.000 Einwohner</b> angegeben.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(_title("So kommen die Daten ins Dashboard"), unsafe_allow_html=True)
    st.markdown(_steps_html(), unsafe_allow_html=True)

    st.markdown(_title("Was Sie tun können"), unsafe_allow_html=True)
    st.markdown(_features_html(), unsafe_allow_html=True)

    st.markdown(_title("Datenquelle"), unsafe_allow_html=True)
    with st.container(border=True):
        link, text = st.columns([2, 5])
        link.page_link(source_page, label="ARE-Konsultationsinzidenz", icon="📦")
        text.markdown("Robert Koch-Institut – wöchentlich, je Bundesland und Altersgruppe. Lizenz: **CC BY 4.0**.")
        st.caption(
            "Ein Klick auf den Namen öffnet die Seite des Datensatzes (README, Lizenz, Metadaten, Dokumentation) – "
            "auch ohne Internet. Deutschland gesamt liegt ab 2012 vor, die Bundesländer ab 2022."
        )

    st.markdown(_title("Technik"), unsafe_allow_html=True)
    st.markdown(_tech_html(), unsafe_allow_html=True)

    st.markdown(_title("Datenschutz"), unsafe_allow_html=True)
    st.markdown(
        '<div class="p-privacy">🛡️ Es werden ausschließlich <b>veröffentlichte, aggregierte RKI-Daten</b> verarbeitet. '
        "Keine personenbezogenen Gesundheitsdaten und keine medizinischen Entscheidungen – die Zahlen sind keine "
        "individuelle Krankheitsprognose.</div>",
        unsafe_allow_html=True,
    )
