import pytest

from printbot.formatting import align_line, boxed, rule, table_row, two_columns, wrap_text
from printbot.kernel import Alignment


def test_wrap_text_wraps_at_width_and_keeps_blank_lines() -> None:
    assert wrap_text("aaa bbb ccc\n\nddd", 7) == ["aaa bbb", "ccc", "", "ddd"]


def test_wrap_text_breaks_overlong_words() -> None:
    assert wrap_text("abcdefghij", 4) == ["abcd", "efgh", "ij"]


@pytest.mark.parametrize("width", [0, -3])
def test_non_positive_widths_are_rejected(width: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        wrap_text("x", width)
    with pytest.raises(ValueError, match="positive"):
        rule(width)


@pytest.mark.parametrize(
    ("align", "expected"),
    [("left", "ab   "), ("right", "   ab"), ("center", " ab  ")],
)
def test_align_line(align: Alignment, expected: str) -> None:
    assert align_line("ab", 5, align) == expected


def test_align_line_leaves_long_text_alone() -> None:
    assert align_line("abcdef", 4, "center") == "abcdef"


def test_rule_truncates_multi_character_patterns() -> None:
    assert rule(5, "-=") == "-=-=-"


def test_two_columns_pads_and_right_aligns() -> None:
    assert two_columns("Total", "9.50", 20) == ["Total           9.50"]


def test_two_columns_wraps_the_left_column() -> None:
    lines = two_columns("a long left column text", "R", 12)
    assert all(len(line) == 12 for line in lines)
    assert lines[0].endswith("R")
    assert len(lines) > 1


def test_two_columns_without_right_text_just_wraps() -> None:
    assert two_columns("one two", "", 4) == ["one", "two"]


def test_two_columns_rejects_impossible_width() -> None:
    with pytest.raises(ValueError, match="too small"):
        two_columns("a", "b", 2)


def test_table_row_splits_width_evenly() -> None:
    assert table_row(["a", "b", "c"], 11) == "a   b   c  "


def test_table_row_truncates_with_ellipsis() -> None:
    assert table_row(["abcdefgh", "x"], 12, widths=[7, 4]) == "abcd... x   "


def test_table_row_rejects_widths_that_do_not_fit() -> None:
    with pytest.raises(ValueError, match="do not fit"):
        table_row(["a", "b"], 10, widths=[8, 8])


def test_empty_table_row_is_empty() -> None:
    assert table_row([], 10) == ""


def test_boxed_frames_wrapped_text() -> None:
    assert boxed("hello world", 11) == [
        "-----------",
        "| hello   |",
        "| world   |",
        "-----------",
    ]


def test_wrap_text_normalizes_line_endings_and_composition() -> None:
    assert wrap_text("one\r\ntwo\rGru\u0308n", 20) == ["one", "two", "Gr\u00fcn"]
