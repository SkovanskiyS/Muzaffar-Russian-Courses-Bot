import logging, os

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

from filters.admin_filter import AdminFilter
from database.db import async_session
from database.crud.user import get_user
from config import settings


load_dotenv()

router = Router()
ADMIN_IDS: list = []

try:
    ADMIN_IDS = list(map(int, settings.ADMIN_IDS.split(",")))
except Exception as e:
    logging.error(f"ADMIN_IDS is not set\nError: {e}")

@router.message(Command("admin"), AdminFilter(ADMIN_IDS))
async def start_handler(message: Message):
    await message.answer("This is only avaiable for admins.")

@router.message(Command("add"), AdminFilter(ADMIN_IDS))
async def add_handler(message: Message):
    print('we are here')

    async with async_session() as session:
        user = await get_user(session, message.from_user.id)
        print(user)