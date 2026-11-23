from datetime import UTC, datetime
from unittest.mock import AsyncMock

from aiogram.types import Chat, Message, User

from printbot.messaging import acknowledge_text, start


def message(text: str) -> Message:
    user = User(id=42, is_bot=False, first_name="Test")
    chat = Chat(id=42, type="private")
    return Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=chat,
        from_user=user,
        text=text,
    )


async def test_start_acknowledges_message(monkeypatch) -> None:
    telegram_message = message("/start")
    answer = AsyncMock()
    monkeypatch.setattr(Message, "answer", answer)

    await start(telegram_message)

    answer.assert_awaited_once_with("Printbot is ready.")


async def test_text_message_is_acknowledged(monkeypatch) -> None:
    telegram_message = message("hello")
    answer = AsyncMock()
    monkeypatch.setattr(Message, "answer", answer)

    await acknowledge_text(telegram_message)

    answer.assert_awaited_once_with("Message received.")
