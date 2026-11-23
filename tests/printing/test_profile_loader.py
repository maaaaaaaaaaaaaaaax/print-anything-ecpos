from pathlib import Path

import pytest

from printbot.printing import (
    ProfileError,
    bundled_profile_names,
    load_bundled_profile,
    load_profile_file,
)


def test_bundled_profiles_are_listed() -> None:
    assert bundled_profile_names() == ("tm_t88iv", "tm_t88v")


def test_tm_t88iv_matches_epson_specification() -> None:
    profile = load_bundled_profile("tm_t88iv")
    assert profile.model == "TM-T88IV"
    assert profile.dpi == 180
    assert profile.print_width_dots == 512
    assert profile.font_a.columns == 42
    assert profile.font_b.columns == 56
    assert (profile.usb.vendor, profile.usb.product) == (0x04B8, 0x0202)


def test_tm_t88v_differs_only_in_identity() -> None:
    iv = load_bundled_profile("tm_t88iv")
    v = load_bundled_profile("tm_t88v")
    assert v.usb.product == 0x0E02
    assert (
        v.model_copy(update={"model": iv.model, "escpos_profile": iv.escpos_profile, "usb": iv.usb})
        == iv
    )


def test_unknown_profile_names_the_alternatives() -> None:
    with pytest.raises(ProfileError, match="tm_t88iv"):
        load_bundled_profile("nope")


def test_profile_file_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "custom.yaml"
    path.write_text(
        "model: X\nescpos_profile: default\ndpi: 203\nprint_width_dots: 576\n"
        "font_a: {columns: 48, char_width_dots: 12, line_height_dots: 24}\n"
        "font_b: {columns: 64, char_width_dots: 9, line_height_dots: 17}\n"
        "usb: {vendor: 0x1234, product: 0x5678}\n",
        encoding="utf-8",
    )
    profile = load_profile_file(path)
    assert profile.print_width_dots == 576
    assert profile.usb.vendor == 0x1234


def test_missing_file_is_a_profile_error(tmp_path: Path) -> None:
    with pytest.raises(ProfileError, match="cannot read"):
        load_profile_file(tmp_path / "absent.yaml")


@pytest.mark.parametrize("content", ["model: [", "model: X", "- a\n- b"])
def test_invalid_content_is_a_profile_error(tmp_path: Path, content: str) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ProfileError, match="invalid printer profile"):
        load_profile_file(path)
