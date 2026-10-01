"""Glossary page: project terms and abbreviations, searchable while typing and filterable A–Z."""
import html
import re
import unicodedata
from itertools import groupby

import streamlit as st
from st_keyup import st_keyup

from dashboard.styles import hero_html
from dashboard.glossary_data import CATEGORIES, CATEGORY_DATA, CATEGORY_DOMAIN, CATEGORY_TECH, GLOSSARY, Term

ALL_LETTERS = "Alle"
IN_TERM_LABEL = "Treffer im Begriff"
IN_TEXT_LABEL = "Treffer in der Beschreibung"
DIGIT_GROUP = "0–9"

# Mid-tone accents that stay readable on both the light and the dark Streamlit theme.
CATEGORY_COLORS = {CATEGORY_DOMAIN: "#0d9488", CATEGORY_DATA: "#ea580c", CATEGORY_TECH: "#4f46e5"}
LETTER_GRADIENTS = (
    ("#6366f1", "#06b6d4"),
    ("#ec4899", "#f97316"),
    ("#10b981", "#3b82f6"),
    ("#f59e0b", "#ef4444"),
    ("#8b5cf6", "#ec4899"),
    ("#0ea5e9", "#22c55e"),
)

_CSS = """
<style>
.g-section { display: flex; align-items: center; gap: 0.75rem; margin: 1.1rem 0 0.7rem; }
.g-letter { min-width: 2.7rem; height: 2.7rem; padding: 0 0.55rem; border-radius: 12px; display: flex; align-items: center;
  justify-content: center; font-size: 1.5rem; font-weight: 800; color: #fff;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2); }
.g-wide { font-size: 0.95rem; padding: 0 1rem; }
.g-line { flex: 1; height: 3px; border-radius: 3px; opacity: 0.6; }
.g-count { font-size: 0.8rem; opacity: 0.7; white-space: nowrap; }
.g-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 0.85rem; }
.g-card { border: 1px solid rgba(128, 128, 128, 0.28); border-left: 6px solid var(--accent);
  border-radius: 12px; padding: 0.8rem 1rem 0.85rem;
  background: linear-gradient(135deg, rgba(var(--rgb), 0.10), rgba(var(--rgb), 0) 65%);
  transition: transform 0.12s ease, box-shadow 0.12s ease; }
.g-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0, 0, 0, 0.14); }
.g-term { font-size: 1.2rem; font-weight: 800; line-height: 1.25; color: var(--accent); }
.g-long { font-size: 0.92rem; opacity: 0.75; margin-top: 0.1rem; }
.g-def { margin: 0.5rem 0 0.65rem; line-height: 1.5; }
.g-pill { display: inline-block; font-size: 0.72rem; font-weight: 700; padding: 0.12rem 0.65rem;
  border-radius: 999px; color: var(--accent); background: rgba(var(--rgb), 0.14);
  border: 1px solid rgba(var(--rgb), 0.38); }
</style>
"""


def _rgb(hex_color: str) -> str:
    return ",".join(str(int(hex_color[i : i + 2], 16)) for i in (1, 3, 5))


def _category_class(category: str) -> str:
    return f"g-cat-{CATEGORIES.index(category)}" if category in CATEGORIES else "g-cat-other"


def _category_css() -> str:
    rules = [
        f".{_category_class(category)} {{ --accent: {color}; --rgb: {_rgb(color)}; }}"
        for category, color in CATEGORY_COLORS.items()
    ]
    return "\n".join([*rules, ".g-cat-other { --accent: #64748b; --rgb: 100,116,139; }"])


def _sort_key(term: Term) -> str:
    """Case-insensitive, umlaut-folded key that ignores leading punctuation (".env" sorts under E)."""
    folded = unicodedata.normalize("NFKD", term.term)
    folded = "".join(char for char in folded if not unicodedata.combining(char)).casefold()
    return re.sub(r"^[^0-9a-z]+", "", folded)


def _letter(term: Term) -> str:
    first = _sort_key(term)[:1].upper()
    return first if first.isalpha() else DIGIT_GROUP


TITLE_HIT_MAX_RANK = 3  # ranks 0-3 are hits in the term itself, rank 4 only in the description


