from src.services.export.emphasis import emphasize, to_reportlab


def test_weeks_years_percentages_and_levels_are_bold() -> None:
    text = (
        "Einordnung: Die aktuelle Konsultationsinzidenz (2026-W39: 1.003 je 100.000 Einwohner) liegt 41,3 % über "
        "der Vorwoche und 3,3 % über dem Vorjahr (2025-W39: 971). Im Zeitraum Ø KW36–KW39 2026 liegt das Niveau "
        "jedoch deutlich unter dem durchschnittlichen Niveau der Vergleichsjahre 2023–2025."
    )
    result = emphasize(text)
    for bold in (
        "**Einordnung:**", "**2026-W39**", "**1.003 je 100.000 Einwohner**", "**41,3 % über**", "**3,3 % über**", "**2025-W39**",
        "**KW36–KW39**", "**2026**", "**deutlich unter dem durchschnittlichen Niveau**", "**2023–2025**",
    ):
        assert bold in result, bold
    assert result.replace("**", "") == text  # only markers are added, the wording is untouched


def test_a_week_label_is_not_split_into_a_bold_year() -> None:
    assert emphasize("ab 2022-W40 (Saison 2022/23)") == "ab **2022-W40** (Saison **2022/23**)"
    assert emphasize("Ø 2023, 2025") == "Ø **2023**, **2025**"
    assert emphasize("Niveau (+1,2 %) und (-0,4 %)") == "Niveau (**+1,2 %**) und (**-0,4 %**)"
    assert emphasize("auf dem durchschnittlichen Niveau") == "**auf dem durchschnittlichen Niveau**"
    assert emphasize("deutlich steigend, weitgehend stabil") == "**deutlich steigend**, **weitgehend stabil**"


def test_the_lead_of_a_note_is_bold() -> None:
    assert emphasize("Baden-Württemberg: Das RKI") == "**Baden-Württemberg:** Das RKI"
    assert emphasize("2022: Für KW01–KW39 keine Daten").startswith("**2022:** Für **KW01–KW39**")
    assert emphasize("Kein Doppelpunkt in den ersten vierzig Zeichen dieses sehr langen Satzes: ja") == (
        "Kein Doppelpunkt in den ersten vierzig Zeichen dieses sehr langen Satzes: ja"
    )


def test_numbers_inside_other_numbers_are_left_alone() -> None:
    assert emphasize("24.348 Datensätze") == "24.348 Datensätze"
    assert emphasize("12026 und 20260") == "12026 und 20260"


def test_reportlab_markup_is_escaped_and_bold() -> None:
    assert to_reportlab("A & B in 2026-W39 <x>") == "A &amp; B in <b>2026-W39</b> &lt;x&gt;"
