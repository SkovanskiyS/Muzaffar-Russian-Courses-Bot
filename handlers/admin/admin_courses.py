from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.orm import Session

from database.crud.courses import (
    create_course_type,
    create_course,
    get_course_type,
    update_course,
    delete_course
)
from database.models.courses import DifficultyLevel, CourseType
from keyboards.admin import get_admin_course_keyboard
from database.db import get_db
from utils.i18n import get_all_translations_for_key

router = Router()

class CourseCreation(StatesGroup):
    waiting_for_type = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_banner = State()
    waiting_for_video = State()
    waiting_for_voice = State()
    waiting_for_text = State()
    waiting_for_difficulty = State()
    waiting_for_order = State()

@router.message(F.text.in_(get_all_translations_for_key("admin.add_course")))
async def cmd_add_course_type(message: types.Message, state: FSMContext):
    """Handler for adding a new course type"""
    await message.answer("Please send me the name of the course type (e.g. 'Basic Russian Course')")
    await state.set_state("waiting_course_type_name")

@router.message(StateFilter("waiting_course_type_name"))
async def process_course_type_name(message: types.Message, state: FSMContext):
    """Process the course type name"""
    db: Session = next(get_db())
    course_type = create_course_type(db, name=message.text)
    await message.answer(f"Course type '{course_type.name}' has been created successfully!")
    await state.clear()

@router.message(Command("add_course"))
async def cmd_add_course(message: types.Message, state: FSMContext):
    """Start the course creation process"""
    db: Session = next(get_db())
    course_types = db.query(CourseType).filter(CourseType.is_active == True).all()
    
    if not course_types:
        await message.answer("No course types available. Please create a course type first using /add_course_type")
        return
    
    keyboard = get_admin_course_keyboard(course_types)
    await message.answer("Please select the course type:", reply_markup=keyboard)
    await state.set_state(CourseCreation.waiting_for_type)

@router.callback_query(CourseCreation.waiting_for_type, F.data.startswith("course_type_"))
async def process_course_type_selection(callback: types.CallbackQuery, state: FSMContext):
    """Process course type selection"""
    course_type_id = int(callback.data.split("_")[-1])
    await state.update_data(course_type_id=course_type_id)
    
    await callback.message.edit_text("Please send the title of the course:")
    await state.set_state(CourseCreation.waiting_for_title)

@router.message(CourseCreation.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    """Process course title"""
    await state.update_data(title=message.text)
    await message.answer("Please send the course description:")
    await state.set_state(CourseCreation.waiting_for_description)

@router.message(CourseCreation.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    """Process course description"""
    await state.update_data(description=message.text)
    await message.answer("Please send the course banner image:")
    await state.set_state(CourseCreation.waiting_for_banner)

@router.message(CourseCreation.waiting_for_banner, F.photo)
async def process_banner(message: types.Message, state: FSMContext):
    """Process course banner"""
    await state.update_data(banner_file_id=message.photo[-1].file_id)
    await message.answer("Please send the course video content:")
    await state.set_state(CourseCreation.waiting_for_video)

@router.message(CourseCreation.waiting_for_video, F.video)
async def process_video(message: types.Message, state: FSMContext):
    """Process course video"""
    await state.update_data(video_file_id=message.video.file_id)
    await message.answer("Please send the voice explanation:")
    await state.set_state(CourseCreation.waiting_for_voice)

@router.message(CourseCreation.waiting_for_voice, F.voice)
async def process_voice(message: types.Message, state: FSMContext):
    """Process voice explanation"""
    await state.update_data(voice_file_id=message.voice.file_id)
    await message.answer("Please send the text explanation:")
    await state.set_state(CourseCreation.waiting_for_text)

@router.message(CourseCreation.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext):
    """Process text explanation"""
    await state.update_data(text_explanation=message.text)
    
    # Create difficulty level keyboard
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text=level.value.title(), callback_data=f"difficulty_{level.name}")
                for level in DifficultyLevel
            ]
        ]
    )
    
    await message.answer("Please select the difficulty level:", reply_markup=keyboard)
    await state.set_state(CourseCreation.waiting_for_difficulty)

@router.callback_query(CourseCreation.waiting_for_difficulty, F.data.startswith("difficulty_"))
async def process_difficulty(callback: types.CallbackQuery, state: FSMContext):
    """Process difficulty selection"""
    difficulty = DifficultyLevel[callback.data.split("_")[-1]]
    await state.update_data(difficulty_level=difficulty)
    
    await callback.message.edit_text("Please send the order index (1-40):")
    await state.set_state(CourseCreation.waiting_for_order)

@router.message(CourseCreation.waiting_for_order)
async def process_order(message: types.Message, state: FSMContext):
    """Process order index and create the course"""
    try:
        order_index = int(message.text)
        if not 1 <= order_index <= 40:
            raise ValueError
    except ValueError:
        await message.answer("Please send a valid number between 1 and 40")
        return
    
    data = await state.get_data()
    db: Session = next(get_db())
    
    course = create_course(
        db=db,
        course_type_id=data["course_type_id"],
        title=data["title"],
        description=data["description"],
        difficulty_level=data["difficulty_level"],
        order_index=order_index,
        banner_file_id=data["banner_file_id"],
        video_file_id=data["video_file_id"],
        voice_file_id=data["voice_file_id"],
        text_explanation=data["text_explanation"]
    )
    
    await message.answer(f"Course '{course.title}' has been created successfully!")
    await state.clear() 