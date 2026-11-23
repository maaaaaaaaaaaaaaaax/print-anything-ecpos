from typing import Annotated, Literal

from PIL import Image
from pydantic import ConfigDict, Field

from printbot.kernel.literals import Alignment, CutMode, NativeFont
from printbot.kernel.models import Frozen


class PlanModel(Frozen):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class TextStyle(Frozen):
    font: NativeFont = "a"
    bold: bool = False
    underline: bool = False
    invert: bool = False
    width: int = Field(default=1, ge=1, le=8)
    height: int = Field(default=1, ge=1, le=8)
    align: Alignment = "left"


class TextOp(Frozen):
    kind: Literal["text"] = "text"
    text: str
    style: TextStyle = Field(default_factory=TextStyle)


class RasterOp(PlanModel):
    kind: Literal["raster"] = "raster"
    image: Image.Image
    centered: bool = False


class QrOp(Frozen):
    kind: Literal["qr"] = "qr"
    data: str
    size: int = Field(default=3, ge=1, le=16)
    centered: bool = True


class FeedOp(Frozen):
    kind: Literal["feed"] = "feed"
    lines: int = Field(default=1, ge=1, le=255)


class CutOp(Frozen):
    kind: Literal["cut"] = "cut"
    mode: CutMode = "full"


PrintOp = Annotated[
    TextOp | RasterOp | QrOp | FeedOp | CutOp,
    Field(discriminator="kind"),
]


class PrintPlan(PlanModel):
    ops: tuple[PrintOp, ...]
    length_mm: float = Field(ge=0)
