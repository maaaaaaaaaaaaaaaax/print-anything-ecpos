from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from aiogram.types import Chat, Message, Update, User

from printbot.app import Config, run

if TYPE_CHECKING:
    from aiogram import Bot, Dispatcher


class RecordingSession:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class RecordingBot:
    id = 1
    instances: ClassVar[list[RecordingBot]] = []

    def __init__(self, **_kwargs: object) -> None:
        self.session = RecordingSession()
        self.messages: list[tuple[int, str]] = []
        self.documents: list[tuple[int, object]] = []
        self.calls: list[object] = []
        self.instances.append(self)

    async def __call__(self, method: object) -> None:
        self.calls.append(method)

    async def send_message(self, chat_id: int, text: str) -> None:
        self.messages.append((chat_id, text))

    async def send_document(self, chat_id: int, document: object) -> None:
        self.documents.append((chat_id, document))


def text_update() -> Update:
    user = User(id=42, is_bot=False, first_name="Test")
    chat = Chat(id=42, type="private")
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=chat,
        from_user=user,
        text="hello from Telegram",
    )
    return Update(update_id=7, message=message)


async def test_run_wires_text_job_to_fake_print_and_stops_workers(
    monkeypatch,
    tmp_path: Path,
) -> None:
    RecordingBot.instances.clear()
    data_dir = tmp_path / "data"
    config = Config(
        telegram_token="123:secret",
        allowed_user_ids="42",
        data_dir=data_dir,
        printer_backend="fake",
        printer_profile="tm_t88iv",
        migrations_directory=Path("migrations"),
    )

    async def poll_once(bot: Bot, dispatcher: Dispatcher) -> None:
        assert isinstance(bot, RecordingBot)
        try:
            await dispatcher.feed_update(bot, text_update())
            for _ in range(100):
                output_exists = (data_dir / "prints" / "print-0001.png").exists()
                result_reported = (42, "Printed.") in bot.messages
                document_sent = bool(bot.documents)
                if not output_exists and document_sent and result_reported:
                    return
                await asyncio.sleep(0.01)
            raise AssertionError("text job did not finish")
        finally:
            await bot.session.close()

    monkeypatch.setattr("printbot.app.runtime.Bot", RecordingBot)
    monkeypatch.setattr("printbot.app.runtime.run_polling", poll_once)

    await run(config)

    assert RecordingBot.instances[0].session.closed
    assert not (data_dir / "prints" / "print-0001.png").exists()
    assert not (data_dir / "prints").exists()
    assert len(RecordingBot.instances[0].documents) == 1
    assert (42, "Printed.") in RecordingBot.instances[0].messages
