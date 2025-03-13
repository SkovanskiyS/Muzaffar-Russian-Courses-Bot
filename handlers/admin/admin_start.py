from logging_config import logger

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv
from aiogram.types import ReplyKeyboardRemove

from filters.admin_filter import AdminFilter
from database.db import async_session
from database.crud.user import get_user, check_if_admin
from config import settings
from utils.i18n import get_text

from keyboards.admin import get_admin_main_keyboard

load_dotenv()

router = Router()
ADMIN_IDS: list = []

try:
    if settings.ADMIN_IDS:
        ADMIN_IDS = list(map(int, settings.ADMIN_IDS.split(",")))
except Exception as e:
    logger.error(f"Error parsing ADMIN_IDS from environment: {e}")

@router.message(Command("admin"))
async def start_handler(message: Message, session, i18n_language: str):
    # Check if user is an admin in database
    is_admin = await check_if_admin(session, message.from_user.id)
    
    if is_admin:
        await message.answer(get_text("admin.welcome", i18n_language), reply_markup=get_admin_main_keyboard(i18n_language))
    else:
        await message.answer(get_text("errors.access_denied", i18n_language), reply_markup=ReplyKeyboardRemove())
