import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Final

from PIL import Image, ImageDraw, ImageFont

from printbot.formatting.font_catalog import FontFamily, load_font, variant_for
from printbot.formatting.text_normalization import normalize_text
from printbot.kernel import Alignment

_TOKEN_SPLITTER: Final = re.compile(r"(\n|\s+)")
_INK: Final = 0
_PAPER: Final = 255
_UNDERLINE_OFFSET: Final = 2
_MIN_FONT_SIZE: Final = 6


@dataclass(frozen=True, slots=True)
class RasterSpan:
    text: str
    family: FontFamily = "sans"
    size: int = 28
    bold: bool = False
    italic: bool = False
    underline: bool = False
    invert: bool = False

    def __post_init__(self) -> None:
        if self.size < _MIN_FONT_SIZE:
            raise ValueError(f"font size must be at least {_MIN_FONT_SIZE}, got {self.size}")

    def font(self) -> ImageFont.FreeTypeFont:
        return load_font(self.family, variant_for(bold=self.bold, italic=self.italic), self.size)


@dataclass(frozen=True, slots=True)
class RasterBlockStyle:
    width: int
    align: Alignment = "left"
    line_spacing: float = 1.2
    padding: int = 8

    def __post_init__(self) -> None:
        if self.padding < 0 or self.width <= 2 * self.padding:
            raise ValueError("width must be larger than twice the padding")
        if self.line_spacing <= 0:
            raise ValueError("line spacing must be positive")

    @property
    def content_width(self) -> int:
        return self.width - 2 * self.padding


@dataclass(slots=True)
class _Run:
    text: str
    span: RasterSpan
    font: ImageFont.FreeTypeFont
    width: float


@dataclass(slots=True)
class _Line:
    runs: list[_Run] = field(default_factory=list)
    ascent: int = 0
    descent: int = 0
    width: float = 0.0

    @property
    def height(self) -> int:
        return self.ascent + self.descent

    def reserve(self, font: ImageFont.FreeTypeFont) -> None:
        ascent, descent = font.getmetrics()
        self.ascent = max(self.ascent, ascent)
        self.descent = max(self.descent, descent)

    def add(self, run: _Run) -> None:
        self.runs.append(run)
        self.width += run.width
        self.reserve(run.font)


def render_spans(spans: Sequence[RasterSpan], style: RasterBlockStyle) -> Image.Image:
    lines = _layout(spans, style.content_width)
    tops = _line_tops(lines, style)
    bottom = tops[-1] + lines[-1].height if lines else style.padding
    image = Image.new("L", (style.width, max(1, bottom + style.padding)), _PAPER)
    draw = ImageDraw.Draw(image)
    for line, top in zip(lines, tops, strict=True):
        x = _start_x(style, line.width)
        for run in line.runs:
            _draw_run(draw, run, x=x, top=top, line=line)
            x += run.width
    return image


def _line_tops(lines: Sequence[_Line], style: RasterBlockStyle) -> list[int]:
    tops: list[int] = []
    y = style.padding
    for line in lines:
        tops.append(y)
        y += round(line.height * style.line_spacing)
    return tops


def _layout(spans: Sequence[RasterSpan], content_width: float) -> list[_Line]:
    lines = [_Line()]
    for span in spans:
        font = span.font()
        for token in _tokenize(normalize_text(span.text)):
            if token == "\n":
                lines[-1].reserve(font)
                lines.append(_Line())
            else:
                _place(lines, token, span, font, content_width)
    if not lines[-1].runs and lines[-1].height == 0:
        lines.pop()
    return lines


def _tokenize(text: str) -> list[str]:
    return [part for part in _TOKEN_SPLITTER.split(text) if part]


def _place(
    lines: list[_Line],
    token: str,
    span: RasterSpan,
    font: ImageFont.FreeTypeFont,
    content_width: float,
) -> None:
    line = lines[-1]
    if token.isspace() and not line.runs:
        return
    width = font.getlength(token)
    if line.width + width <= content_width:
        line.add(_Run(token, span, font, width))
        return
    if token.isspace():
        return
    if line.runs:
        line = _Line()
        lines.append(line)
    for chunk in _split_to_fit(token, font, content_width):
        chunk_width = font.getlength(chunk)
        if line.runs and line.width + chunk_width > content_width:
            line = _Line()
            lines.append(line)
        line.add(_Run(chunk, span, font, chunk_width))


def _split_to_fit(token: str, font: ImageFont.FreeTypeFont, max_width: float) -> list[str]:
    chunks: list[str] = []
    current = ""
    for char in token:
        if current and font.getlength(current + char) > max_width:
            chunks.append(current)
            current = char
        else:
            current += char
    if current:
        chunks.append(current)
    return chunks


def _start_x(style: RasterBlockStyle, line_width: float) -> float:
    free = max(0.0, style.content_width - line_width)
    match style.align:
        case "left":
            return float(style.padding)
        case "center":
            return style.padding + free / 2
        case "right":
            return style.padding + free


def _draw_run(draw: ImageDraw.ImageDraw, run: _Run, *, x: float, top: int, line: _Line) -> None:
    ink, paper = (_PAPER, _INK) if run.span.invert else (_INK, _PAPER)
    baseline = top + line.ascent
    if run.span.invert:
        draw.rectangle((x, top, x + run.width, top + line.height), fill=paper)
    draw.text((x, baseline), run.text, font=run.font, fill=ink, anchor="ls")
    if run.span.underline:
        y = baseline + _UNDERLINE_OFFSET
        draw.line((x, y, x + run.width, y), fill=ink, width=1)
