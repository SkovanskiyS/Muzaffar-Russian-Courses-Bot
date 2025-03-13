from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Optional
from database.models.courses import CourseType, DifficultyLevel
from utils.i18n import get_text

def get_admin_main_keyboard(language: Optional[str] = None) -> ReplyKeyboardMarkup:
    """Create main admin keyboard"""
    keyboard = [
        [
            KeyboardButton(text=get_text("course.add", language)),
        ],
        [
            KeyboardButton(text=get_text("admin.course_management", language)),
            KeyboardButton(text=get_text("student.management", language))
        ],
        [
            KeyboardButton(text=get_text("course_type.add", language)),
        ],
        [
            KeyboardButton(text=get_text("admin.admin_management", language))
        ],
        [
            KeyboardButton(text=get_text("buttons.settings", language))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_admin_course_keyboard(course_types: List[CourseType], language: Optional[str] = None) -> InlineKeyboardMarkup:
    """Create keyboard for course type selection"""
    keyboard = []
    for course_type in course_types:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📚 {course_type.name}",
                callback_data=f"course_type_{course_type.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=get_text("buttons.cancel", language),
            callback_data="cancel_course_creation"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_difficulty_keyboard(language: Optional[str] = None) -> InlineKeyboardMarkup:
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
                callback_data=f"difficulty_{level.name}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=get_text("buttons.cancel", language),
            callback_data="cancel_course_creation"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_course_management_keyboard(course_id: int, language: Optional[str] = None) -> InlineKeyboardMarkup:
    """Create keyboard for course management"""
    keyboard = [
        [
            InlineKeyboardButton(
                text=get_text("admin.edit_course", language),
                callback_data=f"edit_course_{course_id}"
            ),
            InlineKeyboardButton(
                text=get_text("admin.delete_course", language),
                callback_data=f"delete_course_{course_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("course.change_difficulty", language),
                callback_data=f"change_difficulty_{course_id}"
            ),
            InlineKeyboardButton(
                text=get_text("course.change_order", language),
                callback_data=f"change_order_{course_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text=get_text("buttons.cancel", language),
                callback_data="cancel_course_management"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 