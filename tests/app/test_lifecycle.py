from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from printbot.app import run_polling

if TYPE_CHECKING:
    from aiogram import Bot, Dispatcher


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class FakeBot:
    def __init__(self) -> None:
        self.session = FakeSession()


class FakeDispatcher:
    def __init__(self) -> None:
        self.bot: Bot | None = None

    async def start_polling(self, bot: Bot, *, close_bot_session: bool) -> None:
        assert not close_bot_session
        self.bot = bot


async def test_run_polling_closes_session_after_shutdown() -> None:
    bot = FakeBot()
    dispatcher = FakeDispatcher()

    await run_polling(cast("Bot", bot), cast("Dispatcher", dispatcher))

    assert dispatcher.bot is bot
    assert bot.session.closed


async def test_run_polling_closes_session_when_polling_fails() -> None:
    class FailingDispatcher(FakeDispatcher):
        async def start_polling(self, bot: Bot, *, close_bot_session: bool) -> None:
            assert not close_bot_session
            self.bot = bot
            raise RuntimeError("polling stopped")

    bot = FakeBot()
    dispatcher = FailingDispatcher()

    with pytest.raises(RuntimeError, match="polling stopped"):
        await run_polling(cast("Bot", bot), cast("Dispatcher", dispatcher))

    assert bot.session.closed
