from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.types import ReplyKeyboardRemove
import json


from database.crud.courses import (
    create_course_type,
    create_course,
    get_course_type,
    update_course,
    delete_course
)
from database.models.courses import DifficultyLevel, CourseType
from keyboards.admin import (
    get_admin_main_keyboard,
    get_admin_course_keyboard,
    get_difficulty_keyboard,
    get_course_management_keyboard
)
from utils.i18n import get_text, get_all_translations_for_key

router = Router()

# Helper function to create a cancel keyboard
def get_cancel_keyboard(i18n_language=None) -> types.ReplyKeyboardMarkup:
    """Create a cancel keyboard with localized text"""
    keyboard = [[types.KeyboardButton(text=get_text("buttons.cancel", i18n_language))]]
    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False)

class CourseCreation(StatesGroup):
    waiting_for_type = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_banner = State()
    waiting_for_video = State()
    waiting_for_voice = State()
    waiting_for_text = State()
    waiting_for_practice_images = State()
    waiting_for_difficulty = State()
    waiting_for_order = State()

@router.message(F.text.in_(get_all_translations_for_key("course_type.add")))
async def cmd_add_course_type(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Handler for adding a new course type"""
    await message.answer(get_text("course_type.name", i18n_language), reply_markup=get_cancel_keyboard(i18n_language))
    await state.set_state("waiting_course_type_name")

@router.message(StateFilter("waiting_course_type_name"))
async def process_course_type_name(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Process the course type name"""
    # Check for cancel command
    if message.text == get_text("buttons.cancel", i18n_language):
        await state.clear()
        await message.answer(
            get_text("course.creation_cancelled", i18n_language),
            reply_markup=get_admin_main_keyboard(i18n_language)
        )
        return
        
    course_type = await create_course_type(session, name=message.text)
    success_message = get_text("course_type.created_success", i18n_language).format(name=course_type.name)
    await message.answer(
        success_message,
        reply_markup=get_admin_main_keyboard(i18n_language)
    )
    await state.clear()


@router.message(F.text.in_(get_all_translations_for_key("course.add")))
async def cmd_add_course(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Start the course creation process"""
    query = select(CourseType).filter(CourseType.is_active == True)
    result = await session.execute(query)
    course_types = result.scalars().all()
    
    if not course_types:
        await message.answer(
            get_text("course_type.no_types", i18n_language),
            reply_markup=get_admin_main_keyboard(i18n_language)
        )
        return
    
    keyboard = get_admin_course_keyboard(course_types, i18n_language)

    await message.answer(
        get_text("course_type.select", i18n_language),
        reply_markup=keyboard
    )
    await state.set_state(CourseCreation.waiting_for_type)

@router.callback_query(CourseCreation.waiting_for_type, F.data.startswith("course_type_"))
async def process_course_type_selection(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Process course type selection"""
    course_type_id = int(callback.data.split("_")[-1])
    await state.update_data(course_type_id=course_type_id)
    
    await callback.message.edit_text(get_text("course.add_title", i18n_language))
    # Send a new message with cancel keyboard
    await callback.message.answer("📚", reply_markup=get_cancel_keyboard(i18n_language))
    await state.set_state(CourseCreation.waiting_for_title)

@router.message(CourseCreation.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext, i18n_language=None):
    """Process course title"""
    # Check for cancel command
    if message.text == get_text("buttons.cancel", i18n_language):
        await cancel_course_creation_handler(message, state, i18n_language)
        return
        
    await state.update_data(title=message.text)
    await message.answer(get_text("course.add_description", i18n_language), reply_markup=get_cancel_keyboard(i18n_language))
    await state.set_state(CourseCreation.waiting_for_description)

@router.message(CourseCreation.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext, i18n_language=None):
    """Process course description"""
    # Check for cancel command
    if message.text == get_text("buttons.cancel", i18n_language):
        await cancel_course_creation_handler(message, state, i18n_language)
        return
        
    await state.update_data(description=message.text)
    await message.answer(get_text("course.add_banner", i18n_language), reply_markup=get_cancel_keyboard(i18n_language))
    await state.set_state(CourseCreation.waiting_for_banner)

@router.message(CourseCreation.waiting_for_banner, F.photo)
async def process_banner(message: types.Message, state: FSMContext, i18n_language=None):
    """Process course banner"""
    await state.update_data(banner_file_id=message.photo[-1].file_id)
    await message.answer(get_text("course.add_video", i18n_language), reply_markup=get_cancel_keyboard(i18n_language))
    await state.set_state(CourseCreation.waiting_for_video)

@router.message(CourseCreation.waiting_for_video, F.video)
async def process_video(message: types.Message, state: FSMContext, i18n_language=None):
    """Process course video"""
    await state.update_data(video_file_id=message.video.file_id)
    await message.answer(get_text("course.add_voice", i18n_language), reply_markup=get_cancel_keyboard(i18n_language))
    await state.set_state(CourseCreation.waiting_for_voice)

@router.message(CourseCreation.waiting_for_voice, F.voice)
async def process_voice(message: types.Message, state: FSMContext, i18n_language=None):
    """Process voice explanation"""
    await state.update_data(voice_file_id=message.voice.file_id)
    await message.answer(get_text("course.add_text", i18n_language), reply_markup=get_cancel_keyboard(i18n_language))
    await state.set_state(CourseCreation.waiting_for_text)

@router.message(CourseCreation.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext, i18n_language=None):
    """Process text explanation"""
    # Check for cancel command
    if message.text == get_text("buttons.cancel", i18n_language):
        await cancel_course_creation_handler(message, state, i18n_language)
        return
        
    await state.update_data(text_explanation=message.text)
    
    # Let's add the practice images step
    #await message.answer(get_text("course.add_practice_images", i18n_language))
    # Initialize empty list for practice images
    await state.update_data(practice_images=[])
    
    # Provide a finish button to end image collection
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=get_text("course.practice_finish_button", i18n_language))],
            [types.KeyboardButton(text=get_text("buttons.cancel", i18n_language))]
        ],
        resize_keyboard=True
    )
    #await message.answer(get_text("course.practice_send_or_finish", i18n_language), reply_markup=keyboard)
    await message.answer(get_text("course.add_practice_images", i18n_language), reply_markup=keyboard)
    await state.set_state(CourseCreation.waiting_for_practice_images)

