from logging_config import logger
from aiogram import Router, F, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.fsm.context import FSMContext

from database.crud.courses import get_active_course_types, get_courses_by_type_and_difficulty
from database.models.courses import DifficultyLevel, Course
from keyboards.user import (
    get_user_main_keyboard,
    get_course_type_keyboard,
    get_difficulty_selection_keyboard,
    get_course_list_keyboard,
    get_course_content_keyboard
)
from utils.i18n import get_text, get_all_translations_for_key

router = Router()

@router.message(F.text.in_(get_all_translations_for_key("buttons.courses")))
async def cmd_courses(message: types.Message, session: AsyncSession, i18n_language=None):
    """Show available course types"""
    course_types = await get_active_course_types(session)
    
    if not course_types:
        await message.answer(
            get_text("courses.no_courses", i18n_language),
            reply_markup=get_user_main_keyboard(i18n_language)
        )
        return
    
    keyboard = get_course_type_keyboard(course_types, i18n_language)
    await message.answer(get_text("course_type.select", i18n_language), reply_markup=keyboard)

@router.callback_query(F.data.startswith("view_course_type_"))
async def process_course_type_selection(callback: types.CallbackQuery, i18n_language=None):
    """Process course type selection and show difficulty levels"""
    course_type_id = int(callback.data.split("_")[-1])
    
    keyboard = get_difficulty_selection_keyboard(course_type_id, i18n_language)
    await callback.message.edit_text(get_text("course.select_difficulty", i18n_language), reply_markup=keyboard)

