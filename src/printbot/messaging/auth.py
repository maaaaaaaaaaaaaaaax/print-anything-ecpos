from collections.abc import Awaitable, Callable

from aiogram.types import TelegramObject, Update, User
from aiogram.types.update import UpdateTypeLookupError

UpdateHandler = Callable[[TelegramObject, dict[str, object]], Awaitable[object]]


class AllowlistMiddleware:
    def __init__(self, allowed_user_ids: frozenset[int]) -> None:
        self._allowed_user_ids = allowed_user_ids

    async def __call__(
        self,
        handler: UpdateHandler,
        event: TelegramObject,
        data: dict[str, object],
    ) -> object | None:
        if not isinstance(event, Update):
            return None
        try:
            user = getattr(event.event, "from_user", None)
        except UpdateTypeLookupError:
            return None
        if not isinstance(user, User) or user.id not in self._allowed_user_ids:
            return None
        return await handler(event, data)
