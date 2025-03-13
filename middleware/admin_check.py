from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database.crud.user import get_user


class AdminRequiredMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Get user ID based on event type
        user_id = event.from_user.id if isinstance(event, Message) else event.from_user.id
        
        # Get session from data (provided by DatabaseMiddleware)
        session = data["session"]
        
        # Get user from database
        user = await get_user(session, user_id)
        
        # Check if user exists and is admin
        if not user or not user.is_admin:
            if isinstance(event, Message):
                await event.answer("⛔️ Эта команда доступна только для администраторов.")
            else:
                await event.answer("⛔️ Это действие доступно только для администраторов.", show_alert=True)
            return
        
        # If user is admin, proceed with handling the request
        return await handler(event, data) 