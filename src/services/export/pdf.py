"""PDF report (A4 portrait) built with ReportLab's Platypus layout engine.

The chart is the dashboard's own Plotly figure rendered to an image, so nothing is drawn by hand.
"""
import io
import logging
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import simpleSplit
from reportlab.platypus import CondPageBreak, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.core.config import settings
from src.services.export.emphasis import to_reportlab
from src.services.export.figure import PNG_HEIGHT, PNG_WIDTH, figure_png
from src.services.export.model import ChartExport, Kpi, format_de

logger = logging.getLogger(__name__)

GRID = colors.HexColor("#dddddd")
MUTED = colors.HexColor("#555555")
HEADER_BG = colors.HexColor("#1f3a5f")
INSIGHT_BG = colors.HexColor("#eef4ff")
INSIGHT_BAR = colors.HexColor("#1f6feb")
WARNING_COLOR = colors.HexColor("#8a5a00")
ZEBRA = colors.HexColor("#f3f6fa")
FOOTER_FONT_SIZE = 7
MONTH_COLUMN_WIDTH = 62
FIRST_COLUMN_WIDTH = 70

DISCLAIMER = (
    "Fachlicher Hinweis: Die ARE-Konsultationsinzidenz beschreibt Arztkonsultationen wegen akuter "
    "respiratorischer Erkrankungen pro 100.000 Einwohner. Sie ist keine individuelle Krankheitsprognose "
    "und keine Grundlage für automatische medizinische Entscheidungen."
)


def _table_style(numeric_from: int, extra: list | None = None) -> TableStyle:
    return TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA]),
            ("ALIGN", (numeric_from, 0), (-1, -1), "RIGHT"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, GRID),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            *(extra or []),
        ]
    )


TONE_COLORS = {"up": "#dc2626", "down": "#16a34a", "flat": "#64748b"}  # an increase is the unfavourable direction


def _kpi_table(items: list[Kpi], width: float) -> Table:
    """Cards in a row: short title, big value, small line for period and unit."""
    style = ParagraphStyle("kpi", fontName="Helvetica", fontSize=8, leading=13, alignment=1)
    cells = []
    for item in items:
        color = TONE_COLORS.get(item.tone, "#000000")
        cells.append(
            Paragraph(
                f'<font size="7.5" color="#444444"><b>{escape(item.title)}</b></font><br/>'
                f'<font size="14" color="{color}"><b>{escape(item.value)}</b></font><br/>'
                f'<font size="6" color="#777777">{escape(item.sub)}</font>',
                style,
            )
        )
    table = Table([cells], colWidths=[width / len(cells)] * len(cells))
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, GRID),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, GRID),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _insight_box(text: str, width: float) -> Table:
    style = ParagraphStyle("insight", fontName="Helvetica", fontSize=9, leading=12.5)
    box = Table([[Paragraph(to_reportlab(text), style)]], colWidths=[width])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), INSIGHT_BG),
                ("LINEBEFORE", (0, 0), (0, -1), 3, INSIGHT_BAR),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return box


def _summary_table(chart: ChartExport, width: float) -> Table:
    rows = [chart.summary_header] + [
        [
            "—" if cell is None else cell if isinstance(cell, str) else format_de(cell, 0 if float(cell).is_integer() else 1)
            for cell in row
        ]
        for row in chart.summary_rows
    ]
    table = Table(rows, colWidths=[width / len(chart.summary_header)] * len(chart.summary_header))
    table.setStyle(_table_style(1))
    return table


def _data_table(chart: ChartExport, width: float) -> Table:
    names = list(chart.series)
    decimals = {
        name: 0 if all(v is None or float(v).is_integer() for v in chart.series[name]) else 1 for name in names
    }
    rows = [[chart.x_title, "Monat", *names]]
    for position, category in enumerate(chart.categories):
        rows.append(
            [category, chart.months[position], *(format_de(chart.series[n][position], decimals[n]) for n in names)]
        )
    first = FIRST_COLUMN_WIDTH + MONTH_COLUMN_WIDTH
    table = Table(
        rows,
        colWidths=[FIRST_COLUMN_WIDTH, MONTH_COLUMN_WIDTH, *[(width - first) / len(names)] * len(names)],
        repeatRows=1,
    )
    table.setStyle(_table_style(2))
    return table


def _footer(chart: ChartExport):
    def draw(canvas, doc) -> None:  # noqa: ANN001
        canvas.saveState()
        canvas.setFont("Helvetica", FOOTER_FONT_SIZE)
        canvas.setFillColor(MUTED)
        lines = simpleSplit(chart.source_note, "Helvetica", FOOTER_FONT_SIZE, doc.width - 50)
        for offset, line in enumerate(lines):
            canvas.drawString(doc.leftMargin, 14 * mm - offset * 9, line)
        canvas.drawRightString(A4[0] - doc.rightMargin, 14 * mm, f"Seite {doc.page}")
        canvas.restoreState()

    return draw


def _chart_flowable(chart: ChartExport, width: float, note_style: ParagraphStyle):
    """The dashboard chart as an image; a short note instead if the image engine is unavailable on this system."""
    try:
        return Image(io.BytesIO(figure_png(chart)), width=width, height=width * PNG_HEIGHT / PNG_WIDTH)
    except Exception:  # Kaleido needs a browser engine that some hosts do not provide
        logger.exception("Chart image could not be rendered; creating the PDF without it")
        return Paragraph(
            "Das Diagramm konnte auf diesem System nicht als Bild erzeugt werden. "
            "Kennzahlen und Datentabelle sind vollständig.",
            note_style,
        )


def build_pdf(chart: ChartExport) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=24 * mm,
        title=chart.title,
        subject=chart.subtitle,
        author=settings.app_name,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=16, alignment=0)
    subtitle = ParagraphStyle("subtitle", parent=styles["Normal"], fontSize=10, textColor=MUTED, spaceAfter=8)
    note = ParagraphStyle("note", parent=styles["Normal"], fontSize=7, leading=9, textColor=MUTED)
    group_style = ParagraphStyle("group", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7,
                                 textColor=MUTED, spaceBefore=2, spaceAfter=2)
    heading = ParagraphStyle("heading", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10)
    warning = ParagraphStyle("warning", parent=styles["Normal"], fontSize=8, leading=10.5, textColor=WARNING_COLOR,
                             leftIndent=8, firstLineIndent=-8)

    story = [
        Paragraph(escape(chart.title), title),
        Paragraph(escape(chart.subtitle), subtitle),
    ]
    if chart.insight:
        story += [_insight_box(chart.insight, doc.width), Spacer(1, 8)]
    for group in chart.kpi_groups:
        story += [Paragraph(escape(group.title.upper()), group_style), _kpi_table(group.items, doc.width), Spacer(1, 6)]
    story += [
        Spacer(1, 4),
        _chart_flowable(chart, doc.width, note),
    ]
    if chart.notes:
        story += [Paragraph("Hinweise zur Datenverfügbarkeit", heading)]
        story += [Paragraph(f"• {to_reportlab(text)}", warning) for text in chart.notes]
        story += [Spacer(1, 4)]
    story += [Paragraph(escape(DISCLAIMER), note), Spacer(1, 8)]
    if chart.summary_rows:
        story += [Paragraph("Kennzahlen je Jahr", heading), _summary_table(chart, doc.width), Spacer(1, 8)]
    story += [
        CondPageBreak(80),  # do not leave the heading alone at the bottom of a page
        Paragraph("Daten", heading),
        _data_table(chart, doc.width),
    ]
    footer = _footer(chart)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
