from logging_config import logger

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

from filters.admin_filter import AdminFilter
from database.db import async_session
from database.crud.user import get_user
from config import settings
from utils.i18n import get_text

# NEW ADMIN KEYBOARD BY AI
#from keyboards.default.admin_keyboard import admin_main_menu_keyboard
from keyboards.admin import get_admin_main_keyboard

load_dotenv()

router = Router()
ADMIN_IDS: list = []

try:
    ADMIN_IDS = list(map(int, settings.ADMIN_IDS.split(",")))
except Exception as e:
    logger.error(f"ADMIN_IDS is not set\nError: {e}")

@router.message(Command("admin"), AdminFilter(ADMIN_IDS))
async def start_handler(message: Message, i18n_language: str):
    await message.answer(get_text("admin.welcome", i18n_language), reply_markup=get_admin_main_keyboard(i18n_language))

@router.message(Command("add"), AdminFilter(ADMIN_IDS))
async def add_handler(message: Message, i18n_language: str):
    async with async_session() as session:
        user = await get_user(session, message.from_user.id)