def _rank(term: Term, query: str) -> int | None:
    """How well a term answers the query (0 = best); None if it does not match at all."""
    needle = query.casefold()
    title = term.term.casefold()
    if title == needle:
        return 0
    if title.startswith(needle):
        return 1
    if needle in title:
        return 2
    if needle in term.long_name.casefold():
        return 3
    if needle in term.definition.casefold():
        return 4
    return None


def _matches(term: Term, query: str, categories: list[str]) -> bool:
    if categories and term.category not in categories:
        return False
    return not query or _rank(term, query) is not None


def _ranked_sections(terms: list[Term], query: str) -> list[tuple[str, list[Term]]]:
    """Search hits best first: hits in the term (exact, prefix, contained, long name) before hits in the text."""
    ranked = ((_rank(term, query), _sort_key(term), term) for term in terms)
    hits = sorted(((rank, key, term) for rank, key, term in ranked if rank is not None), key=lambda item: item[:2])
    in_term = [term for rank, _, term in hits if rank <= TITLE_HIT_MAX_RANK]
    in_text = [term for rank, _, term in hits if rank > TITLE_HIT_MAX_RANK]
    sections = [(IN_TERM_LABEL, in_term), (IN_TEXT_LABEL, in_text)]
    return [(label, group) for label, group in sections if group]


def _card_html(term: Term) -> str:
    long_name = f'<div class="g-long">{html.escape(term.long_name)}</div>' if term.long_name else ""
    return (
        f'<div class="g-card {_category_class(term.category)}">'
        f'<div class="g-term">{html.escape(term.term)}</div>{long_name}'
        f'<div class="g-def">{html.escape(term.definition)}</div>'
        f'<span class="g-pill">{html.escape(term.category)}</span></div>'
    )


def _section_html(badge: str, group: list[Term]) -> str:
    """Section header (letter or search-hit label) followed by the cards of ``group``."""
    start, end = LETTER_GRADIENTS[ord(badge[0]) % len(LETTER_GRADIENTS)]
    badge_class = "g-letter g-wide" if len(badge) > 3 else "g-letter"
    label = "Begriff" if len(group) == 1 else "Begriffe"
    cards = "".join(_card_html(term) for term in group)
    # No blank lines or indentation: Markdown would otherwise end the HTML block early.
    return (
        f'<div class="g-section"><div class="{badge_class}" style="background:linear-gradient(135deg,{start},{end})">'
        f'{html.escape(badge)}</div><div class="g-line" style="background:linear-gradient(90deg,{start},transparent)">'
        f'</div><div class="g-count">{len(group)} {label}</div></div><div class="g-grid">{cards}</div>'
    )


def render() -> None:
    # The style block gets its own element: styles.py hides every element container that holds a <style> tag.
    st.markdown(_CSS.replace("</style>", _category_css() + "\n</style>"), unsafe_allow_html=True)
    st.markdown(
        hero_html("📖 Glossar", "Begriffe und Abkürzungen aus diesem Projekt – durchsuchbar und alphabetisch filterbar."),
        unsafe_allow_html=True,
    )

    terms = sorted(GLOSSARY, key=_sort_key)
    available_letters = sorted({_letter(term) for term in terms}, key=lambda letter: (letter != DIGIT_GROUP, letter))

    search_col, category_col = st.columns([2, 1])
    # st.text_input only reruns on Enter/blur; st_keyup reports every keystroke so the list filters while typing.
    with search_col:
        typed = st_keyup(
            "Suche", placeholder="z. B. UPSERT, API, Inzidenz …", debounce=150, key="glossary_search"
        )
    query = (typed or "").strip()
    categories = category_col.multiselect("Kategorie", CATEGORIES, placeholder="Alle Kategorien")
    selected_letter = st.radio(
        "Anfangsbuchstabe",
        [ALL_LETTERS, *available_letters],
        horizontal=True,
    )

    shown = [
        term
        for term in terms
        if _matches(term, query, categories) and selected_letter in (ALL_LETTERS, _letter(term))
    ]
    st.caption(f"{len(shown)} von {len(terms)} Begriffen" + (" · Treffer im Begriff zuerst" if query else ""))

    if not shown:
        st.info("Keine Begriffe gefunden. Suche oder Filter anpassen.")
        return

    if query:
        for label, group in _ranked_sections(shown, query):
            st.markdown(_section_html(label, group), unsafe_allow_html=True)
        return
    for letter, group in groupby(shown, key=_letter):
        st.markdown(_section_html(letter, list(group)), unsafe_allow_html=True)
