from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from database.crud.user import get_user
from utils.i18n import get_text
from filters.admin_filter import AdminFilter
from config import settings

class PaymentCheckMiddleware(BaseMiddleware):
    """Middleware to check if a user has paid before accessing certain functionalities"""
    
    def __init__(self, admin_ids: list):
        self.admin_ids = admin_ids
        
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Skip check for admin users
        if isinstance(event, Message) and str(event.from_user.id) in self.admin_ids:
            return await handler(event, data)
        
        if isinstance(event, CallbackQuery) and str(event.from_user.id) in self.admin_ids:
            return await handler(event, data)
        
        # Check if the user has paid
        user = await get_user(data["session"], event.from_user.id)
        
        if not user:
            # User doesn't exist, let the handler deal with it
            return await handler(event, data)
        
        # Allowed actions even if not paid
        allowed_commands = ["/start", "/admin", "/help"]
        allowed_buttons = ["buttons.about_us", "buttons.contact_teacher", "buttons.settings", "settings.language"]
        
        if isinstance(event, Message):
            # Allow certain commands for all users
            if event.text and event.text in allowed_commands:
                return await handler(event, data)
            
            # Check if text is in allowed buttons
            for button in allowed_buttons:
                translations = [get_text(button, "ru"), get_text(button, "uz")]
                if event.text and event.text in translations:
                    return await handler(event, data)
        
        # Block access if not paid
        if not user.is_paid:
            i18n_language = data.get("i18n_language", "ru")
            
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ Для доступа к этой функции требуется оплата. Пожалуйста, свяжитесь с администратором."
                    if i18n_language == "ru" else
                    "⚠️ Bu funksiyaga kirish uchun to'lov talab qilinadi. Iltimos, administrator bilan bog'laning."
                )
                return
            
            if isinstance(event, CallbackQuery):
                await event.answer(
                    "⚠️ Требуется оплата. Свяжитесь с администратором."
                    if i18n_language == "ru" else
                    "⚠️ To'lov talab qilinadi. Administrator bilan bog'laning.",
                    show_alert=True
                )
                return
        
        # If we get here, the user is allowed to proceed
        return await handler(event, data) 