@router.callback_query(F.data.startswith("difficulty_"))
async def show_courses(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Show courses for selected type and difficulty"""
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer("Invalid selection")
        return
        
    course_type_id = int(parts[1])
    difficulty = parts[2]
    
    # Store the current difficulty level in state for back navigation
    await state.update_data(current_difficulty=difficulty)
    
    difficulty_level = None if difficulty == "all" else DifficultyLevel[difficulty]
    courses = await get_courses_by_type_and_difficulty(session, course_type_id, difficulty_level)
    print(f"view_course_type_{course_type_id}")
    if not courses:
        await callback.message.edit_text(
            get_text("course.no_available", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[[
                    types.InlineKeyboardButton( 
                        text=get_text("buttons.back", i18n_language),
                        callback_data=f"view_course_type_{course_type_id}"
                    )
                ]]
            )
        )
        return

    keyboard = get_course_list_keyboard(courses, i18n_language, course_type_id)
    await callback.message.edit_text(get_text("course.available", i18n_language), reply_markup=keyboard)

@router.callback_query(F.data.startswith("course_"))
async def show_course_details(callback: types.CallbackQuery, session: AsyncSession, i18n_language=None):
    """Show detailed information about a course"""
    course_id = int(callback.data.split("_")[-1])
    
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    
    if not course:
        await callback.message.edit_text(get_text("course.not_found", i18n_language))
        return
    
    # Send course banner
    if course.banner_file_id:
        await callback.message.answer_photo(
            photo=course.banner_file_id,
            caption=f"📚 {course.title}\n\n{course.description}",
            protect_content=True
        )
    
    # Send course content
    difficulty_text = get_text(f"course.difficulty.{course.difficulty_level.name.lower()}", i18n_language)
    content_message = (
        f"{get_text('course.title', i18n_language)}: {course.title}\n"
        f"{get_text('course.difficulty_title', i18n_language)}: {difficulty_text}\n"
        f"{get_text('course.order', i18n_language)}: {course.order_index}\n\n"
        f"{get_text('course.description', i18n_language)}: {course.description}\n\n"
        f"{get_text('course.text_explanation', i18n_language)}:\n{course.text_explanation}"
    )
    
    keyboard = get_course_content_keyboard(course_id, course.course_type_id, i18n_language)
    await callback.message.answer(content_message, reply_markup=keyboard)

@router.callback_query(F.data.startswith("video_"))
async def send_course_video(callback: types.CallbackQuery, session: AsyncSession, i18n_language=None):
    """Send course video content"""
    course_id = int(callback.data.split("_")[-1])
    
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    
    if course and course.video_file_id:
        await callback.message.answer_video(video=course.video_file_id)

@router.callback_query(F.data.startswith("voice_"))
async def send_course_voice(callback: types.CallbackQuery, session: AsyncSession, i18n_language=None):
    """Send course voice explanation"""
    course_id = int(callback.data.split("_")[-1])
    
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    
    if course and course.voice_file_id:
        await callback.message.answer_voice(voice=course.voice_file_id)

@router.callback_query(F.data.startswith("text_"))
async def show_course_text(callback: types.CallbackQuery, session: AsyncSession, i18n_language=None):
    """Show course text explanation"""
    course_id = int(callback.data.split("_")[-1])
    
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    
    if course and course.text_explanation:
        await callback.message.answer(
            f"{get_text('course.text_content', i18n_language)} {course.title}:\n\n{course.text_explanation}"
        )

@router.callback_query(F.data == "back_to_types")
async def back_to_types(callback: types.CallbackQuery, session: AsyncSession, i18n_language=None):
    """Return to course type selection"""
    course_types = await get_active_course_types(session)
    keyboard = get_course_type_keyboard(course_types, i18n_language)
    await callback.message.edit_text(get_text("course_type.select", i18n_language), reply_markup=keyboard)

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery, i18n_language=None):
    """Return to main menu"""
    # First delete the message with inline keyboard
    await callback.message.delete()
    
    # Then send a new message with reply keyboard
    await callback.message.answer(
        get_text("welcome_back", i18n_language),
        reply_markup=get_user_main_keyboard(i18n_language)
    )

@router.callback_query(F.data.startswith("back_to_courses_"))
async def back_to_courses(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Return to course list with previously selected difficulty level"""
    course_type_id = int(callback.data.split("_")[-1])
    
    # Get the stored difficulty level
    data = await state.get_data()
    difficulty = data.get("current_difficulty", "all")
    
    difficulty_level = None if difficulty == "all" else DifficultyLevel[difficulty]
    courses = await get_courses_by_type_and_difficulty(session, course_type_id, difficulty_level)
    
    if not courses:
        await callback.message.answer(
            get_text("course.no_available", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[[
                    types.InlineKeyboardButton(
                        text=get_text("buttons.back_to_types", i18n_language),
                        callback_data="back_to_types"
                    )
                ]]
            )
        )
        return
    
    keyboard = get_course_list_keyboard(courses, i18n_language, course_type_id)
    await callback.message.delete()
    await callback.message.answer(get_text("course.available", i18n_language), reply_markup=keyboard)

@router.callback_query(F.data.startswith("practice_"))
async def show_practice_image(callback: types.CallbackQuery, session: AsyncSession, i18n_language=None):
    """Show practice images with navigation"""
    parts = callback.data.split("_")
    course_id = int(parts[1])
    current_index = int(parts[2]) - 1  # Convert to 0-based index
    
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    
    if not course or not course.practice_images:
        await callback.answer(get_text("course.no_practice_images", i18n_language))
        return
    
    try:
        import json
        practice_images = json.loads(course.practice_images)
        
        if not practice_images:
            await callback.answer(get_text("course.no_practice_images", i18n_language))
            return
        
        # Ensure the index is valid
        total_images = len(practice_images)
        current_index = max(0, min(current_index, total_images - 1))
        
        # Build navigation keyboard
        keyboard = []
        nav_row = []
        
        # Previous button (if not first image)
        if current_index > 0:
            nav_row.append(
                types.InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"practice_{course_id}_{current_index}"
                )
            )
        
        # Image counter
        nav_row.append(
            types.InlineKeyboardButton(
                text=f"📸 {current_index + 1}/{total_images}",
                callback_data="noop"
            )
        )
        
        # Next button (if not last image)
        if current_index < total_images - 1:
            nav_row.append(
                types.InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"practice_{course_id}_{current_index + 2}"  # +2 because we need 1-based index in callback
                )
            )
        
        keyboard.append(nav_row)
        
        # Back button
        keyboard.append([
            types.InlineKeyboardButton(
                text=get_text("course.back_to_content", i18n_language),
                callback_data=f"course_{course_id}"
            )
        ])
        
        # Send or edit the image
        image_file_id = practice_images[current_index]
        caption = f"{get_text('course.practice_image', i18n_language)} {current_index + 1}/{total_images}"
        
        # If this is a fresh message, answer with new photo
        await callback.message.answer_photo(
            photo=image_file_id,
            caption=caption,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
    except (json.JSONDecodeError, IndexError) as e:
        await callback.answer(f"Error showing practice image: {str(e)}")
        
@router.callback_query(F.data == "noop")
async def noop_callback(callback: types.CallbackQuery):
    """Handle no-operation callback"""
    await callback.answer() 