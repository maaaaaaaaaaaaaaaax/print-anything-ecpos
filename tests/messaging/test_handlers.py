from datetime import UTC, datetime
from unittest.mock import AsyncMock

from aiogram.types import Chat, Message, Update, User

from printbot.messaging import start, submit_text


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


async def test_text_message_is_queued(monkeypatch) -> None:
    telegram_message = message("hello")
    answer = AsyncMock()
    service = AsyncMock()
    service.submit.return_value = object()
    update = Update(update_id=7, message=telegram_message)
    monkeypatch.setattr(Message, "answer", answer)

    await submit_text(telegram_message, update, service)

    service.submit.assert_awaited_once_with(
        chat_id=42,
        telegram_update_id=7,
        text="hello",
    )
    answer.assert_awaited_once_with("Queued for printing.")


async def test_duplicate_text_update_is_not_acknowledged_again(monkeypatch) -> None:
    telegram_message = message("hello")
    answer = AsyncMock()
    service = AsyncMock()
    service.submit.return_value = None
    update = Update(update_id=7, message=telegram_message)
    monkeypatch.setattr(Message, "answer", answer)

    await submit_text(telegram_message, update, service)

    answer.assert_not_awaited()
