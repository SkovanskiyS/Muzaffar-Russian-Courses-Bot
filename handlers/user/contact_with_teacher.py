from aiogram import Router, F
from aiogram.types import Message
from keyboards.inline.contact_with_teacher import contact_with_teacher_button
from utils.i18n import get_text, get_all_translations_for_key

router = Router()

@router.message(F.text.in_(get_all_translations_for_key("buttons.contact_teacher")))
async def contact_handler(message: Message, i18n_language: str):
    # Here you would typically get teacher info from database
    teacher_available = True  # This should be determined by your business logic
    
    if teacher_available:
        text = (
            f"{get_text('contact.teacher_info', i18n_language)}\n"
            f"{get_text('contact.contact_message', i18n_language)}\n"
            "@teacher_username"  # Replace with actual teacher contact
        )
    else:
        text = get_text('contact.no_teacher', i18n_language)
    
    await message.answer(text)