@router.message(CourseCreation.waiting_for_practice_images, F.photo)
async def process_practice_image(message: types.Message, state: FSMContext, i18n_language=None):
    """Process practice image"""
    data = await state.get_data()
    practice_images = data.get("practice_images", [])
    
    # Add the new image file_id to the list
    practice_images.append(message.photo[-1].file_id)
    await state.update_data(practice_images=practice_images)
    
    # Let the user know how many images have been added
    confirmation_message = get_text("course.practice_image_added", i18n_language).format(number=len(practice_images))
    await message.answer(confirmation_message)

# Define the finish_practice_images function
async def finish_practice_images(message: types.Message, state: FSMContext, i18n_language=None):
    """Finish practice image collection"""
    data = await state.get_data()
    practice_images = data.get("practice_images", [])
    
    # Convert the list to JSON string
    await state.update_data(practice_images_json=json.dumps(practice_images))

    # Add cancel keyboard
    await message.answer("✅", reply_markup=get_cancel_keyboard(i18n_language))

    # Move to difficulty selection
    keyboard = get_difficulty_keyboard(i18n_language)
    await message.answer(
        get_text("course.select_difficulty", i18n_language), 
        reply_markup=keyboard
    )
    await state.set_state(CourseCreation.waiting_for_difficulty)

@router.message(CourseCreation.waiting_for_practice_images, F.text)
async def process_practice_image_text(message: types.Message, state: FSMContext, i18n_language=None):
    """Handle text commands during practice image collection"""
    if message.text == get_text("buttons.cancel", i18n_language):
        await cancel_course_creation_handler(message, state, i18n_language)
        return
    
    if message.text == get_text("course.practice_finish_button", i18n_language):
        await finish_practice_images(message, state, i18n_language)

@router.callback_query(CourseCreation.waiting_for_difficulty, F.data.startswith("difficulty_"))
async def process_difficulty(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Process difficulty selection"""
    difficulty = DifficultyLevel[callback.data.split("_")[-1]]
    await state.update_data(difficulty_level=difficulty)
    
    await callback.message.edit_text(get_text("course.enter_order", i18n_language))
    await state.set_state(CourseCreation.waiting_for_order)

@router.message(CourseCreation.waiting_for_order)
async def process_order(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Process order index and create the course"""
    # Check for cancel command
    if message.text == get_text("buttons.cancel", i18n_language):
        await cancel_course_creation_handler(message, state, i18n_language)
        return
        
    try:
        order_index = int(message.text)
        if not 1 <= order_index <= 40:
            raise ValueError
    except ValueError:
        await message.answer(get_text("course.invalid_order", i18n_language), reply_markup=get_cancel_keyboard(i18n_language))
        return
    
    data = await state.get_data()
    
    course = await create_course(
        db=session,
        course_type_id=data["course_type_id"],
        title=data["title"],
        description=data["description"],
        difficulty_level=data["difficulty_level"],
        order_index=order_index,
        banner_file_id=data["banner_file_id"],
        video_file_id=data["video_file_id"],
        voice_file_id=data["voice_file_id"],
        text_explanation=data["text_explanation"],
        practice_images=data.get("practice_images_json")
    )
    
    success_message = get_text("course.created_success", i18n_language).format(title=course.title)
    await message.answer(
        success_message,
        reply_markup=get_admin_main_keyboard(i18n_language)
    )
    await state.clear()

# Helper function for cancellation to reuse code
async def cancel_course_creation_handler(message: types.Message, state: FSMContext, i18n_language=None):
    """Cancel course creation process"""
    await state.clear()
    await message.answer(
        get_text("course.creation_cancelled", i18n_language),
        reply_markup=get_admin_main_keyboard(i18n_language)
    )

@router.callback_query(F.data == "cancel_course_creation")
async def cancel_course_creation(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Cancel course creation process"""
    await state.clear()
    await callback.message.edit_text(
        get_text("course.creation_cancelled", i18n_language)
    )
    await callback.message.answer(
        get_text("course.creation_cancelled", i18n_language), 
        reply_markup=get_admin_main_keyboard(i18n_language)
    ) 