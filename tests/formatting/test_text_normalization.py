import pytest

from printbot.formatting import normalize_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("a\r\nb", "a\nb"),
        ("a\rb", "a\nb"),
        ("a\r\n\r\nb", "a\n\nb"),
        ("a\nb", "a\nb"),
        ("", ""),
    ],
)
def test_line_endings_become_line_feeds(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


def test_decomposed_characters_are_composed() -> None:
    assert normalize_text("u\u0308") == "\u00fc"
    assert normalize_text("Gru\u0308\u00dfe") == "Gr\u00fc\u00dfe"


def test_normalization_is_idempotent() -> None:
    once = normalize_text("a\r\nu\u0308")
    assert normalize_text(once) == once
