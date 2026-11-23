from typing import Self

from pydantic import Field, model_validator

from printbot.kernel.literals import NativeFont
from printbot.kernel.models import Frozen

MM_PER_INCH = 25.4


class UsbId(Frozen):
    vendor: int = Field(ge=0, le=0xFFFF)
    product: int = Field(ge=0, le=0xFFFF)


class FontMetrics(Frozen):
    columns: int = Field(gt=0)
    char_width_dots: int = Field(gt=0)
    line_height_dots: int = Field(gt=0)


class PrinterProfile(Frozen):
    model: str
    escpos_profile: str
    dpi: int = Field(gt=0)
    print_width_dots: int = Field(gt=0)
    font_a: FontMetrics
    font_b: FontMetrics
    usb: UsbId

    @model_validator(mode="after")
    def _fonts_fit_print_width(self) -> Self:
        for name in ("a", "b"):
            metrics = self.font(name)
            if metrics.columns * metrics.char_width_dots > self.print_width_dots:
                raise ValueError(
                    f"font {name} needs {metrics.columns * metrics.char_width_dots} dots "
                    f"but the print width is {self.print_width_dots}"
                )
        return self

    @property
    def dots_per_mm(self) -> float:
        return self.dpi / MM_PER_INCH

    def font(self, name: NativeFont) -> FontMetrics:
        return self.font_a if name == "a" else self.font_b
