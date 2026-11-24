from typing import Annotated, Literal

from pydantic import Field

from printbot.kernel.models import Frozen


class Run(Frozen):
    text: str
    bold: bool = False
    italic: bool = False


class Paragraph(Frozen):
    kind: Literal["paragraph"] = "paragraph"
    runs: Annotated[tuple[Run, ...], Field(min_length=1)]


Block = Annotated[Paragraph, Field(discriminator="kind")]


class Document(Frozen):
    blocks: Annotated[tuple[Block, ...], Field(min_length=1)]
