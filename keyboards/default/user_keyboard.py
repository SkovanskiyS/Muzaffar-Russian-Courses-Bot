from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.i18n import get_text, DEFAULT_LANGUAGE


def main_menu_keyboard(language: str = DEFAULT_LANGUAGE) -> ReplyKeyboardMarkup:
    kb = [
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
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
