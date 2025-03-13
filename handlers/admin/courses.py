from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from aiogram.types import ReplyKeyboardRemove
from database.models.courses import Course
import json


from database.crud.courses import (
    create_course_type,
    create_course,
    get_course_type,
    get_courses_by_type,
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

class CourseManagement(StatesGroup):
    waiting_for_type = State()
    waiting_for_course = State()
    waiting_for_new_title = State()
    waiting_for_new_description = State()
    waiting_for_new_banner = State()
    waiting_for_new_video = State()
    waiting_for_new_voice = State()
    waiting_for_new_text = State()
    waiting_for_new_difficulty = State()
    waiting_for_new_order = State()
    confirm_delete = State()

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

@router.message(F.text.in_(get_all_translations_for_key("admin.course_management")))
async def cmd_course_management(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Handler for course management - show main management options first"""
    keyboard = [
        [
            types.InlineKeyboardButton(
                text=get_text("admin.manage_courses", i18n_language),
                callback_data="manage_courses"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("admin.manage_course_types", i18n_language),
                callback_data="manage_course_types"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("buttons.back_to_menu", i18n_language),
                callback_data="back_to_admin_menu"
            )
        ]
    ]
    
    await message.answer(
        get_text("admin.select_management_option", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data == "manage_courses")
async def manage_courses(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Show course types for course management"""
    query = select(CourseType).filter(CourseType.is_active == True)
    result = await session.execute(query)
    course_types = result.scalars().all()
    
    if not course_types:
        await callback.message.edit_text(
            get_text("course_type.no_types", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data="back_to_course_management"
                )
            ]])
        )
        return
    
    # Create a keyboard with course types
    keyboard = []
    for course_type in course_types:
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"📚 {course_type.name}",
                callback_data=f"manage_course_type_{course_type.id}"
            )
        ])
    
    keyboard.append([
        types.InlineKeyboardButton(
            text=get_text("buttons.back", i18n_language),
            callback_data="back_to_course_management"
        )
    ])
    
    await callback.message.edit_text(
        get_text("admin.select_course_type", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(CourseManagement.waiting_for_type)

@router.callback_query(F.data == "manage_course_types")
async def manage_course_types(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Handle the course types management"""
    
    # Get all course types
    query = select(CourseType)
    result = await session.execute(query)
    course_types = result.scalars().all()
    
    if not course_types:
        await callback.message.edit_text(
            get_text("course_type.no_types", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data="back_to_course_management"
                )
            ]])
        )
        return
    
    # Create keyboard with course types and actions
    keyboard = []
    for course_type in course_types:
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"📚 {course_type.name}",
                callback_data=f"select_course_type_{course_type.id}"
            )
        ])
        keyboard.append([
            types.InlineKeyboardButton(
                text=get_text("course_type.edit", i18n_language),
                callback_data=f"rename_course_type_{course_type.id}"
            ),
            types.InlineKeyboardButton(
                text=get_text("course_type.delete", i18n_language),
                callback_data=f"delete_type_course_{course_type.id}" 
            )
        ])
    
    keyboard.append([
        types.InlineKeyboardButton(
            text=get_text("buttons.back", i18n_language),
            callback_data="back_to_course_management"
        )
    ])
    
    await callback.message.edit_text(
        get_text("course_type.select", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data == "back_to_course_management")
async def back_to_course_management(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Return to course management main menu"""
    await cmd_course_management(callback.message, state, None, i18n_language)
    await callback.message.delete()

@router.callback_query(F.data.startswith("manage_course_type_"))
async def process_manage_course_type(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Show difficulty levels for selected course type"""
    course_type_id = int(callback.data.split("_")[-1])
    
    # Store the course type ID for later use
    await state.update_data(course_type_id=course_type_id)
    
    # Get the course type
    course_type = await get_course_type(session, course_type_id)
    if not course_type:
        await callback.message.edit_text(
            get_text("course_type.not_found", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back_to_menu", i18n_language),
                    callback_data="back_to_admin_menu"
                )
            ]])
        )
        return
    
    # Create a keyboard with difficulty levels
    keyboard = []
    
    # Add a button for each difficulty level
    for level in DifficultyLevel:
        difficulty_text = get_text(f"course.difficulty.{level.name.lower()}", i18n_language)
        keyboard.append([
            types.InlineKeyboardButton(
                text=difficulty_text,
                callback_data=f"manage_course_difficulty_{course_type_id}_{level.name}"
            )
        ])
    
    # Add an "All levels" option
    keyboard.append([
        types.InlineKeyboardButton(
            text=get_text("course.difficulty.all", i18n_language),
            callback_data=f"manage_course_difficulty_{course_type_id}_ALL"
        )
    ])
    
    # Add back button
    keyboard.append([
        types.InlineKeyboardButton(
            text=get_text("buttons.back", i18n_language),
            callback_data="back_to_course_types_management"
        )
    ])
    
    await callback.message.edit_text(
        get_text("course.select_difficulty", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(CourseManagement.waiting_for_type)

@router.callback_query(F.data.startswith("manage_course_difficulty_"))
async def process_manage_course_difficulty(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Show courses for selected type and difficulty"""
    parts = callback.data.split("_")
    course_type_id = int(parts[3])
    difficulty = parts[4]
    
    # Store the course type ID for later use
    await state.update_data(course_type_id=course_type_id)
    await state.update_data(selected_difficulty=difficulty)
    
    # Get the course type
    course_type = await get_course_type(session, course_type_id)
    if not course_type:
        await callback.message.edit_text(
            get_text("course_type.not_found", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back_to_menu", i18n_language),
                    callback_data="back_to_admin_menu"
                )
            ]])
        )
        return
    
    # Get courses for this type and difficulty
    query = select(Course).filter(Course.course_type_id == course_type_id, Course.is_active == True)
    
    # Filter by difficulty if not "ALL"
    if difficulty != "ALL":
        query = query.filter(Course.difficulty_level == DifficultyLevel[difficulty])
    
    # Order by order_index
    query = query.order_by(Course.order_index)
    
    result = await session.execute(query)
    courses = result.scalars().all()
    
    if not courses:
        await callback.message.edit_text(
            get_text("course.no_courses_to_manage", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"manage_course_type_{course_type_id}"
                )
            ]])
        )
        return
    
    # Create a keyboard with courses
    keyboard = []
    for course in courses:
        difficulty_text = get_text(f"course.difficulty.{course.difficulty_level.name.lower()}", i18n_language)
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"{course.title} ({difficulty_text}, #{course.order_index})",
                callback_data=f"manage_course_{course.id}"
            )
        ])
    
    keyboard.append([
        types.InlineKeyboardButton(
            text=get_text("buttons.back", i18n_language),
            callback_data=f"manage_course_type_{course_type_id}"
        )
    ])
    
    # Get the title for the message based on difficulty
    if difficulty == "ALL":
        title = get_text("admin.select_course", i18n_language)
    else:
        difficulty_text = get_text(f"course.difficulty.{difficulty.lower()}", i18n_language)
        title = get_text("admin.select_course_with_difficulty", i18n_language).format(
            difficulty=difficulty_text
        )
    
    await callback.message.edit_text(
        title,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(CourseManagement.waiting_for_course)

@router.callback_query(F.data.startswith("manage_course_"))
async def process_manage_course(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Show management options for selected course"""
    course_id = int(callback.data.split("_")[-1])
    
    # Store the course ID for later use
    await state.update_data(course_id=course_id)
    
    # Reset state to waiting_for_course to ensure consistency
    await state.set_state(CourseManagement.waiting_for_course)
    
    # Get the course
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    
    if not course:
        await callback.message.edit_text(
            get_text("course.not_found", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data="back_to_course_management"
                )
            ]])
        )
        return
    
    # Send course info
    difficulty_text = get_text(f"course.difficulty.{course.difficulty_level.name.lower()}", i18n_language)
    print(difficulty_text)
    course_info = (
        f"{get_text('course.title', i18n_language)}: {course.title}\n"
        f"📊 {get_text('course.difficulty_title', i18n_language)}: {difficulty_text}\n"
        f"🔢 {get_text('course.order', i18n_language)}: {course.order_index}\n\n"
        f"{get_text('course.description', i18n_language)}:\n{course.description}\n\n"
        f"{get_text('course.text_explanation', i18n_language)}:\n{course.text_explanation[:200]}..."
    )
    
    if course.banner_file_id:
        await callback.message.answer_photo(
            photo=course.banner_file_id,
            caption=course_info
        )
    else:
        await callback.message.edit_text(course_info)
    
    # Show management options
    keyboard = get_course_management_keyboard(course_id, i18n_language)
    await callback.message.answer(
        get_text("admin.course_management_options", i18n_language),
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("edit_course_"))
async def edit_course_menu(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Show edit options for the course"""
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(course_id=course_id)
    
    # Reset the state to waiting_for_course to ensure back button works after cancellation
    await state.set_state(CourseManagement.waiting_for_course)
    
    keyboard = [
        [
            types.InlineKeyboardButton(
                text=get_text("course.edit_title", i18n_language),
                callback_data=f"edit_title_{course_id}"
            ),
            types.InlineKeyboardButton(
                text=get_text("course.edit_description", i18n_language),
                callback_data=f"edit_description_{course_id}"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("course.edit_banner", i18n_language),
                callback_data=f"edit_banner_{course_id}"
            ),
            types.InlineKeyboardButton(
                text=get_text("course.edit_video", i18n_language),
                callback_data=f"edit_video_{course_id}"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("course.edit_voice", i18n_language),
                callback_data=f"edit_voice_{course_id}"
            ),
            types.InlineKeyboardButton(
                text=get_text("course.edit_text", i18n_language),
                callback_data=f"edit_text_{course_id}"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("buttons.back", i18n_language),
                callback_data=f"manage_course_{course_id}"
            )
        ]
    ]
    
    await callback.message.edit_text(
        get_text("admin.select_what_to_edit", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@router.callback_query(F.data.startswith("delete_course_"))
async def delete_course_confirmation(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Ask for confirmation before deleting a course"""
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(course_id=course_id)
    
    keyboard = [
        [
            types.InlineKeyboardButton(
                text=get_text("buttons.confirm", i18n_language),
                callback_data=f"confirm_delete_{course_id}"
            ),
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data=f"manage_course_{course_id}"
            )
        ]
    ]
    
    await callback.message.edit_text(
        get_text("admin.confirm_delete_course", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(CourseManagement.confirm_delete)

@router.callback_query(CourseManagement.confirm_delete, F.data.startswith("confirm_delete_"))
async def confirm_delete_course(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Handle course deletion confirmation"""
    course_id = int(callback.data.split("_")[-1])
    
    # Get course data for messages
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    
    if not course:
        await callback.message.edit_text(
            get_text("course.not_found", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back_to_menu", i18n_language),
                    callback_data="back_to_admin_menu"
                )
            ]])
        )
        return
    
    course_title = course.title
    
    # Delete the course
    success = await delete_course(session, course_id)
    
    if success:
        await callback.message.edit_text(
            get_text("admin.course_deleted", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back_to_menu", i18n_language),
                    callback_data="back_to_admin_menu"
                )
            ]])
        )
    else:
        await callback.message.edit_text(
            get_text("admin.delete_failed", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"manage_course_{course_id}"
                )
            ]])
        )
    
    await state.clear()

