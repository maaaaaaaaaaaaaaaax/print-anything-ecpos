import asyncio
from pathlib import Path
from typing import assert_never

from PIL import Image, ImageDraw

from printbot.kernel import (
    CutOp,
    FeedOp,
    NativeFont,
    PrinterProfile,
    PrintPlan,
    QrOp,
    RasterOp,
    TextOp,
)
from printbot.printing.errors import PrinterExecutionError
from printbot.printing.ports import PaperState, PrinterStatus


class FakePrinter:
    def __init__(self, profile: PrinterProfile, output_directory: Path) -> None:
        self._profile = profile
        self._output_directory = output_directory
        self._plans: list[PrintPlan] = []
        self._saved_paths: list[Path] = []
        self._lock = asyncio.Lock()
        self._closed = False

    @property
    def plans(self) -> tuple[PrintPlan, ...]:
        return tuple(self._plans)

    @property
    def saved_paths(self) -> tuple[Path, ...]:
        return tuple(self._saved_paths)

    async def execute(self, plan: PrintPlan) -> Path:
        self._require_open()
        async with self._lock:
            try:
                self._output_directory.mkdir(parents=True, exist_ok=True)
                path = self._output_directory / f"print-{len(self._plans) + 1:04d}.png"
                _render_plan(plan, self._profile).save(path)
            except OSError as error:
                raise PrinterExecutionError(f"cannot write fake print: {error}") from error
            self._plans.append(plan)
            self._saved_paths.append(path)
            return path

    async def status(self) -> PrinterStatus:
        self._require_open()
        return PrinterStatus(
            online=True,
            paper=PaperState.OK,
            cover_open=False,
        )

    async def close(self) -> None:
        self._closed = True

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("printer is closed")


def _render_plan(plan: PrintPlan, profile: PrinterProfile) -> Image.Image:
    pieces: list[Image.Image] = []
    for op in plan.ops:
        match op:
            case TextOp(text=text, style=style):
                pieces.append(_render_text(text, profile, style.font))
            case RasterOp(image=image, centered=centered):
                pieces.append(_fit_raster(image, profile.print_width_dots, centered))
            case QrOp(data=data):
                pieces.append(_render_text(f"QR: {data}", profile, "a"))
            case FeedOp(lines=lines):
                pieces.append(
                    Image.new(
                        "L",
                        (profile.print_width_dots, lines * profile.font_a.line_height_dots),
                        255,
                    )
                )
            case CutOp():
                pass
            case _:
                assert_never(op)
    height = sum(image.height for image in pieces)
    output = Image.new("L", (profile.print_width_dots, max(1, height)), 255)
    top = 0
    for piece in pieces:
        output.paste(piece, (0, top))
        top += piece.height
    return output


def _render_text(text: str, profile: PrinterProfile, font: NativeFont) -> Image.Image:
    image = Image.new(
        "L",
        (profile.print_width_dots, profile.font(font).line_height_dots),
        255,
    )
    ImageDraw.Draw(image).text((0, 0), text, fill=0)
    return image


def _fit_raster(image: Image.Image, width: int, centered: bool) -> Image.Image:
    resized = image.convert("L")
    if resized.width > width:
        height = round(resized.height * width / resized.width)
        resized = resized.resize((width, max(1, height)))
    if resized.width == width:
        return resized
    output = Image.new("L", (width, resized.height), 255)
    left = (width - resized.width) // 2 if centered else 0
    output.paste(resized, (left, 0))
    return output
