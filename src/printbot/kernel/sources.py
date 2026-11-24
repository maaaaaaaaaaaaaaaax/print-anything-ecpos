from typing import Annotated, Literal

from pydantic import Field, field_validator

from printbot.kernel.models import Frozen


class TextSource(Frozen):
    kind: Literal["text"] = "text"
    text: Annotated[str, Field(min_length=1)]

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be blank")
        return value


Source = Annotated[TextSource, Field(discriminator="kind")]
