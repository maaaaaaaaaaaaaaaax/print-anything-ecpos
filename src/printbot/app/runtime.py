import asyncio
from contextlib import suppress

from aiogram import Bot, Dispatcher

from printbot.app.config import Config
from printbot.messaging import AllowlistMiddleware, create_router


def create_dispatcher(config: Config) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.update.outer_middleware(AllowlistMiddleware(config.allowed_user_ids))
    dispatcher.include_router(create_router())
    return dispatcher


async def run_polling(bot: Bot, dispatcher: Dispatcher) -> None:
    try:
        await dispatcher.start_polling(bot, close_bot_session=False)
    finally:
        await bot.session.close()


async def run(config: Config) -> None:
    await run_polling(Bot(token=config.telegram_token), create_dispatcher(config))


def main() -> None:
    with suppress(KeyboardInterrupt):
        asyncio.run(run(Config()))
