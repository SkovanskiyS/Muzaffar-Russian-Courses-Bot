from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database.crud.user import get_user
from utils.i18n import DEFAULT_LANGUAGE

class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any]
    ) -> Any:
        # Get user from the database
        user = None
        if isinstance(event, Message):
            user = await get_user(data["session"], event.from_user.id)
        elif isinstance(event, CallbackQuery):
            user = await get_user(data["session"], event.from_user.id)

        # Set language in data
        data["i18n_language"] = user.language if user else DEFAULT_LANGUAGE
        
        # Call the handler
        return await handler(event, data) 