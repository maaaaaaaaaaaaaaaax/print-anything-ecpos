from importlib.resources import files

import pytest

LICENSE_FILES = [
    "Inter-OFL-1.1.txt",
    "JetBrainsMono-OFL-1.1.txt",
    "NotoSerif-Apache-2.0.txt",
]


def license_text(name: str) -> str:
    resource = files("printbot.formatting") / "fonts" / "licenses" / name
    return resource.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", LICENSE_FILES)
def test_every_bundled_family_ships_its_license(name: str) -> None:
    assert len(license_text(name)) > 1000


def test_ofl_files_carry_the_ofl_and_a_copyright_line() -> None:
    for name in ("Inter-OFL-1.1.txt", "JetBrainsMono-OFL-1.1.txt"):
        text = license_text(name)
        assert "SIL OPEN FONT LICENSE Version 1.1" in text
        assert text.startswith("Copyright")


def test_noto_serif_ships_the_apache_license() -> None:
    assert "Apache License" in license_text("NotoSerif-Apache-2.0.txt")
    assert "Version 2.0, January 2004" in license_text("NotoSerif-Apache-2.0.txt")


def test_license_overview_names_all_three_families() -> None:
    overview = license_text("README.md")
    for family in ("Inter", "JetBrains Mono", "Noto Serif"):
        assert family in overview
