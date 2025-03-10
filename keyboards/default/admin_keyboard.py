from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.i18n import get_text, DEFAULT_LANGUAGE


def admin_main_menu_keyboard(language: str = DEFAULT_LANGUAGE) -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text=get_text("admin.course_management", language))
        ],
        [
            KeyboardButton(text=get_text("admin.add_course", language)),
            KeyboardButton(text=get_text("admin.edit_course", language))
        ],
        [
            KeyboardButton(text=get_text("admin.delete_course", language))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
