import pytest
from pydantic import ValidationError

from printbot.app import Config


def test_config_reads_token_and_allowed_user_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_TOKEN", "123:secret")
    monkeypatch.setenv("ALLOWED_USER_IDS", "42, 84")

    config = Config()

    assert config.telegram_token == "123:secret"
    assert config.allowed_user_ids == frozenset({42, 84})
    assert config.printer_backend == "fake"
    assert config.printer_profile == "tm_t88v"


def test_config_reads_runtime_paths_and_usb_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_TOKEN", "123:secret")
    monkeypatch.setenv("ALLOWED_USER_IDS", "42")
    monkeypatch.setenv("DATA_DIR", "/tmp/printbot-test")
    monkeypatch.setenv("PRINTER_BACKEND", "usb")
    monkeypatch.setenv("PRINTER_PROFILE", "tm_t88iv")

    config = Config()

    assert config.data_dir.as_posix() == "/tmp/printbot-test"
    assert config.printer_backend == "usb"
    assert config.printer_profile == "tm_t88iv"


@pytest.mark.parametrize("value", ["", "42,", "invalid"])
def test_config_rejects_invalid_allowed_user_ids(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("TELEGRAM_TOKEN", "123:secret")
    monkeypatch.setenv("ALLOWED_USER_IDS", value)

    with pytest.raises(ValidationError):
        Config()


def test_config_requires_token(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    monkeypatch.setenv("ALLOWED_USER_IDS", "42")

    with pytest.raises(ValidationError):
        Config()


def test_config_rejects_blank_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_TOKEN", "   ")
    monkeypatch.setenv("ALLOWED_USER_IDS", "42")

    with pytest.raises(ValidationError):
        Config()


def test_config_reads_dotenv_file(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    monkeypatch.delenv("ALLOWED_USER_IDS", raising=False)
    tmp_path.joinpath(".env").write_text(
        "TELEGRAM_TOKEN=123:file-secret\nALLOWED_USER_IDS=42,84\n",
        encoding="ascii",
    )

    config = Config()

    assert config.telegram_token == "123:file-secret"
    assert config.allowed_user_ids == frozenset({42, 84})
