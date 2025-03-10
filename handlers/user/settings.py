from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.crud.user import update_user_language
from utils.i18n import get_text, get_all_translations_for_key
from keyboards.default.user_keyboard import main_menu_keyboard

router = Router()

@router.message(Command("settings"))
@router.message(F.text.in_(get_all_translations_for_key("buttons.settings")))
async def show_settings(message: Message, i18n_language: str):
    kb = InlineKeyboardBuilder()
    kb.button(text=get_text("user.language", i18n_language), callback_data="change_language")
    
    await message.answer(
        text=get_text("user.settings", i18n_language),
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "change_language")
async def show_language_selection(callback: CallbackQuery, i18n_language: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="Русский", callback_data="lang_ru")
    kb.button(text="O'zbek", callback_data="lang_uz")
    kb.adjust(2)
    
    await callback.message.edit_text(
        text=get_text("user.language", i18n_language),
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery, session, i18n_language: str):
    new_language = callback.data.split("_")[1]
    await update_user_language(session, callback.from_user.id, new_language)
    
    # Send new main menu keyboard with updated language
    await callback.message.answer(
        text=get_text("settings.language_changed", new_language),
        reply_markup=main_menu_keyboard(new_language)
    )
    
    # Update the settings message
    await callback.message.edit_text(
        text=get_text("user.settings", new_language),
        reply_markup=InlineKeyboardBuilder()
        .button(text=get_text("user.language", new_language), callback_data="change_language")
        .as_markup()
    ) 