@router.callback_query(F.data.startswith("change_difficulty_"))
async def change_difficulty(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Show difficulty selection for changing course difficulty"""
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(course_id=course_id)
    
    # Reset the state to waiting_for_course to ensure back button works after cancellation
    await state.set_state(CourseManagement.waiting_for_course)
    
    keyboard = []
    difficulty_texts = {
        DifficultyLevel.BEGINNER: get_text("course.difficulty.beginner", i18n_language),
        DifficultyLevel.INTERMEDIATE: get_text("course.difficulty.intermediate", i18n_language),
        DifficultyLevel.ADVANCED: get_text("course.difficulty.advanced", i18n_language),
        DifficultyLevel.EXPERT: get_text("course.difficulty.expert", i18n_language)
    }
    
    for level in DifficultyLevel:
        keyboard.append([
            types.InlineKeyboardButton(
                text=difficulty_texts[level],
                callback_data=f"set_difficulty_{course_id}_{level.name}"
            )
        ])
    
    keyboard.append([
        types.InlineKeyboardButton(
            text=get_text("buttons.back", i18n_language),
            callback_data=f"manage_course_{course_id}"
        )
    ])
    
    await callback.message.edit_text(
        get_text("admin.select_new_difficulty", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(CourseManagement.waiting_for_new_difficulty)

@router.callback_query(CourseManagement.waiting_for_new_difficulty, F.data.startswith("set_difficulty_"))
async def set_difficulty(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Update course difficulty"""
    parts = callback.data.split("_")
    course_id = int(parts[2])
    difficulty = DifficultyLevel[parts[3]]
    
    # Get course before update for message
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    course_title = course.title if course else ""
    
    # Update the course
    updated_course = await update_course(
        session,
        course_id,
        difficulty_level=difficulty
    )
    
    # Reset the state to waiting_for_course to ensure back button works after update
    await state.set_state(CourseManagement.waiting_for_course)
    
    if updated_course:
        difficulty_text = get_text(f"course.difficulty.{difficulty.name.lower()}", i18n_language)
        await callback.message.edit_text(
            get_text("admin.difficulty_updated", i18n_language).format(
                title=course_title,
                difficulty=difficulty_text
            ),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"manage_course_{course_id}"
                )
            ]])
        )
    else:
        await callback.message.edit_text(
            get_text("admin.update_failed", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"manage_course_{course_id}"
                )
            ]])
        )

