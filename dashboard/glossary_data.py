"""Static glossary content: terms and abbreviations used in this project."""
from typing import NamedTuple

CATEGORY_DOMAIN = "Fachlich (RKI-Daten)"
CATEGORY_DATA = "Daten & ETL"
CATEGORY_TECH = "Architektur & Technik"

CATEGORIES = (CATEGORY_DOMAIN, CATEGORY_DATA, CATEGORY_TECH)


class Term(NamedTuple):
    term: str
    long_name: str
    category: str
    definition: str


GLOSSARY: tuple[Term, ...] = (
    # --- Fachlich (RKI-Daten) ---
    Term(
        "4-Wochen-Mittel", "Gleitender Durchschnitt", CATEGORY_DOMAIN,
        "Durchschnitt aus der aktuellen und den drei vorherigen Wochen. Glättet kurzfristige "
        "Schwankungen im Verlaufsdiagramm.",
    ),
    Term(
        "Altersgruppe", "", CATEGORY_DOMAIN,
        "Der RKI-Datensatz unterscheidet sechs Gruppen: 00+ (alle Altersgruppen), 0-4, 5-14, 15-34, "
        "35-59 und 60+.",
    ),
    Term(
        "ARE", "Akute respiratorische Erkrankung", CATEGORY_DOMAIN,
        "Sammelbegriff für akute Atemwegsinfektionen, zum Beispiel Erkältung, Influenza oder COVID-19.",
    ),
    Term(
        "ARE-Konsultationsinzidenz", "", CATEGORY_DOMAIN,
        "Geschätzte wöchentliche Zahl der Arztkonsultationen wegen neu aufgetretener ARE pro 100.000 "
        "Einwohner der jeweiligen Altersgruppe. Keine individuelle Diagnose.",
    ),
    Term(
        "Bundesland-ID", "", CATEGORY_DOMAIN,
        "Numerischer RKI-Schlüssel der Region. 0 steht für Bundesweit, 1 bis 16 für die Bundesländer. "
        "Werte außerhalb von 0–16 werden bei der Validierung verworfen.",
    ),
    Term(
        "CC BY 4.0", "Creative Commons Namensnennung 4.0", CATEGORY_DOMAIN,
        "Lizenz der RKI-Open-Data. Die Nutzung ist erlaubt, wenn die Quelle genannt wird – deshalb "
        "steht sie im Dashboard.",
    ),
    Term(
        "Inzidenz", "", CATEGORY_DOMAIN,
        "Anzahl neuer Fälle oder Ereignisse in einem Zeitraum, bezogen auf eine Bevölkerungsgröße "
        "(hier: pro 100.000 Einwohner).",
    ),
    Term(
        "Kalenderwoche", "KW", CATEGORY_DOMAIN,
        "Woche nach ISO-8601 im Format JJJJ-Www, zum Beispiel 2025-W03. Teil des fachlichen Schlüssels.",
    ),
    Term(
        "Nachmeldung", "", CATEGORY_DOMAIN,
        "Verspätet gemeldete Daten, durch die sich bereits veröffentlichte Wochen rückwirkend ändern "
        "können. Der Grund für UPSERT statt Append.",
    ),
    Term(
        "NA", "Not Available", CATEGORY_DOMAIN,
        "Fehlender Wert im RKI-Datensatz. Ist laut RKI erlaubt und wird als leerer Wert gespeichert.",
    ),
    Term(
        "RKI", "Robert Koch-Institut", CATEGORY_DOMAIN,
        "Zentrale Einrichtung des Bundes für Krankheitsüberwachung und -prävention. Quelle der Daten.",
    ),
    Term(
        "Saison", "RKI-Saison (KW40 bis KW39)", CATEGORY_DOMAIN,
        "Spalte im RKI-Datensatz, die jede Kalenderwoche einer Saison zuordnet. Eine Saison beginnt in "
        "Kalenderwoche 40 und endet in Kalenderwoche 39 des Folgejahres, z. B. 2025/26. Deutschland gesamt "
        "liegt ab 2012/13 vor, die Bundesländer ab 2022/23.",
    ),
    Term(
        "Veränderung zur Vorwoche", "", CATEGORY_DOMAIN,
        "(aktueller Wert − Vorwochenwert) ÷ Vorwochenwert × 100, in Prozent. Wird nicht berechnet, "
        "wenn ein Wert fehlt oder die Vorwoche 0 ist.",
    ),
    Term(
        "Jahresvergleich", "", CATEGORY_DOMAIN,
        "Vergleicht dieselben Kalenderwochen mehrerer Jahre, zum Beispiel KW36 bis KW39 von 2026 mit KW36 bis "
        "KW39 von 2025, 2024 und früher. Bei „Letzte 3/5 Jahre“ werden ganze Jahre übereinandergelegt.",
    ),
    Term(
        "Zeitraum", "", CATEGORY_DOMAIN,
        "Auswahl für Verlauf und Jahresvergleich: letzte Woche, letzter Monat (4 Wochen), letzte 3 Monate "
        "(13 Wochen), dieses Jahr (ab erster Kalenderwoche bis zur neuesten Woche) sowie letzte 3 oder 5 Jahre.",
    ),
    # --- Daten & ETL ---
    Term(
        "Audit-Trail", "", CATEGORY_DATA,
        "Nachvollziehbare Protokollierung jedes Imports. Hier die Tabelle etl_run mit Status, "
        "Zeilenzählern, Hash und Fehlermeldung.",
    ),
    Term(
        "Dimensionstabelle", "", CATEGORY_DATA,
        "Tabelle mit Stammdaten, auf die die Faktentabelle verweist. Hier dim_region und dim_age_group.",
    ),
    Term(
        "ETL", "Extract, Transform, Load", CATEGORY_DATA,
        "Daten aus einer Quelle holen, prüfen und umformen und in das Zielsystem laden. In diesem "
        "Projekt: Extract → Validate → Transform → Load.",
    ),
    Term(
        "Faktentabelle", "", CATEGORY_DATA,
        "Tabelle mit den Messwerten. Hier fact_are_incidence: ein Wert je Region, Altersgruppe und "
        "Kalenderwoche.",
    ),
    Term(
        "LAG", "SQL-Fensterfunktion", CATEGORY_DATA,
        "Liefert den Wert der vorherigen Zeile. Wird für den Vorwochenvergleich verwendet.",
    ),
    Term(
        "NO_CHANGE", "ETL-Status", CATEGORY_DATA,
        "Die Quelldatei hat denselben SHA-256-Hash wie beim letzten Import. Es wird nichts neu "
        "geschrieben.",
    ),
    Term(
        "SHA-256", "Secure Hash Algorithm 256", CATEGORY_DATA,
        "Kryptografische Hashfunktion. Der Hash der Quelldatei dient als Fingerabdruck, um "
        "Änderungen zu erkennen.",
    ),
    Term(
        "TSV", "Tab-Separated Values", CATEGORY_DATA,
        "Textformat für Tabellen, bei dem Spalten durch Tabulatoren getrennt sind. Format der "
        "RKI-Quelldatei.",
    ),
    Term(
        "Unique Constraint", "Eindeutigkeitsregel", CATEGORY_DATA,
        "Datenbankregel, die eine Kombination von Spalten nur einmal zulässt. Hier: Region + "
        "Altersgruppe + Kalenderwoche.",
    ),
    Term(
        "UPSERT", "UPDATE + INSERT", CATEGORY_DATA,
        "Neue Zeilen werden eingefügt, bereits vorhandene aktualisiert. Nötig, weil das RKI frühere "
        "Wochen nachträglich ändert.",
    ),
    Term(
        "Validierung", "", CATEGORY_DATA,
        "Prüfung von Schema (Pflichtspalten) und Werten (Region, Altersgruppe, Woche, Wert ≥ 0) vor "
        "dem Laden. Ungültige Zeilen werden verworfen und gezählt.",
    ),
    Term(
        "Window Function", "Fensterfunktion", CATEGORY_DATA,
        "SQL-Funktion, die über eine Gruppe von Zeilen relativ zur aktuellen Zeile rechnet, ohne die "
        "Zeilen zusammenzufassen. Beispiele: LAG, AVG() OVER.",
    ),
    # --- Architektur & Technik ---
    Term(
        ".env", "Umgebungskonfiguration", CATEGORY_TECH,
        "Lokale Datei für umgebungsabhängige Werte wie Datenbankpfad, API-Port und RKI-URL. "
        "Vorlage: .env.example.",
    ),
    Term(
        "API", "Application Programming Interface", CATEGORY_TECH,
        "Schnittstelle, über die Programme miteinander sprechen. Das Dashboard holt alle Daten über "
        "die lokale API.",
    ),
    Term(
        "CLI", "Command Line Interface", CATEGORY_TECH,
        "Bedienung über die Kommandozeile: python -m src.cli mit init-db, refresh, status und reset-db.",
    ),
    Term(
        "Dashboard", "", CATEGORY_TECH,
        "Grafische Oberfläche mit Filtern, Kennzahlen und Diagramm. Hier umgesetzt mit Streamlit.",
    ),
    Term(
        "FastAPI", "", CATEGORY_TECH,
        "Python-Framework für REST-APIs mit automatischer OpenAPI-Dokumentation unter /docs.",
    ),
    Term(
        "HTTP / HTTPS", "Hypertext Transfer Protocol (Secure)", CATEGORY_TECH,
        "Protokoll für die Kommunikation im Web. Der RKI-Download läuft über HTTPS, Dashboard und API "
        "sprechen über HTTP.",
    ),
    Term(
        "KPI", "Key Performance Indicator", CATEGORY_TECH,
        "Kennzahl. Im Dashboard: aktuelle Konsultationsinzidenz, Vorwoche und Veränderung in Prozent.",
    ),
    Term(
        "MVP", "Minimum Viable Product", CATEGORY_TECH,
        "Kleinste sinnvolle Ausbaustufe. Der Projektumfang ist bewusst auf einen MVP begrenzt.",
    ),
    Term(
        "OpenAPI / Swagger", "", CATEGORY_TECH,
        "Standard zur Beschreibung von REST-APIs. Swagger UI ist die interaktive Dokumentation unter "
        "http://127.0.0.1:8000/docs.",
    ),
    Term(
        "ORM", "Object-Relational Mapping", CATEGORY_TECH,
        "Abbildung von Datenbanktabellen auf Python-Klassen. Hier mit SQLAlchemy (src/db/models.py).",
    ),
    Term(
        "pandas", "", CATEGORY_TECH,
        "Python-Bibliothek für tabellarische Daten. Wird im ETL zum Einlesen, Prüfen und Umformen "
        "verwendet.",
    ),
    Term(
        "PoC", "Proof of Concept", CATEGORY_TECH,
        "Machbarkeitsnachweis. Zeigt, dass der Datenfluss vom Import bis zum Dashboard funktioniert.",
    ),
    Term(
        "Pydantic", "", CATEGORY_TECH,
        "Bibliothek zur Datenvalidierung mit Typen. Definiert die API-Antworten; pydantic-settings "
        "liest die Konfiguration.",
    ),
    Term(
        "pytest", "", CATEGORY_TECH,
        "Test-Framework für Python. Die Tests liegen im Ordner tests/.",
    ),
    Term(
        "REST", "Representational State Transfer", CATEGORY_TECH,
        "Architekturstil für Web-APIs: Ressourcen werden über URLs und HTTP-Methoden wie GET und POST "
        "angesprochen.",
    ),
    Term(
        "SQL", "Structured Query Language", CATEGORY_TECH,
        "Sprache zum Abfragen und Verändern relationaler Datenbanken. Die Auswertungen stehen "
        "bewusst als explizites SQL im Code.",
    ),
    Term(
        "SQLAlchemy", "", CATEGORY_TECH,
        "Python-Bibliothek für den Datenbankzugriff (ORM und SQL). Erleichtert einen späteren Wechsel "
        "auf PostgreSQL.",
    ),
    Term(
        "SQLite", "", CATEGORY_TECH,
        "Dateibasierte Datenbank ohne eigenen Server. Die lokale Datenbank liegt unter "
        "data/rki_monitor.db.",
    ),
    Term(
        "Streamlit", "", CATEGORY_TECH,
        "Python-Framework für Datenanwendungen im Browser. Dieses Dashboard ist damit gebaut.",
    ),
    Term(
        "Uvicorn", "", CATEGORY_TECH,
        "ASGI-Webserver, der die FastAPI-Anwendung ausführt.",
    ),
    Term(
        "WAL", "Write-Ahead Logging", CATEGORY_TECH,
        "Journal-Modus von SQLite, bei dem Lesen und Schreiben sich weniger blockieren. Hier per "
        "PRAGMA aktiviert.",
    ),
)
