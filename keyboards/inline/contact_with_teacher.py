from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def contact_with_teacher_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="✍️ Написать учителю", callback_data="russian_language", url='t.me/o101xd'),
    )
    builder.adjust(1)

    return builder.as_markup()
