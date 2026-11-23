import pytest
from PIL import Image

from printbot.formatting import RasterBlockStyle, RasterSpan, render_spans
from printbot.kernel import Alignment

WIDTH = 512
INK_TABLE = [255] * 128 + [0] * 128


def ink_box(image: Image.Image) -> tuple[int, int, int, int]:
    box = image.point(INK_TABLE).getbbox()
    assert box is not None
    return box


def ink_count(image: Image.Image) -> int:
    return sum(image.histogram()[:128])


def test_output_has_requested_width_and_is_grayscale() -> None:
    image = render_spans([RasterSpan("Hello")], RasterBlockStyle(width=WIDTH))
    assert image.width == WIDTH
    assert image.mode == "L"
    assert ink_count(image) > 0


def test_no_spans_gives_blank_padding_only() -> None:
    image = render_spans([], RasterBlockStyle(width=WIDTH, padding=8))
    assert image.size == (WIDTH, 16)
    assert ink_count(image) == 0


def test_long_text_wraps_into_more_lines() -> None:
    style = RasterBlockStyle(width=WIDTH)
    short = render_spans([RasterSpan("word")], style)
    long = render_spans([RasterSpan("word " * 60)], style)
    assert long.height > short.height * 3


def test_ink_stays_inside_the_padding() -> None:
    style = RasterBlockStyle(width=WIDTH, padding=20)
    left, _, right, _ = ink_box(render_spans([RasterSpan("word " * 60)], style))
    assert left >= 20
    assert right <= WIDTH - 20


def test_overlong_word_is_broken_instead_of_overflowing() -> None:
    style = RasterBlockStyle(width=200, padding=10)
    image = render_spans([RasterSpan("x" * 200)], style)
    _, _, right, _ = ink_box(image)
    assert right <= 190
    assert image.height > 60


@pytest.mark.parametrize("align", ["left", "center", "right"])
def test_alignment_moves_the_ink(align: Alignment) -> None:
    style = RasterBlockStyle(width=WIDTH, align=align, padding=8)
    left, _, right, _ = ink_box(render_spans([RasterSpan("Hi")], style))
    left_gap = left
    right_gap = WIDTH - right
    if align == "left":
        assert left_gap < 16
    elif align == "right":
        assert right_gap < 16
    else:
        assert abs(left_gap - right_gap) <= 2


def test_blank_lines_add_height() -> None:
    style = RasterBlockStyle(width=WIDTH)
    tight = render_spans([RasterSpan("a\nb")], style)
    spaced = render_spans([RasterSpan("a\n\n\nb")], style)
    assert spaced.height > tight.height + 40


def test_trailing_newline_does_not_add_a_line() -> None:
    style = RasterBlockStyle(width=WIDTH)
    with_newline = render_spans([RasterSpan("a\n")], style)
    without_newline = render_spans([RasterSpan("a")], style)
    assert with_newline.height == without_newline.height


def test_invert_fills_the_background() -> None:
    style = RasterBlockStyle(width=WIDTH)
    plain = render_spans([RasterSpan("Hello")], style)
    inverted = render_spans([RasterSpan("Hello", invert=True)], style)
    assert ink_count(inverted) > ink_count(plain) * 2


def test_underline_adds_ink() -> None:
    style = RasterBlockStyle(width=WIDTH)
    plain = render_spans([RasterSpan("Hello")], style)
    underlined = render_spans([RasterSpan("Hello", underline=True)], style)
    assert ink_count(underlined) > ink_count(plain)


def test_mixed_sizes_share_a_baseline() -> None:
    style = RasterBlockStyle(width=WIDTH, padding=0)
    small = RasterSpan("x", size=16)
    large = RasterSpan("x", size=64)
    mixed = render_spans([small, large], style)
    assert mixed.height == render_spans([large], style).height
    small_bottom = ink_box(mixed.crop((0, 0, 12, mixed.height)))[3]
    large_bottom = ink_box(mixed.crop((20, 0, 60, mixed.height)))[3]
    assert abs(small_bottom - large_bottom) <= 1


def test_styles_are_not_mutated() -> None:
    style = RasterBlockStyle(width=WIDTH, align="center")
    render_spans([RasterSpan("Hello")], style)
    assert style.align == "center"


def test_invalid_styles_are_rejected() -> None:
    with pytest.raises(ValueError, match="padding"):
        RasterBlockStyle(width=10, padding=8)
    with pytest.raises(ValueError, match="line spacing"):
        RasterBlockStyle(width=WIDTH, line_spacing=0)
    with pytest.raises(ValueError, match="font size"):
        RasterSpan("x", size=2)


def test_characters_outside_latin1_still_render() -> None:
    spans = [RasterSpan("arrow \u2192 check \u2713 greek \u03b1")]
    assert ink_count(render_spans(spans, RasterBlockStyle(width=WIDTH))) > 0


@pytest.mark.parametrize("ending", ["\r\n", "\r"])
def test_non_unix_line_endings_render_like_line_feeds(ending: str) -> None:
    style = RasterBlockStyle(width=WIDTH)
    unix = render_spans([RasterSpan("first\nsecond")], style)
    other = render_spans([RasterSpan(f"first{ending}second")], style)
    assert other.tobytes() == unix.tobytes()


def test_decomposed_and_composed_umlauts_render_identically() -> None:
    style = RasterBlockStyle(width=WIDTH)
    composed = render_spans([RasterSpan("Gr\u00fc\u00dfe")], style)
    decomposed = render_spans([RasterSpan("Gru\u0308\u00dfe")], style)
    assert composed.tobytes() == decomposed.tobytes()