@router.callback_query(F.data.startswith("change_order_"))
async def change_order(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Prompt for a new order index"""
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(course_id=course_id)
    
    await callback.message.edit_text(
        get_text("admin.enter_new_order", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data=f"manage_course_{course_id}"
            )
        ]])
    )
    await state.set_state(CourseManagement.waiting_for_new_order)

@router.message(CourseManagement.waiting_for_new_order)
async def process_new_order(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Process new order index"""
    try:
        order_index = int(message.text)
    except ValueError:
        data = await state.get_data()
        course_id = data.get("course_id")
        await message.answer(
            get_text("course.invalid_order", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.try_again", i18n_language),
                    callback_data=f"change_order_{course_id}"
                ),
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"manage_course_{course_id}"
                )
            ]])
        )
        return
            
    data = await state.get_data()
    course_id = data.get("course_id")
    
    # Get course before update for message
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    course_title = course.title if course else ""
    old_order = course.order_index if course else 0
    
    # Update the course
    updated_course = await update_course(
        session,
        course_id,
        order_index=order_index
    )
    
    if updated_course:
        await message.answer(
            get_text("admin.order_updated", i18n_language).format(
                title=course_title,
                old_order=old_order,
                new_order=order_index
            ),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"manage_course_{course_id}"
                )
            ]])
        )
    else:
        await message.answer(
            get_text("admin.update_failed", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"manage_course_{course_id}"
                )
            ]])
        )

