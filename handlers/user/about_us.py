from aiogram import Router, F
from aiogram.types import Message
from utils.i18n import get_text, get_all_translations_for_key

router = Router()

@router.message(F.text.in_(get_all_translations_for_key("buttons.about_us")))
async def about_handler(message: Message, i18n_language: str):
    text = f"{get_text('about.title', i18n_language)}\n\n{get_text('about.description', i18n_language)}"
    await message.answer(text)