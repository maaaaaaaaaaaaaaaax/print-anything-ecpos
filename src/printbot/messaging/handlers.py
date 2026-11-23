from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message


async def start(message: Message) -> None:
    await message.answer("Printbot is ready.")


async def acknowledge_text(message: Message) -> None:
    await message.answer("Message received.")


def create_router() -> Router:
    router = Router()
    router.message.register(start, CommandStart())
    router.message.register(acknowledge_text, F.text)
    return router
