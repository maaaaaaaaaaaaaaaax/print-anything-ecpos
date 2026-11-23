import textwrap
from itertools import zip_longest

from printbot.formatting.text_normalization import normalize_text
from printbot.kernel import Alignment

_ELLIPSIS = "..."


def wrap_text(text: str, width: int) -> list[str]:
    _require_positive(width)
    lines: list[str] = []
    for paragraph in normalize_text(text).split("\n"):
        if paragraph.strip():
            lines.extend(textwrap.wrap(paragraph, width=width))
        else:
            lines.append("")
    return lines


def align_line(text: str, width: int, align: Alignment) -> str:
    padding = width - len(text)
    if padding <= 0:
        return text
    match align:
        case "left":
            return text + " " * padding
        case "right":
            return " " * padding + text
        case "center":
            left = padding // 2
            return " " * left + text + " " * (padding - left)


def rule(width: int, char: str = "-") -> str:
    _require_positive(width)
    return (char * width)[:width]


def two_columns(left: str, right: str, width: int, separator: str = " ") -> list[str]:
    _require_positive(width)
    if not right:
        return wrap_text(left, width)
    if width <= len(separator) + 1:
        raise ValueError(f"width {width} is too small for two columns")
    right_width = min(len(right), width - len(separator) - 1)
    left_width = width - len(separator) - right_width
    rows = zip_longest(
        wrap_text(left, left_width),
        wrap_text(right, right_width),
        fillvalue="",
    )
    return [
        f"{left_part.ljust(left_width)}{separator}{right_part.rjust(right_width)}"
        for left_part, right_part in rows
    ]


def table_row(
    cells: list[str],
    width: int,
    separator: str = " ",
    widths: list[int] | None = None,
) -> str:
    _require_positive(width)
    if not cells:
        return ""
    available = width - len(separator) * (len(cells) - 1)
    column_widths = widths if widths is not None else [available // len(cells)] * len(cells)
    if len(column_widths) != len(cells) or sum(column_widths) > available:
        raise ValueError("column widths do not fit the row")
    return separator.join(
        _fit_cell(cell, column_width)
        for cell, column_width in zip(cells, column_widths, strict=True)
    )


def boxed(text: str, width: int, border: str = "-", side: str = "|") -> list[str]:
    inner = width - 2 * len(side) - 2
    _require_positive(inner)
    top_and_bottom = rule(width, border)
    body = [f"{side} {line.ljust(inner)} {side}" for line in wrap_text(text, inner)]
    return [top_and_bottom, *body, top_and_bottom]


def _fit_cell(text: str, width: int) -> str:
    if len(text) <= width:
        return text.ljust(width)
    if width <= len(_ELLIPSIS):
        return text[:width]
    return text[: width - len(_ELLIPSIS)] + _ELLIPSIS


def _require_positive(width: int) -> None:
    if width <= 0:
        raise ValueError(f"width must be positive, got {width}")
