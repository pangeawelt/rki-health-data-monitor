"""Bold markup for the key facts inside generated sentences: years, weeks, percentages and levels.

The texts themselves stay plain (API, Excel); dashboard and PDF apply this at render time.
"""
import re
from xml.sax.saxutils import escape

NUMBER = r"\d[\d.]*(?:,\d+)?"
YEAR = r"(?:19|20)\d{2}"

# Alternatives are tried left to right at every position, so longer forms (2026-W39) win over a bare year.
_PATTERNS = (
    r"^[^:\n]{1,40}:",  # the lead of a sentence: "Einordnung:", "Baden-Württemberg:", "2022:"
    r"\d{4}-W\d{2}",  # 2026-W39
    r"\d{4}/\d{2}",  # season 2022/23
    r"KW\d{2}(?:–KW\d{2})?(?: \(Jahreswechsel\))?",  # KW36–KW39
    rf"(?<![\d.-]){YEAR}(?:–{YEAR})?(?![\d/-])",  # 2026, 2022–2025
    rf"{NUMBER} % (?:über|unter)",  # 41,3 % über
    rf"[+-]{NUMBER} %",  # (+0,5 %)
    rf"{NUMBER} je 100\.000 Einwohner",
    r"(?:deutlich|leicht) (?:über|unter) dem durchschnittlichen Niveau",
    r"auf dem durchschnittlichen Niveau",
    r"(?:deutlich )?(?:steigend|fallend)|weitgehend stabil",
)
_EMPHASIS = re.compile("|".join(f"(?:{pattern})" for pattern in _PATTERNS))
_BOLD = re.compile(r"\*\*(.+?)\*\*")


def emphasize(text: str) -> str:
    """Markdown with the key facts of ``text`` in bold."""
    return _EMPHASIS.sub(lambda match: f"**{match.group(0)}**", text)


def to_reportlab(text: str) -> str:
    """ReportLab paragraph markup (``<b>``) for ``text`` with its key facts in bold."""
    return _BOLD.sub(r"<b>\1</b>", escape(emphasize(text)))
