from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from aiogram.types import Chat, Message, Update, User

from printbot.app import Config, create_dispatcher

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.methods import TelegramMethod


class RecordingBot:
    id = 1

    def __init__(self) -> None:
        self.calls: list[TelegramMethod[object]] = []

    async def __call__(self, method: TelegramMethod[object]) -> None:
        self.calls.append(method)


def message_update(user_id: int, text: str) -> Update:
    user = User(id=user_id, is_bot=False, first_name="Test")
    chat = Chat(id=user_id, type="private")
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=chat,
        from_user=user,
        text=text,
    )
    return Update(update_id=1, message=message)


async def test_allowed_update_reaches_registered_text_handler() -> None:
    dispatcher = create_dispatcher(Config(telegram_token="123:secret", allowed_user_ids="42"))
    bot = RecordingBot()

    await dispatcher.feed_update(cast("Bot", bot), message_update(42, "hello"))

    assert len(bot.calls) == 1
    assert bot.calls[0].model_dump()["text"] == "Message received."


async def test_allowed_start_reaches_registered_command_handler() -> None:
    dispatcher = create_dispatcher(Config(telegram_token="123:secret", allowed_user_ids="42"))
    bot = RecordingBot()

    await dispatcher.feed_update(cast("Bot", bot), message_update(42, "/start"))

    assert len(bot.calls) == 1
    assert bot.calls[0].model_dump()["text"] == "Printbot is ready."


async def test_rejected_update_is_dropped_before_registered_handler() -> None:
    dispatcher = create_dispatcher(Config(telegram_token="123:secret", allowed_user_ids="42"))
    bot = RecordingBot()

    await dispatcher.feed_update(cast("Bot", bot), message_update(7, "hello"))

    assert bot.calls == []
