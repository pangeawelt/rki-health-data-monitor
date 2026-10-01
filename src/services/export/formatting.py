"""German number formatting shared by the export model and the interpretation texts."""


def format_de(value: float | None, decimals: int = 0, signed: bool = False) -> str:
    """German number format (1.234,5); ``—`` for missing values."""
    if value is None:
        return "—"
    text = f"{value:{'+' if signed else ''},.{decimals}f}"
    return text.replace(",", "\0").replace(".", ",").replace("\0", ".")


def format_value(value: float | None) -> str:
    """Whole numbers without decimals, everything else with one decimal."""
    return format_de(value, 0 if value is None or float(value).is_integer() else 1)


def format_percent(value: float | None) -> str:
    return "—" if value is None else f"{format_de(value, 1, signed=True)} %"
