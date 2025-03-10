from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def courses_type() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="russian_language"),
    )
    builder.adjust(1)

    return builder.as_markup()
