from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


# def main_menu_keyboard() -> InlineKeyboardMarkup:
#     builder = InlineKeyboardBuilder()
#
#     builder.add(
#         InlineKeyboardButton(text="📚 Доступные курсы", callback_data="browse_courses"),
#         InlineKeyboardButton(text="💬 Связаться с учителем", callback_data="contact_teacher"),
#         InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")
#     )
#     builder.adjust(1)
#
#     return builder.as_markup()