# Navigation handlers
@router.callback_query(F.data == "back_to_admin_menu")
async def back_to_admin_menu(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Return to admin menu"""
    # Get the correct language from callback if not explicitly provided
    if not i18n_language:
        i18n_language = callback.from_user.language_code
        
    await state.clear()
    await callback.message.edit_text(
        get_text("admin.back_to_menu", i18n_language)
    )
    await callback.message.answer(
        get_text("admin.welcome", i18n_language),
        reply_markup=get_admin_main_keyboard(i18n_language)
    )

@router.callback_query(F.data == "back_to_course_types_management")
async def back_to_course_types_management(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Return to course types selection for management"""
    await cmd_course_management(callback.message, state, session, i18n_language)

@router.callback_query(F.data == "cancel_course_management")
async def cancel_course_management(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Cancel course management"""
    await state.clear()
    await callback.message.edit_text(
        get_text("admin.management_cancelled", i18n_language),
    )
    await callback.message.answer(
        get_text("admin.welcome", i18n_language),
        reply_markup=get_admin_main_keyboard(i18n_language)
    )

@router.callback_query(F.data.startswith("edit_title_"))
async def edit_title(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Prompt for new course title"""
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(course_id=course_id)
    
    await callback.message.edit_text(
        get_text("admin.enter_new_title", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data=f"edit_course_{course_id}"
            )
        ]])
    )
    await state.set_state(CourseManagement.waiting_for_new_title)

