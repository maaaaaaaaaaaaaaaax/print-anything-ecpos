from printbot.formatting.raster_text import RasterBlockStyle, RasterSpan, render_spans
from printbot.formatting.text_layout import wrap_text
from printbot.formatting.text_normalization import normalize_text
from printbot.kernel import (
    CutOp,
    Document,
    FeedOp,
    PrinterProfile,
    PrintOp,
    PrintPlan,
    RasterOp,
    TextOp,
)

_NATIVE_ENCODING = "cp858"
_TRAILING_FEED_LINES = 3


def plan_text(document: Document, profile: PrinterProfile) -> PrintPlan:
    text = normalize_text(
        "\n".join("".join(run.text for run in block.runs) for block in document.blocks)
    )
    if _requires_raster(text):
        return _raster_plan(text, profile)
    return _native_plan(text, profile)


def _requires_raster(text: str) -> bool:
    try:
        text.encode(_NATIVE_ENCODING)
    except UnicodeEncodeError:
        return True
    return False


def _native_plan(text: str, profile: PrinterProfile) -> PrintPlan:
    font = profile.font_a
    text_ops = tuple(TextOp(text=line) for line in wrap_text(text, font.columns))
    ops: tuple[PrintOp, ...] = (
        *text_ops,
        FeedOp(lines=_TRAILING_FEED_LINES),
        CutOp(),
    )
    length_dots = (len(text_ops) + _TRAILING_FEED_LINES) * font.line_height_dots
    return PrintPlan(ops=ops, length_mm=length_dots / profile.dots_per_mm)


def _raster_plan(text: str, profile: PrinterProfile) -> PrintPlan:
    image = render_spans(
        [RasterSpan(text)],
        RasterBlockStyle(width=profile.print_width_dots, padding=0),
    )
    ops: tuple[PrintOp, ...] = (
        RasterOp(image=image),
        FeedOp(lines=_TRAILING_FEED_LINES),
        CutOp(),
    )
    length_dots = image.height + _TRAILING_FEED_LINES * profile.font_a.line_height_dots
    return PrintPlan(ops=ops, length_mm=length_dots / profile.dots_per_mm)
