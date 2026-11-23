import pytest
from PIL import Image
from pydantic import ValidationError

from printbot.kernel import CutOp, FeedOp, PrintPlan, QrOp, RasterOp, TextOp, TextStyle


def test_text_op_defaults_to_plain_style() -> None:
    op = TextOp(text="hello")
    assert op.style == TextStyle()
    assert op.kind == "text"


@pytest.mark.parametrize("size", [0, 9])
def test_text_style_rejects_out_of_range_size(size: int) -> None:
    with pytest.raises(ValidationError):
        TextStyle(width=size)
    with pytest.raises(ValidationError):
        TextStyle(height=size)


def test_ops_are_immutable() -> None:
    op = FeedOp(lines=2)
    with pytest.raises(ValidationError):
        setattr(op, "lines", 3)


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        CutOp.model_validate({"mode": "full", "extra": True})


def test_plan_holds_mixed_ops_and_images() -> None:
    image = Image.new("1", (8, 8), 1)
    plan = PrintPlan(
        ops=(TextOp(text="a"), RasterOp(image=image), QrOp(data="x"), FeedOp(), CutOp()),
        length_mm=12.5,
    )
    assert [op.kind for op in plan.ops] == ["text", "raster", "qr", "feed", "cut"]


def test_plan_rejects_negative_length() -> None:
    with pytest.raises(ValidationError):
        PrintPlan(ops=(), length_mm=-1)


def test_raster_op_rejects_non_image() -> None:
    with pytest.raises(ValidationError):
        RasterOp(image="not an image")