@router.message(CourseManagement.waiting_for_new_title)
async def process_new_title(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Process new course title"""
    if not message.text or len(message.text.strip()) < 3:
        data = await state.get_data()
        course_id = data.get("course_id")
        await message.answer(
            get_text("admin.title_too_short", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.try_again", i18n_language),
                    callback_data=f"edit_title_{course_id}"
                ),
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )
        return
    
    data = await state.get_data()
    course_id = data.get("course_id")
    
    # Get course before update for message
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    old_title = course.title if course else ""
    new_title = message.text.strip()
    
    # Update the course title
    updated_course = await update_course(
        session,
        course_id,
        title=new_title
    )
    
    if updated_course:
        await message.answer(
            get_text("admin.title_updated", i18n_language).format(
                old_title=old_title,
                new_title=new_title
            ),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )
    else:
        await message.answer(
            get_text("admin.update_failed", i18n_language).format(title=old_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )

@router.callback_query(F.data.startswith("edit_description_"))
async def edit_description(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Prompt for new course description"""
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(course_id=course_id)
    
    await callback.message.edit_text(
        get_text("admin.enter_new_description", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data=f"edit_course_{course_id}"
            )
        ]])
    )
    await state.set_state(CourseManagement.waiting_for_new_description)

@router.message(CourseManagement.waiting_for_new_description)
async def process_new_description(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Process new course description"""
    if not message.text or len(message.text.strip()) < 10:
        data = await state.get_data()
        course_id = data.get("course_id")
        await message.answer(
            get_text("admin.description_too_short", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.try_again", i18n_language),
                    callback_data=f"edit_description_{course_id}"
                ),
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )
        return
    
    data = await state.get_data()
    course_id = data.get("course_id")
    
    # Get course before update for message
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    course_title = course.title if course else ""
    
    # Update the course description
    updated_course = await update_course(
        session,
        course_id,
        description=message.text.strip()
    )
    
    if updated_course:
        await message.answer(
            get_text("admin.description_updated", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )
    else:
        await message.answer(
            get_text("admin.update_failed", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )

@router.callback_query(F.data.startswith("edit_banner_"))
async def edit_banner(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Prompt for new course banner"""
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(course_id=course_id)
    
    await callback.message.edit_text(
        get_text("admin.send_new_banner", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data=f"edit_course_{course_id}"
            )
        ]])
    )
    await state.set_state(CourseManagement.waiting_for_new_banner)

@router.message(CourseManagement.waiting_for_new_banner, F.photo)
async def process_new_banner(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Process new course banner"""
    data = await state.get_data()
    course_id = data.get("course_id")
    
    # Get course before update for message
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    course_title = course.title if course else ""
    
    # Update the course banner
    updated_course = await update_course(
        session,
        course_id,
        banner_file_id=message.photo[-1].file_id
    )
    
    if updated_course:
        await message.answer(
            get_text("admin.banner_updated", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )
    else:
        await message.answer(
            get_text("admin.update_failed", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )

@router.message(CourseManagement.waiting_for_new_banner)
async def process_invalid_banner(message: types.Message, state: FSMContext, i18n_language=None):
    """Handle invalid input for banner"""
    data = await state.get_data()
    course_id = data.get("course_id")
    
    await message.answer(
        get_text("admin.send_photo_please", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.try_again", i18n_language),
                callback_data=f"edit_banner_{course_id}"
            ),
            types.InlineKeyboardButton(
                text=get_text("buttons.back", i18n_language),
                callback_data=f"edit_course_{course_id}"
            )
        ]])
    )

@router.callback_query(F.data.startswith("edit_video_"))
async def edit_video(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Prompt for new course video"""
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(course_id=course_id)
    
    await callback.message.edit_text(
        get_text("admin.send_new_video", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data=f"edit_course_{course_id}"
            )
        ]])
    )
    await state.set_state(CourseManagement.waiting_for_new_video)

@router.message(CourseManagement.waiting_for_new_video, F.video)
async def process_new_video(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Process new course video"""
    data = await state.get_data()
    course_id = data.get("course_id")
    
    # Get course before update for message
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    course_title = course.title if course else ""
    
    # Update the course video
    updated_course = await update_course(
        session,
        course_id,
        video_file_id=message.video.file_id
    )
    
    if updated_course:
        await message.answer(
            get_text("admin.video_updated", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )
    else:
        await message.answer(
            get_text("admin.update_failed", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )

@router.message(CourseManagement.waiting_for_new_video)
async def process_invalid_video(message: types.Message, state: FSMContext, i18n_language=None):
    """Handle invalid input for video"""
    data = await state.get_data()
    course_id = data.get("course_id")
    
    await message.answer(
        get_text("admin.send_video_please", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.try_again", i18n_language),
                callback_data=f"edit_video_{course_id}"
            ),
            types.InlineKeyboardButton(
                text=get_text("buttons.back", i18n_language),
                callback_data=f"edit_course_{course_id}"
            )
        ]])
    )

@router.callback_query(F.data.startswith("edit_voice_"))
async def edit_voice(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Prompt for new course voice"""
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(course_id=course_id)
    
    await callback.message.edit_text(
        get_text("admin.send_new_voice", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data=f"edit_course_{course_id}"
            )
        ]])
    )
    await state.set_state(CourseManagement.waiting_for_new_voice)

