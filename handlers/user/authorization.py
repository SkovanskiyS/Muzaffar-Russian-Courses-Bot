from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv
from sqlalchemy.future import select

from config import settings
from database.models.user import Students
from database.db import async_session
from keyboards.default.user_keyboard import main_menu_keyboard
from utils.i18n import get_text

router = Router()
load_dotenv()

@router.message(Command("start"))
async def start_handler(message: Message, i18n_language: str):
    async with async_session() as session:
        result = await session.execute(
            select(Students).where(Students.user_id == message.from_user.id)
        )
        student = result.scalars().first()
        is_admin = False
        admin_list: list = [settings.ADMIN_IDS]
        if str(message.from_user.id) in admin_list:
            is_admin = True

        if student is None:
            # Create a new student record
            student = Students(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                is_admin=is_admin,
                is_blocked=False,
                is_paid=False
            )
            session.add(student)
            await session.commit()
            await message.answer(get_text("registration_success", i18n_language), reply_markup=main_menu_keyboard())
        else:
            student.username = message.from_user.username
            student.first_name = message.from_user.first_name
            student.last_name = message.from_user.last_name
            student.is_admin = is_admin
            await session.commit()
            await message.answer(get_text("welcome_back", i18n_language), reply_markup=main_menu_keyboard())


