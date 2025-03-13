import asyncio
import logging

from aiogram import Bot, Dispatcher # type: ignore
from aiogram.client.default import DefaultBotProperties # type: ignore
from aiogram.enums import ParseMode # type: ignore

from config import settings
from database import db
from handlers.admin import admin_start
from handlers.admin.courses import router as admin_courses_router
from handlers.admin.students import router as admin_students_router
from handlers.admin.admin_management import router as admin_management_router
from handlers.user import authorization, get_courses, contact_with_teacher, about_us, settings as user_settings
from handlers.user.courses import router as user_courses_router
from middleware.i18n import I18nMiddleware
from middleware.payment_check import PaymentCheckMiddleware
from middleware.admin_check import AdminRequiredMiddleware
from utils.i18n import load_translations
from logging_config import logger
from database.crud.user import get_admin_students

class DatabaseMiddleware:
    async def __call__(self, handler, event, data):
        async with db.async_session() as session:
            data["session"] = session
            return await handler(event, data)

async def main() -> None:
    logger.info('Starting bot...')
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Load translations
    load_translations()
    
    # Register middlewares
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())
    dp.message.middleware(PaymentCheckMiddleware([]))  # Empty list since we check database directly
    dp.callback_query.middleware(PaymentCheckMiddleware([]))  # Empty list since we check database directly
    
    # Create admin middleware instance
    admin_middleware = AdminRequiredMiddleware()
    
    # Register admin routers with admin middleware
    admin_routers = [
        admin_start.router,
        admin_courses_router,
        admin_students_router,
        admin_management_router
    ]
    
    for router in admin_routers:
        router.message.middleware(admin_middleware)
        router.callback_query.middleware(admin_middleware)
        dp.include_router(router)
    
    # Register user routers
    dp.include_routers(authorization.router)
    dp.include_routers(user_courses_router)
    dp.include_routers(contact_with_teacher.router)
    dp.include_routers(about_us.router)
    dp.include_routers(user_settings.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
