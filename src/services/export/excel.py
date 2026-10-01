"""Excel export: pandas writes the tables, XlsxWriter adds a native (editable) Excel line chart."""
import io

import pandas as pd
from plotly.colors import qualitative

from src.services.export.figure import MARKER_LIMIT, REFERENCE_COLOR
from src.services.export.model import ChartExport

DATA_SHEET = "Daten"
INFO_SHEET = "Info"
KEY_FIGURES_SHEET = "Kennzahlen"
MONTH_HEADER = "Monat"
HEADER_ROW = 3  # rows 0-1 hold title and subtitle
HEADER_STYLE = {"bold": True, "bg_color": "#1f3a5f", "font_color": "#ffffff", "align": "center", "border": 1}


def _number_format(values: list[float | None]) -> str:
    return "#,##0" if all(v is None or float(v).is_integer() for v in values) else "#,##0.0"


def _add_line_chart(workbook, chart: ChartExport, names: list[str], rows: int) -> object:  # noqa: ANN001
    palette = iter(qualitative.Plotly)
    line_chart = workbook.add_chart({"type": "line"})
    first_row, last_row = HEADER_ROW + 1, HEADER_ROW + rows
    for column, name in enumerate(names, start=2):  # columns A and B hold month and calendar week
        reference = name in chart.reference_series
        color = REFERENCE_COLOR if reference else next(palette)
        series = {
            "name": [DATA_SHEET, HEADER_ROW, column],
            # two columns -> Excel draws a two-level axis: calendar week with its month below
            "categories": [DATA_SHEET, first_row, 0, last_row, 1],
            "values": [DATA_SHEET, first_row, column, last_row, column],
            "line": {"color": color, "width": 2.25, "dash_type": "dash" if reference else "solid"},
        }
        if rows <= MARKER_LIMIT and not reference:
            series["marker"] = {"type": "circle", "size": 5, "border": {"color": color}, "fill": {"color": color}}
        line_chart.add_series(series)
    line_chart.set_title({"name": chart.title, "name_font": {"size": 13}})
    line_chart.set_x_axis({"name": chart.x_title})
    line_chart.set_y_axis(
        {"name": chart.y_title, "min": 0, "num_format": "#,##0",
         "major_gridlines": {"visible": True, "line": {"color": "#dddddd"}}}
    )
    line_chart.set_legend({"position": "bottom"})
    line_chart.show_blanks_as("gap")
    line_chart.set_size({"width": 900, "height": 460})
    return line_chart


def build_excel(chart: ChartExport) -> bytes:
    names = list(chart.series)
    frame = pd.DataFrame({MONTH_HEADER: chart.months, chart.x_title: chart.categories, **chart.series})

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        workbook = writer.book
        title_fmt = workbook.add_format({"bold": True, "font_size": 14})
        subtitle_fmt = workbook.add_format({"font_color": "#555555"})
        header_fmt = workbook.add_format(HEADER_STYLE)

        frame.to_excel(writer, sheet_name=DATA_SHEET, startrow=HEADER_ROW, index=False)
        sheet = writer.sheets[DATA_SHEET]
        sheet.write(0, 0, chart.title, title_fmt)
        sheet.write(1, 0, chart.subtitle, subtitle_fmt)
        for column, name in enumerate(frame.columns):
            sheet.write(HEADER_ROW, column, name, header_fmt)
        sheet.set_column(0, 0, 14)
        sheet.set_column(1, 1, max(16, len(chart.x_title) + 2))
        for column, name in enumerate(names, start=2):
            sheet.set_column(column, column, 18, workbook.add_format({"num_format": _number_format(chart.series[name])}))
        sheet.freeze_panes(HEADER_ROW + 1, 2)
        sheet.insert_chart(HEADER_ROW, len(frame.columns) + 1, _add_line_chart(workbook, chart, names, len(frame)))

        label_fmt = workbook.add_format({"bold": True, "valign": "top"})
        wrap_fmt = workbook.add_format({"text_wrap": True, "valign": "top"})
        key_figures = [(g.title, k.title, k.value, k.sub) for g in chart.kpi_groups for k in g.items]
        details = [*([("Einordnung", chart.insight)] if chart.insight else []), *chart.info,
                   *[("Hinweis", note) for note in chart.notes]]
        pd.DataFrame(details, columns=["Angabe", "Wert"]).to_excel(
            writer, sheet_name=INFO_SHEET, startrow=3, index=False
        )
        info = writer.sheets[INFO_SHEET]
        info.write(0, 0, chart.title, title_fmt)
        info.write(1, 0, chart.subtitle, subtitle_fmt)
        info.set_column(0, 0, 52, label_fmt)
        info.set_column(1, 1, 90, wrap_fmt)

        pd.DataFrame(key_figures, columns=["Bereich", "Kennzahl", "Wert", "Bezug"]).to_excel(
            writer, sheet_name=KEY_FIGURES_SHEET, startrow=3, index=False
        )
        figures = writer.sheets[KEY_FIGURES_SHEET]
        figures.write(0, 0, f"Kennzahlen – {chart.title}", title_fmt)
        figures.set_column(0, 0, 30)
        figures.set_column(1, 1, 22)
        figures.set_column(2, 2, 16)
        figures.set_column(3, 3, 40)
        if chart.summary_rows:
            first = len(key_figures) + 7
            figures.write(first - 2, 0, "Kennzahlen je Jahr", label_fmt)
            pd.DataFrame(chart.summary_rows, columns=chart.summary_header).to_excel(
                writer, sheet_name=KEY_FIGURES_SHEET, startrow=first - 1, index=False
            )
    return buffer.getvalue()
