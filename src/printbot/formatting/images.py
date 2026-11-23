from typing import Final, Literal

from PIL import Image, ImageChops

from printbot.kernel import Alignment

Dither = Literal["floyd_steinberg", "threshold", "ordered"]

_BAYER_4X4: Final = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)
_BAYER_SIZE: Final = 4
_BAYER_LEVELS: Final = 16
_ABOVE_ZERO_TO_WHITE: Final = [0] + [255] * 255


def fit_within(
    image: Image.Image,
    max_width: int,
    max_height: int | None = None,
    *,
    allow_upscale: bool = False,
) -> Image.Image:
    scale = max_width / image.width
    if max_height is not None:
        scale = min(scale, max_height / image.height)
    if scale >= 1 and not allow_upscale:
        return image
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    if size == image.size:
        return image
    return image.resize(size, Image.Resampling.LANCZOS)


def rotate(image: Image.Image, degrees: float) -> Image.Image:
    return image.rotate(degrees, expand=True, resample=Image.Resampling.BICUBIC, fillcolor="white")


def pad_horizontal(image: Image.Image, canvas_width: int, align: Alignment) -> Image.Image:
    if image.width >= canvas_width or align == "left":
        return image
    offset = (canvas_width - image.width) // 2 if align == "center" else canvas_width - image.width
    canvas = Image.new("RGB", (canvas_width, image.height), "white")
    canvas.paste(image.convert("RGB"), (offset, 0))
    if image.mode == "1":
        return canvas.convert("1", dither=Image.Dither.NONE)
    return canvas.convert(image.mode) if image.mode == "L" else canvas


def to_one_bit(image: Image.Image, dither: Dither) -> Image.Image:
    gray = _flatten_to_gray(image)
    match dither:
        case "floyd_steinberg":
            return gray.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
        case "threshold":
            return gray.convert("1", dither=Image.Dither.NONE)
        case "ordered":
            return _ordered_dither(gray)


def _flatten_to_gray(image: Image.Image) -> Image.Image:
    if image.mode in ("RGBA", "LA") or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        return Image.alpha_composite(background, rgba).convert("L")
    return image.convert("L")


def _ordered_dither(gray: Image.Image) -> Image.Image:
    threshold = _threshold_map(gray.size)
    above = ImageChops.subtract(gray, threshold).point(_ABOVE_ZERO_TO_WHITE)
    return above.convert("1", dither=Image.Dither.NONE)


def _threshold_map(size: tuple[int, int]) -> Image.Image:
    width, height = size
    tile = Image.new("L", (_BAYER_SIZE, _BAYER_SIZE))
    for row, values in enumerate(_BAYER_4X4):
        for column, value in enumerate(values):
            tile.putpixel((column, row), round((value + 0.5) / _BAYER_LEVELS * 255))
    strip = Image.new("L", (width, _BAYER_SIZE))
    for x in range(0, width, _BAYER_SIZE):
        strip.paste(tile, (x, 0))
    full = Image.new("L", (width, height))
    for y in range(0, height, _BAYER_SIZE):
        full.paste(strip, (0, y))
    return full
