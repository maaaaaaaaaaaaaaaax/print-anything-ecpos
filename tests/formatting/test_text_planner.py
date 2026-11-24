import pytest

from printbot.formatting import plan_text
from printbot.kernel import CutOp, Document, FeedOp, Paragraph, RasterOp, Run, TextOp
from printbot.printing import load_bundled_profile

PROFILE = load_bundled_profile("tm_t88iv")


def document(text: str) -> Document:
    return Document(blocks=(Paragraph(runs=(Run(text=text),)),))


def test_plan_wraps_using_profile_columns() -> None:
    plan = plan_text(document("word " * 20), PROFILE)
    text_ops = [op for op in plan.ops if isinstance(op, TextOp)]

    assert text_ops
    assert all(len(op.text) <= PROFILE.font_a.columns for op in text_ops)
    assert len(text_ops) > 1
    assert isinstance(plan.ops[-2], FeedOp)
    assert isinstance(plan.ops[-1], CutOp)
    assert plan.length_mm > 0


def test_plan_preserves_blank_lines() -> None:
    plan = plan_text(document("one\n\ntwo"), PROFILE)

    assert [op.text for op in plan.ops if isinstance(op, TextOp)] == ["one", "", "two"]


def test_cp437_text_stays_native() -> None:
    plan = plan_text(document("Gr\u00fc\u00dfe \u00e4 \u20ac"), PROFILE)

    assert any(isinstance(op, TextOp) for op in plan.ops)
    assert not any(isinstance(op, RasterOp) for op in plan.ops)


def test_unsupported_character_rasterizes_the_entire_job() -> None:
    plan = plan_text(document("first\nsecond \u201cquoted\u201d \U0001f642"), PROFILE)
    raster_ops = [op for op in plan.ops if isinstance(op, RasterOp)]

    assert len(raster_ops) == 1
    assert not any(isinstance(op, TextOp) for op in plan.ops)
    assert raster_ops[0].image.width == PROFILE.print_width_dots


def test_identical_documents_produce_identical_plans() -> None:
    first = plan_text(document("same text"), PROFILE)
    second = plan_text(document("same text"), PROFILE)

    assert first == second


@pytest.mark.parametrize("character", ["\u2013", "\u2192", "\U0001f642"])
def test_common_unsupported_characters_use_raster_fallback(character: str) -> None:
    plan = plan_text(document(f"text {character}"), PROFILE)

    assert any(isinstance(op, RasterOp) for op in plan.ops)