@router.message(CourseManagement.waiting_for_new_voice, F.voice)
async def process_new_voice(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Process new course voice"""
    data = await state.get_data()
    course_id = data.get("course_id")
    
    # Get course before update for message
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    course_title = course.title if course else ""
    
    # Update the course voice
    updated_course = await update_course(
        session,
        course_id,
        voice_file_id=message.voice.file_id
    )
    
    if updated_course:
        await message.answer(
            get_text("admin.voice_updated", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )
    else:
        await message.answer(
            get_text("admin.update_failed", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )

@router.message(CourseManagement.waiting_for_new_voice)
async def process_invalid_voice(message: types.Message, state: FSMContext, i18n_language=None):
    """Handle invalid input for voice"""
    data = await state.get_data()
    course_id = data.get("course_id")
    
    await message.answer(
        get_text("admin.send_voice_please", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.try_again", i18n_language),
                callback_data=f"edit_voice_{course_id}"
            ),
            types.InlineKeyboardButton(
                text=get_text("buttons.back", i18n_language),
                callback_data=f"edit_course_{course_id}"
            )
        ]])
    )

@router.callback_query(F.data.startswith("edit_text_"))
async def edit_text(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Prompt for new course text"""
    course_id = int(callback.data.split("_")[-1])
    await state.update_data(course_id=course_id)
    
    await callback.message.edit_text(
        get_text("admin.enter_new_text", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data=f"edit_course_{course_id}"
            )
        ]])
    )
    await state.set_state(CourseManagement.waiting_for_new_text)

@router.message(CourseManagement.waiting_for_new_text)
async def process_new_text(message: types.Message, state: FSMContext, session: AsyncSession, i18n_language=None):
    """Process new course text"""
    if not message.text or len(message.text.strip()) < 10:
        data = await state.get_data()
        course_id = data.get("course_id")
        await message.answer(
            get_text("admin.text_too_short", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.try_again", i18n_language),
                    callback_data=f"edit_text_{course_id}"
                ),
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )
        return
    
    data = await state.get_data()
    course_id = data.get("course_id")
    
    # Get course before update for message
    query = select(Course).filter(Course.id == course_id)
    result = await session.execute(query)
    course = result.scalar_one_or_none()
    course_title = course.title if course else ""
    
    # Update the course text
    updated_course = await update_course(
        session,
        course_id,
        text_explanation=message.text.strip()
    )
    
    if updated_course:
        await message.answer(
            get_text("admin.text_updated", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )
    else:
        await message.answer(
            get_text("admin.update_failed", i18n_language).format(title=course_title),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data=f"edit_course_{course_id}"
                )
            ]])
        )

# Handler for editing course type
@router.message(F.text.in_(get_all_translations_for_key("course_type.edit")))
async def edit_course_type_command(message: types.Message, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Handle the edit course type command"""
    
    # Get all course types
    query = select(CourseType)
    result = await session.execute(query)
    course_types = result.scalars().all()
    
    if not course_types:
        await message.answer(
            get_text("course_type.no_types", i18n_language),
            reply_markup=get_admin_main_keyboard(i18n_language)
        )
        return
    
    # Create keyboard with course types and actions
    keyboard = []
    for course_type in course_types:
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"📚 {course_type.name}",
                callback_data=f"select_course_type_{course_type.id}"
            )
        ])
        keyboard.append([
            types.InlineKeyboardButton(
                text=get_text("course_type.edit", i18n_language), # Use translation instead of hardcoded Russian text
                callback_data=f"rename_course_type_{course_type.id}"
            ),
            types.InlineKeyboardButton(
                text=get_text("course_type.delete", i18n_language), # Use translation instead of hardcoded Russian text
                callback_data=f"delete_type_course_{course_type.id}" 
            )
        ])
    
    keyboard.append([
        types.InlineKeyboardButton(
            text=get_text("buttons.cancel", i18n_language),
            callback_data="cancel_course_type_edit"
        )
    ])
    
    await message.answer(
        get_text("course_type.select", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

# Handler for renaming course type
@router.callback_query(F.data.startswith("rename_course_type_"))
async def rename_course_type(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Handle renaming of course type"""
    course_type_id = int(callback.data.split("_")[-1])
    
    await state.set_state("waiting_for_course_type_name")
    await state.update_data(course_type_id=course_type_id)
    
    await callback.message.edit_text(
        get_text("course_type.name", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data="cancel_course_type_edit"
            )
        ]])
    )
    await callback.answer()

