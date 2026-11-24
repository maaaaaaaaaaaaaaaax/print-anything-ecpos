import asyncio
import time
from contextlib import suppress

from aiogram import Bot, Dispatcher

from printbot.app.config import Config
from printbot.formatting import plan_text
from printbot.ingest import PlainTextConverter
from printbot.jobs import ConversionWorker, JobService, PrintWorker
from printbot.kernel import PrinterProfile
from printbot.messaging import AllowlistMiddleware, TelegramNotifier, create_router
from printbot.printing import (
    EscposUsbPrinter,
    FakePrinter,
    Printer,
    load_bundled_profile,
    usb_device_factory,
)
from printbot.storage import SQLiteJobRepository


def create_dispatcher(config: Config, job_service: JobService) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.update.outer_middleware(AllowlistMiddleware(config.allowed_user_ids))
    dispatcher.include_router(create_router(job_service))
    return dispatcher


async def run_polling(bot: Bot, dispatcher: Dispatcher) -> None:
    try:
        await dispatcher.start_polling(bot, close_bot_session=False)
    finally:
        await bot.session.close()


async def run(config: Config) -> None:
    profile = load_bundled_profile(config.printer_profile)
    repository = SQLiteJobRepository(
        config.data_dir / "jobs.sqlite3",
        config.migrations_directory,
    )
    await repository.initialize()
    printer = create_printer(config, profile)
    bot = Bot(token=config.telegram_token)
    notifier = TelegramNotifier(bot)
    service = JobService(repository, time.time)
    conversion_worker = ConversionWorker(
        repository,
        PlainTextConverter(),
        plan_text,
        profile,
        notifier,
    )
    print_worker = PrintWorker(repository, plan_text, profile, printer, notifier)
    try:
        async with asyncio.TaskGroup() as tasks:
            conversion_task = tasks.create_task(conversion_worker.run())
            print_task = tasks.create_task(print_worker.run())
            try:
                await run_polling(bot, create_dispatcher(config, service))
            finally:
                conversion_task.cancel()
                print_task.cancel()
    finally:
        await printer.close()
        await repository.close()


def create_printer(config: Config, profile: PrinterProfile) -> Printer:
    if config.printer_backend == "fake":
        return FakePrinter(profile, config.data_dir / "prints")
    return EscposUsbPrinter(usb_device_factory(profile))


def main() -> None:
    with suppress(KeyboardInterrupt):
        asyncio.run(run(Config()))
