from datetime import UTC, datetime

from aiogram.types import Chat, Message, TelegramObject, Update, User

from printbot.messaging import AllowlistMiddleware


def message_update(user_id: int) -> Update:
    user = User(id=user_id, is_bot=False, first_name="Test")
    chat = Chat(id=user_id, type="private")
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=chat,
        from_user=user,
        text="hello",
    )
    return Update(update_id=1, message=message)


async def test_allowed_user_reaches_handler() -> None:
    called = False

    async def handler(_event: TelegramObject, _data: dict[str, object]) -> str:
        nonlocal called
        called = True
        return "handled"

    middleware = AllowlistMiddleware(frozenset({42}))

    result = await middleware(handler, message_update(42), {})

    assert result == "handled"
    assert called


async def test_rejected_user_does_not_reach_handler() -> None:
    called = False

    async def handler(_event: TelegramObject, _data: dict[str, object]) -> str:
        nonlocal called
        called = True
        return "handled"

    middleware = AllowlistMiddleware(frozenset({42}))

    result = await middleware(handler, message_update(7), {})

    assert result is None
    assert not called


async def test_update_without_user_does_not_reach_handler() -> None:
    called = False

    async def handler(_event: TelegramObject, _data: dict[str, object]) -> str:
        nonlocal called
        called = True
        return "handled"

    middleware = AllowlistMiddleware(frozenset({42}))

    result = await middleware(handler, Update(update_id=1), {})

    assert result is None
    assert not called
