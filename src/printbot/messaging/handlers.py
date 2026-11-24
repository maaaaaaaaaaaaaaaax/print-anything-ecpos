from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, Update

from printbot.jobs import JobService


async def start(message: Message) -> None:
    await message.answer("Printbot is ready.")


async def submit_text(message: Message, update: Update, service: JobService) -> None:
    if message.text is None or not message.text.strip():
        return
    job = await service.submit(
        chat_id=message.chat.id,
        telegram_update_id=update.update_id,
        text=message.text,
    )
    if job is not None:
        await message.answer("Queued for printing.")


def create_router(service: JobService) -> Router:
    router = Router()
    router.message.register(start, CommandStart())

    async def handle_text(message: Message, event_update: Update) -> None:
        await submit_text(message, event_update, service)

    router.message.register(handle_text, F.text)
    return router
