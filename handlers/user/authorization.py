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

# Get admin IDs from environment
ADMIN_IDS = []
try:
    if settings.ADMIN_IDS:
        ADMIN_IDS = settings.ADMIN_IDS.split(",")
except Exception as e:
    pass

@router.message(Command("start"))
async def start_handler(message: Message, i18n_language: str):
    async with async_session() as session:
        result = await session.execute(
            select(Students).where(Students.user_id == message.from_user.id)
        )
        student = result.scalars().first()
        
        # Check if user is in admin list from environment
        is_admin = str(message.from_user.id) in ADMIN_IDS

        if student is None:
            # Create a new student record
            student = Students(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                is_admin=False,  # Default to not admin
                is_blocked=False,
                is_paid=False
            )
            session.add(student)
            await session.commit()
            await message.answer(get_text("registration_success", i18n_language), reply_markup=main_menu_keyboard(), protect_content=True)
        else:
            # Always update user information
            student.username = message.from_user.username
            student.first_name = message.from_user.first_name
            student.last_name = message.from_user.last_name
            
            await session.commit()
            await message.answer(get_text("welcome_back", i18n_language), reply_markup=main_menu_keyboard(), protect_content=True)


