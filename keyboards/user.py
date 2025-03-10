from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Optional
from database.models.courses import CourseType, Course, DifficultyLevel
from utils.i18n import get_text

def get_user_main_keyboard(language: Optional[str] = None) -> ReplyKeyboardMarkup:
    """Create main user keyboard"""
    keyboard = [
        [
            KeyboardButton(text=get_text("buttons.courses", language)),
        ],
        [
            KeyboardButton(text=get_text("buttons.about_us", language)),
            KeyboardButton(text=get_text("buttons.settings", language))
        ],
        [
            KeyboardButton(text=get_text("buttons.contact_teacher", language))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_course_type_keyboard(course_types: List[CourseType], language: Optional[str] = None) -> InlineKeyboardMarkup:
    """Create keyboard for course type selection"""
    keyboard = []
    for course_type in course_types:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📚 {course_type.name}",
                callback_data=f"view_course_type_{course_type.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=get_text("buttons.back_to_menu", language),
            callback_data="back_to_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_difficulty_selection_keyboard(course_type_id: int, language: Optional[str] = None) -> InlineKeyboardMarkup:
    """Create keyboard for difficulty level selection"""
    keyboard = []
    
    difficulty_texts = {
        DifficultyLevel.BEGINNER: get_text("course.difficulty.beginner", language),
        DifficultyLevel.INTERMEDIATE: get_text("course.difficulty.intermediate", language),
        DifficultyLevel.ADVANCED: get_text("course.difficulty.advanced", language),
        DifficultyLevel.EXPERT: get_text("course.difficulty.expert", language)
    }
    
    for level in DifficultyLevel:
        keyboard.append([
            InlineKeyboardButton(
                text=difficulty_texts[level],
                callback_data=f"difficulty_{course_type_id}_{level.name}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=get_text("course.difficulty.all", language),
            callback_data=f"difficulty_{course_type_id}_all"
        )
    ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=get_text("buttons.back_to_types", language),
            callback_data="back_to_types"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_course_list_keyboard(courses: List[Course], language: Optional[str] = None, course_type_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Create keyboard for course list"""
    keyboard = []
    for course in courses:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📚 {course.order_index}. {course.title}",
                callback_data=f"course_{course.id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text=get_text("buttons.back", language),
            callback_data=f"view_course_type_{course_type_id}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_course_content_keyboard(course_id: int, course_type_id: int, language: Optional[str] = None) -> InlineKeyboardMarkup:
    """Create keyboard for course content"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("course.watch_video", language),
                callback_data=f"video_{course_id}"
            ),
            InlineKeyboardButton(
                text=get_text("course.listen_voice", language),
                callback_data=f"voice_{course_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("course.text_content", language),
                callback_data=f"text_{course_id}"
            ),
            InlineKeyboardButton(
                text=get_text("course.practice_images", language),
                callback_data=f"practice_{course_id}_1"  # Start with first image
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("course.back_to_list", language),
                callback_data=f"back_to_courses_{course_type_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 