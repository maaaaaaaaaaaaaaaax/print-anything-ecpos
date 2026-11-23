from importlib.resources import files
from pathlib import Path

import yaml
from pydantic import ValidationError

from printbot.kernel import PrinterProfile
from printbot.printing.errors import ProfileError

_PROFILE_PACKAGE = "printbot.printing"
_PROFILE_DIRECTORY = "profiles"
_PROFILE_SUFFIX = ".yaml"


def bundled_profile_names() -> tuple[str, ...]:
    directory = files(_PROFILE_PACKAGE) / _PROFILE_DIRECTORY
    return tuple(
        sorted(
            entry.name.removesuffix(_PROFILE_SUFFIX)
            for entry in directory.iterdir()
            if entry.name.endswith(_PROFILE_SUFFIX)
        )
    )


def load_bundled_profile(name: str) -> PrinterProfile:
    resource = files(_PROFILE_PACKAGE) / _PROFILE_DIRECTORY / f"{name}{_PROFILE_SUFFIX}"
    if not resource.is_file():
        known = ", ".join(bundled_profile_names())
        raise ProfileError(f"unknown printer profile {name!r}, available: {known}")
    return _parse(resource.read_text(encoding="utf-8"), name)


def load_profile_file(path: Path) -> PrinterProfile:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ProfileError(f"cannot read printer profile {path}: {error}") from error
    return _parse(text, str(path))


def _parse(text: str, origin: str) -> PrinterProfile:
    try:
        raw = yaml.safe_load(text)
        return PrinterProfile.model_validate(raw)
    except (yaml.YAMLError, ValidationError) as error:
        raise ProfileError(f"invalid printer profile {origin}: {error}") from error