# Handler for receiving new course type name
@router.message(StateFilter("waiting_for_course_type_name"))
async def process_new_course_type_name(message: types.Message, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Process the new name for course type"""
    data = await state.get_data()
    course_type_id = data.get("course_type_id")
    
    if len(message.text.strip()) < 3:
        await message.answer(
            get_text("admin.title_too_short", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.try_again", i18n_language),
                    callback_data=f"rename_course_type_{course_type_id}"
                )
            ]])
        )
        return
    
    # Update course type name
    query = update(CourseType).where(CourseType.id == course_type_id).values(name=message.text.strip())
    await session.execute(query)
    await session.commit()
    
    await state.clear()
    
    await message.answer(
        get_text("course_type.updated_success", i18n_language).format(name=message.text.strip()),
        reply_markup=get_admin_main_keyboard(i18n_language)
    )

# Handler for deleting course type
@router.callback_query(F.data.startswith("delete_type_course_"))
async def delete_course_type(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Ask for confirmation before deleting a course type"""
    course_type_id = int(callback.data.split("_")[-1])
    await state.update_data(course_type_id=course_type_id)
    
    # Get course type to show name
    query = select(CourseType).filter(CourseType.id == course_type_id)
    result = await session.execute(query)
    course_type = result.scalar_one_or_none()
    
    if not course_type:
        await callback.message.edit_text(
            get_text("course_type.not_found", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back_to_menu", i18n_language),
                    callback_data="back_to_admin_menu"
                )
            ]])
        )
        return
        
    # Create inline keyboard for confirmation
    keyboard = [
        [
            types.InlineKeyboardButton(
                text=get_text("buttons.confirm", i18n_language),
                callback_data=f"confirm_delete_type_{course_type_id}"
            ),
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data="cancel_course_type_edit"
            )
        ]
    ]
    
    # Make sure we're using InlineKeyboardMarkup for edit_text
    inline_keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    # Use course_type-specific confirmation message
    confirmation_message = get_text("course_type.confirm_delete", i18n_language)
    
    await callback.message.edit_text(
        text=confirmation_message,
        reply_markup=inline_keyboard
    )
    
    await state.set_state("confirm_delete_type")
    await callback.answer()

@router.callback_query(StateFilter("confirm_delete_type"), F.data.startswith("confirm_delete_type_"))
async def confirm_delete_course_type(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Handle course type deletion after confirmation"""
    course_type_id = int(callback.data.split("_")[-1])
    
    # Get course type name before deletion
    query = select(CourseType).filter(CourseType.id == course_type_id)
    result = await session.execute(query)
    course_type = result.scalar_one_or_none()
    
    if course_type:
        # Delete the course type
        delete_query = delete(CourseType).where(CourseType.id == course_type_id)
        await session.execute(delete_query)  
        await session.commit()
        
        await callback.message.edit_text(
            get_text("course_type.deleted", i18n_language).format(title=course_type.name),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back_to_menu", i18n_language),
                    callback_data="back_to_admin_menu"
                )
            ]])
        )
    else:
        await callback.message.edit_text(
            get_text("course_type.not_found", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back_to_menu", i18n_language),
                    callback_data="back_to_admin_menu"
                )
            ]])
        )
    
    await state.clear()
    await callback.answer()

# Handler for canceling course type edit
@router.callback_query(F.data == "cancel_course_type_edit")
async def cancel_course_type_edit(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Handle cancellation of course type editing"""
    
    await state.clear()
    
    await callback.message.edit_text(
        get_text("admin.management_cancelled", i18n_language)
    )
    
    await callback.message.answer(
        get_text("admin.back_to_menu", i18n_language),
        reply_markup=get_admin_main_keyboard(i18n_language)
    )
    await callback.answer()
