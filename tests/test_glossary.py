from dashboard.glossary_data import CATEGORIES, GLOSSARY, Term
from dashboard.views.glossary import (
    DIGIT_GROUP,
    IN_TERM_LABEL,
    IN_TEXT_LABEL,
    _letter,
    _matches,
    _rank,
    _ranked_sections,
    _sort_key,
)


def test_glossary_terms_are_unique_and_complete() -> None:
    names = [term.term.casefold() for term in GLOSSARY]
    assert len(names) == len(set(names))
    assert all(term.definition.strip() for term in GLOSSARY)
    assert all(term.category in CATEGORIES for term in GLOSSARY)


def test_letter_grouping_ignores_case_punctuation_and_digits() -> None:
    assert _letter(Term("pandas", "", CATEGORIES[2], "x")) == "P"
    assert _letter(Term(".env", "", CATEGORIES[2], "x")) == "E"
    assert _letter(Term("4-Wochen-Mittel", "", CATEGORIES[0], "x")) == DIGIT_GROUP


def test_sorting_is_case_insensitive() -> None:
    ordered = [term.term for term in sorted(GLOSSARY, key=_sort_key) if term.term.startswith(("U", "u"))]
    assert ordered == ["Unique Constraint", "UPSERT", "Uvicorn"]


def test_search_matches_term_name_and_definition_and_category_filter() -> None:
    upsert = next(term for term in GLOSSARY if term.term == "UPSERT")
    assert _matches(upsert, "upsert", [])
    assert _matches(upsert, "nachträglich", [])
    assert not _matches(upsert, "streamlit", [])
    assert not _matches(upsert, "", [CATEGORIES[2]])


def test_rank_prefers_the_term_over_its_description() -> None:
    by_name = {term.term: term for term in GLOSSARY}
    assert _rank(by_name["RKI"], "rki") == 0  # exact term
    assert _rank(by_name["UPSERT"], "ups") == 1  # term starts with the query
    assert _rank(by_name["4-Wochen-Mittel"], "mittel") == 2  # term contains the query
    assert _rank(by_name["Saison"], "kw40") == 3  # only the long name
    assert _rank(by_name["UPSERT"], "nachträglich") == 4  # only the description
    assert _rank(by_name["UPSERT"], "streamlit") is None


def test_search_shows_hits_in_the_term_before_hits_in_the_description() -> None:
    sections = _ranked_sections(list(GLOSSARY), "rki")
    assert [label for label, _ in sections] == [IN_TERM_LABEL, IN_TEXT_LABEL]
    in_term, in_text = (group for _, group in sections)
    assert in_term[0].term == "RKI"  # at the very top, no matter that it sorts under "R"
    assert all("rki" not in term.term.casefold() for term in in_text)
    assert sum(len(group) for group in (in_term, in_text)) == len([t for t in GLOSSARY if _matches(t, "rki", [])])
    assert _ranked_sections(list(GLOSSARY), "gibt-es-nicht") == []
