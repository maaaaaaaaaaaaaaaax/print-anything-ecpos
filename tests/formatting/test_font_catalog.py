import itertools

import pytest
from PIL import ImageFont

from printbot.formatting import FontFamily, FontVariant, load_font, variant_for

FAMILIES: tuple[FontFamily, ...] = ("sans", "serif", "monospace")
VARIANTS: tuple[FontVariant, ...] = ("regular", "bold", "italic", "bold_italic")


@pytest.mark.parametrize(("family", "variant"), list(itertools.product(FAMILIES, VARIANTS)))
def test_every_bundled_font_loads(family: FontFamily, variant: FontVariant) -> None:
    font = load_font(family, variant, 24)
    assert font.getlength("Grüße ß") > 0


def test_fonts_are_cached_per_size() -> None:
    assert load_font("sans", "regular", 20) is load_font("sans", "regular", 20)
    assert load_font("sans", "regular", 20) is not load_font("sans", "regular", 21)


@pytest.mark.parametrize(
    ("bold", "italic", "expected"),
    [
        (False, False, "regular"),
        (True, False, "bold"),
        (False, True, "italic"),
        (True, True, "bold_italic"),
    ],
)
def test_variant_for(bold: bool, italic: bool, expected: FontVariant) -> None:
    assert variant_for(bold=bold, italic=italic) == expected


@pytest.mark.parametrize("family", FAMILIES)
def test_fonts_use_the_basic_layout_engine_for_deterministic_output(family: FontFamily) -> None:
    assert load_font(family, "regular", 24).layout_engine == ImageFont.Layout.BASIC
