import pytest
from PIL import Image

from printbot.formatting import Dither, fit_within, pad_horizontal, rotate, to_one_bit
from printbot.kernel import Alignment


def colors(image: Image.Image) -> set[int]:
    return {value for value, count in enumerate(image.histogram()) if count}


def gradient(width: int = 64, height: int = 16) -> Image.Image:
    image = Image.new("L", (width, height))
    for x in range(width):
        for y in range(height):
            image.putpixel((x, y), round(x / (width - 1) * 255))
    return image


def test_fit_within_shrinks_to_width_keeping_aspect() -> None:
    result = fit_within(Image.new("RGB", (1000, 500)), 512)
    assert result.size == (512, 256)


def test_fit_within_respects_height_limit() -> None:
    result = fit_within(Image.new("RGB", (400, 800)), 512, 200)
    assert result.size == (100, 200)


def test_fit_within_does_not_upscale_by_default() -> None:
    image = Image.new("RGB", (100, 50))
    assert fit_within(image, 512) is image


def test_fit_within_upscales_when_allowed() -> None:
    result = fit_within(Image.new("RGB", (100, 50)), 200, allow_upscale=True)
    assert result.size == (200, 100)


def test_rotate_swaps_dimensions_for_quarter_turn() -> None:
    assert rotate(Image.new("RGB", (30, 10)), 90).size == (10, 30)


@pytest.mark.parametrize(("align", "expected_x"), [("center", 20), ("right", 40)])
def test_pad_horizontal_places_image(align: Alignment, expected_x: int) -> None:
    black = Image.new("1", (20, 4), 0)
    padded = pad_horizontal(black, 60, align)
    assert padded.size == (60, 4)
    assert padded.mode == "1"
    assert padded.getpixel((expected_x, 0)) == 0
    assert padded.getpixel((expected_x - 1, 0)) == 255


def test_pad_horizontal_left_and_oversized_are_unchanged() -> None:
    image = Image.new("1", (20, 4), 0)
    assert pad_horizontal(image, 60, "left") is image
    assert pad_horizontal(image, 10, "center") is image


@pytest.mark.parametrize("dither", ["floyd_steinberg", "threshold", "ordered"])
def test_to_one_bit_returns_one_bit_image_of_same_size(dither: Dither) -> None:
    result = to_one_bit(gradient(), dither)
    assert result.mode == "1"
    assert result.size == (64, 16)


@pytest.mark.parametrize("dither", ["floyd_steinberg", "threshold", "ordered"])
def test_black_and_white_inputs_stay_pure(dither: Dither) -> None:
    black = to_one_bit(Image.new("L", (16, 16), 0), dither)
    white = to_one_bit(Image.new("L", (16, 16), 255), dither)
    assert colors(black) == {0}
    assert colors(white) == {255}


def test_threshold_is_a_hard_cut() -> None:
    result = to_one_bit(gradient(), "threshold")
    assert result.getpixel((5, 0)) == 0
    assert result.getpixel((60, 0)) == 255


def test_ordered_and_error_diffusion_keep_midtones_mixed() -> None:
    midtone = Image.new("L", (32, 32), 128)
    dithers: tuple[Dither, ...] = ("floyd_steinberg", "ordered")
    for dither in dithers:
        assert colors(to_one_bit(midtone, dither)) == {0, 255}


def test_transparent_pixels_become_white() -> None:
    transparent = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    result = to_one_bit(transparent, "threshold")
    assert colors(result) == {255}
