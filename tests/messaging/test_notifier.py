import logging
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramNetworkError
from aiogram.methods import SendMessage

from printbot.jobs import Job, JobStatus
from printbot.kernel import TextSource
from printbot.messaging import TelegramNotifier


def job(status: JobStatus, error: str | None = None) -> Job:
    return Job(
        id=1,
        chat_id=42,
        telegram_update_id=7,
        source=TextSource(text="hello"),
        status=status,
        error=error,
        created_at=1,
        updated_at=2,
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (JobStatus.CONVERTING, "Converting..."),
        (JobStatus.READY, "Ready to print."),
        (JobStatus.PRINTING, "Printing..."),
        (JobStatus.DONE, "Printed."),
        (JobStatus.FAILED, "Print failed: usb unavailable"),
    ],
)
async def test_notifier_reports_job_status(status: JobStatus, expected: str) -> None:
    bot = AsyncMock()
    notifier = TelegramNotifier(bot)

    error = "usb unavailable" if status is JobStatus.FAILED else None
    await notifier.job_updated(job(status, error))

    bot.send_message.assert_awaited_once_with(42, expected)


async def test_notifier_does_not_interrupt_jobs_when_telegram_fails(caplog) -> None:
    bot = AsyncMock()
    bot.send_message.side_effect = TelegramNetworkError(
        method=SendMessage(chat_id=42, text="Printed."),
        message="network unavailable",
    )
    notifier = TelegramNotifier(bot)

    with caplog.at_level(logging.ERROR):
        await notifier.job_updated(job(JobStatus.DONE))

    assert "could not notify job 1" in caplog.text


async def test_notifier_sends_fake_png_document(tmp_path: Path) -> None:
    image = tmp_path / "print-0001.png"
    image.write_bytes(b"png")
    bot = AsyncMock()
    notifier = TelegramNotifier(bot)

    await notifier.job_output(job(JobStatus.DONE), image)

    bot.send_document.assert_awaited_once()
    call = bot.send_document.await_args
    assert call.kwargs["chat_id"] == 42
    assert call.kwargs["document"].path == image


async def test_notifier_upload_failure_preserves_fake_png(tmp_path: Path) -> None:
    image = tmp_path / "print-0001.png"
    image.write_bytes(b"png")
    bot = AsyncMock()
    bot.send_document.side_effect = TelegramNetworkError(
        method=SendMessage(chat_id=42, text="Printed."),
        message="upload unavailable",
    )
    notifier = TelegramNotifier(bot)

    sent = await notifier.job_output(job(JobStatus.DONE), image)

    assert sent is False
    assert image.exists()
