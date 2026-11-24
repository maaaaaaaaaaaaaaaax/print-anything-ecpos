import pytest
from pydantic import ValidationError

from printbot.app import Config


def test_config_reads_token_and_allowed_user_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_TOKEN", "123:secret")
    monkeypatch.setenv("ALLOWED_USER_IDS", "42, 84")

    config = Config()

    assert config.telegram_token == "123:secret"
    assert config.allowed_user_ids == frozenset({42, 84})


@pytest.mark.parametrize("value", ["", "42,", "invalid"])
def test_config_rejects_invalid_allowed_user_ids(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("TELEGRAM_TOKEN", "123:secret")
    monkeypatch.setenv("ALLOWED_USER_IDS", value)

    with pytest.raises(ValidationError):
        Config()


def test_config_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
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
