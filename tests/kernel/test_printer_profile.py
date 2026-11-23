import pytest
from pydantic import ValidationError

from printbot.kernel import FontMetrics, PrinterProfile, UsbId


def make_profile(**overrides: object) -> PrinterProfile:
    values: dict[str, object] = {
        "model": "TM-T88IV",
        "escpos_profile": "TM-T88IV",
        "dpi": 180,
        "print_width_dots": 512,
        "font_a": FontMetrics(columns=42, char_width_dots=12, line_height_dots=24),
        "font_b": FontMetrics(columns=56, char_width_dots=9, line_height_dots=17),
        "usb": UsbId(vendor=0x04B8, product=0x0202),
    }
    values.update(overrides)
    return PrinterProfile.model_validate(values)


def test_dots_per_mm_uses_dpi() -> None:
    assert make_profile().dots_per_mm == pytest.approx(7.087, abs=1e-3)


def test_font_lookup_by_name() -> None:
    profile = make_profile()
    assert profile.font("a").columns == 42
    assert profile.font("b").columns == 56


def test_fonts_wider_than_print_width_are_rejected() -> None:
    with pytest.raises(ValidationError, match="print width"):
        make_profile(font_a=FontMetrics(columns=48, char_width_dots=12, line_height_dots=24))


def test_usb_ids_must_fit_sixteen_bits() -> None:
    with pytest.raises(ValidationError):
        UsbId(vendor=0x10000, product=1)
