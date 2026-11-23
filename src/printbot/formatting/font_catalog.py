from functools import cache
from importlib.resources import files
from io import BytesIO
from typing import Final, Literal

from PIL import ImageFont

FontFamily = Literal["sans", "serif", "monospace"]
FontVariant = Literal["regular", "bold", "italic", "bold_italic"]

_FONT_PACKAGE = "printbot.formatting"
_FONT_DIRECTORY = "fonts"

_FILENAMES: Final[dict[FontFamily, dict[FontVariant, str]]] = {
    "sans": {
        "regular": "Inter-Regular.ttf",
        "bold": "Inter-Bold.ttf",
        "italic": "Inter-Italic.ttf",
        "bold_italic": "Inter-BoldItalic.ttf",
    },
    "serif": {
        "regular": "NotoSerif-Regular.ttf",
        "bold": "NotoSerif-Bold.ttf",
        "italic": "NotoSerif-Italic.ttf",
        "bold_italic": "NotoSerif-BoldItalic.ttf",
    },
    "monospace": {
        "regular": "JetBrainsMono-Regular.ttf",
        "bold": "JetBrainsMono-Bold.ttf",
        "italic": "JetBrainsMono-Italic.ttf",
        "bold_italic": "JetBrainsMono-BoldItalic.ttf",
    },
}


def variant_for(*, bold: bool, italic: bool) -> FontVariant:
    if bold and italic:
        return "bold_italic"
    if bold:
        return "bold"
    if italic:
        return "italic"
    return "regular"


@cache
def load_font(family: FontFamily, variant: FontVariant, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        BytesIO(_font_bytes(_FILENAMES[family][variant])),
        size=size,
        layout_engine=ImageFont.Layout.BASIC,
    )


@cache
def _font_bytes(filename: str) -> bytes:
    return (files(_FONT_PACKAGE) / _FONT_DIRECTORY / filename).read_bytes()
