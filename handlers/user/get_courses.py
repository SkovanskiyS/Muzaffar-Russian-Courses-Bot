import logging

from aiogram import Router, F
from aiogram.handlers.message import Message
from aiogram.types import CallbackQuery

from database.db import async_session
from sqlalchemy.future import select
from database.models.user import Students
from database.models.courses import Course, CourseType
from logging_config import logger
from utils.i18n import get_text, get_all_translations_for_key

from keyboards.inline.courses_type import courses_type
router = Router()

@router.message(F.text.in_(get_all_translations_for_key("buttons.courses")))
async def courses_handler(message: Message, i18n_language: str):
    async with async_session() as session:
        result = await session.execute(
            select(Course)
            .join(CourseType)
            .where(Course.is_active == True)
            .order_by(Course.order_index)
        )
        courses = result.scalars().all()

        if not courses:
            await message.answer(get_text("courses.no_courses", i18n_language))
            return

        text = get_text("courses.list_title", i18n_language) + "\n\n"
        
        for course in courses:
            text += (
                f"📚 {course.title}\n"
                f"{get_text('courses.type', i18n_language)}: {course.course_type.name}\n"
                f"{get_text('courses.description', i18n_language)}: {course.description}\n"
                "-------------------\n"
            )

        await message.answer(text)

@router.callback_query(lambda c: c.data == 'russian_language')
async def russian_language_handler(callback_query: CallbackQuery):
    await callback_query.message.delete()
    await callback_query.message.answer('here should be all available courses which will come from database')
    async with async_session() as session:
        # get avaiable courses and create dynamic buttons for each course
        ...