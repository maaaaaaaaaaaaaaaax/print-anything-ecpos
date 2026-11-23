import pytest

from printbot.printing import PaperState
from printbot.printing.status_codes import parse_cover_open, parse_online, parse_paper


@pytest.mark.parametrize(
    ("reply", "expected"),
    [(b"\x12", True), (b"\x1a", False), (b"", None)],
)
def test_parse_online(reply: bytes, expected: bool | None) -> None:
    assert parse_online(reply) is expected


@pytest.mark.parametrize(
    ("reply", "expected"),
    [(b"\x12", PaperState.OK), (b"\x1e", PaperState.NEAR_END), (b"\x72", PaperState.OUT)],
)
def test_parse_paper(reply: bytes, expected: PaperState) -> None:
    assert parse_paper(reply) is expected


def test_parse_paper_without_reply_is_unknown_not_ok() -> None:
    assert parse_paper(b"") is PaperState.UNKNOWN


def test_parse_paper_with_unrecognised_bits_is_unknown() -> None:
    assert parse_paper(b"\x00") is PaperState.UNKNOWN


@pytest.mark.parametrize(
    ("reply", "expected"),
    [(b"\x16", True), (b"\x12", False), (b"", None)],
)
def test_parse_cover_open(reply: bytes, expected: bool | None) -> None:
    assert parse_cover_open(reply) is expected
