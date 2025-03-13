from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.user import (
    get_user,
    get_admin_students,
    add_admin,
    remove_admin,
    check_if_admin
)
from keyboards.admin import get_admin_main_keyboard
from utils.i18n import get_text, get_all_translations_for_key
from config import settings

router = Router()

class AdminManagement(StatesGroup):
    viewing_admins = State()
    adding_admin = State()
    removing_admin = State()
    confirming_remove = State()


@router.message(F.text.in_(get_all_translations_for_key("admin.admin_management")))
async def admin_management_command(message: types.Message, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Handle the admin management command"""
    # Get all admins
    admins = await get_admin_students(session)
    
    # Create the admin management keyboard
    keyboard = [
        [
            types.InlineKeyboardButton(
                text=get_text("admin.admin_list", i18n_language).format(count=len(admins)),
                callback_data="list_admins"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("admin.add_admin", i18n_language),
                callback_data="add_admin"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("admin.remove_admin", i18n_language),
                callback_data="remove_admin"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("buttons.back_to_menu", i18n_language),
                callback_data="back_to_admin_menu"
            )
        ]
    ]
    
    await message.answer(
        get_text("admin.admin_management", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(AdminManagement.viewing_admins)


@router.callback_query(F.data == "list_admins")
async def list_admins(callback: types.CallbackQuery, session: AsyncSession, i18n_language=None):
    """List all admins"""
    admins = await get_admin_students(session)
    
    if not admins:
        await callback.message.edit_text(
            get_text("admin.no_admins", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back_to_menu", i18n_language),
                    callback_data="back_to_admin_menu"
                )
            ]])
        )
        return
    
    # Create admin list message
    admin_list_text = f"{get_text('admin.admin_list', i18n_language).format(count=len(admins))}\n\n"
    
    for admin in admins:
        full_name = admin.first_name
        if admin.last_name:
            full_name += f" {admin.last_name}"
        
        admin_info = f"• {full_name} (ID: {admin.user_id})"
        if admin.username:
            admin_info += f" @{admin.username}"
        
        admin_list_text += f"{admin_info}\n"
    
    # Create keyboard
    keyboard = [[
        types.InlineKeyboardButton(
            text=get_text("buttons.back", i18n_language),
            callback_data="back_to_admin_management"
        )
    ]]
    
    await callback.message.edit_text(
        admin_list_text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data == "add_admin")
async def add_admin_request(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Request admin ID to add"""
    await state.set_state(AdminManagement.adding_admin)
    await callback.message.edit_text(
        get_text("admin.enter_admin_id", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data="back_to_admin_management"
            )
        ]])
    )
    await callback.answer()


@router.message(AdminManagement.adding_admin)
async def process_add_admin(message: types.Message, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Process adding a new admin"""
    try:
        user_id = int(message.text)
        
        # Check if user exists
        user = await get_user(session, user_id)
        if not user:
            await message.answer(
                get_text("admin.user_not_found", i18n_language).format(id=user_id),
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(
                        text=get_text("buttons.back", i18n_language),
                        callback_data="back_to_admin_management"
                    )
                ]])
            )
            return
        
        # Check if user is already an admin
        if user.is_admin:
            await message.answer(
                get_text("admin.already_admin", i18n_language).format(id=user_id),
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(
                        text=get_text("buttons.back", i18n_language),
                        callback_data="back_to_admin_management"
                    )
                ]])
            )
            return
        
        # Make user an admin
        await add_admin(session, user_id)
        
        # Format user name
        full_name = user.first_name
        if user.last_name:
            full_name += f" {user.last_name}"
        
        await message.answer(
            f"{get_text('admin.admin_added', i18n_language).format(id=user_id)}\n\n"
            f"{full_name}" + (f" (@{user.username})" if user.username else ""),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data="back_to_admin_management"
                )
            ]])
        )
        
        # Go back to admin management state
        await state.set_state(AdminManagement.viewing_admins)
        
    except ValueError:
        await message.answer(
            get_text("admin.invalid_admin_id", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data="back_to_admin_management"
                )
            ]])
        )


@router.callback_query(F.data == "remove_admin")
async def remove_admin_request(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Show list of admins to remove"""
    admins = await get_admin_students(session)
    
    if not admins or len(admins) <= 1:
        await callback.message.edit_text(
            get_text("admin.no_admins", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data="back_to_admin_management"
                )
            ]])
        )
        return
    
    # Create keyboard with admins
    keyboard = []
    
    for admin in admins:
        # Skip the current user (can't remove yourself)
        if admin.user_id == callback.from_user.id:
            continue
            
        full_name = admin.first_name
        if admin.last_name:
            full_name += f" {admin.last_name}"
            
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"{full_name}" + (f" (@{admin.username})" if admin.username else ""),
                callback_data=f"confirm_remove_{admin.user_id}"
            )
        ])
    
    # Add back button
    keyboard.append([
        types.InlineKeyboardButton(
            text=get_text("buttons.back", i18n_language),
            callback_data="back_to_admin_management"
        )
    ])
    
    if not keyboard or len(keyboard) == 1:
        # Only the back button is present, no admins to remove
        await callback.message.edit_text(
            get_text("admin.no_admins", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data="back_to_admin_management"
                )
            ]])
        )
        return
        
    await callback.message.edit_text(
        get_text("admin.select_admin_to_remove", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(AdminManagement.removing_admin)
    await callback.answer()


@router.callback_query(AdminManagement.removing_admin, F.data.startswith("confirm_remove_"))
async def confirm_remove_admin(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Confirm removing an admin"""
    user_id = int(callback.data.split("_")[-1])
    
    # Check if user is trying to remove themselves
    if user_id == callback.from_user.id:
        await callback.answer(get_text("admin.cant_remove_yourself", i18n_language))
        return
    
    # Get the admin
    user = await get_user(session, user_id)
    
    if not user:
        await callback.answer(get_text("admin.user_not_found", i18n_language).format(id=user_id))
        return
    
    if not user.is_admin:
        await callback.answer(get_text("admin.not_admin", i18n_language).format(id=user_id))
        return
    
    # Format admin name
    full_name = user.first_name
    if user.last_name:
        full_name += f" {user.last_name}"
    
    # Save the user_id for confirmation
    await state.update_data(admin_to_remove=user_id, admin_name=full_name)
    
    # Create confirmation keyboard
    keyboard = [
        [
            types.InlineKeyboardButton(
                text=get_text("buttons.confirm", i18n_language),
                callback_data=f"remove_admin_{user_id}"
            ),
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data="back_to_admin_management"
            )
        ]
    ]
    
    await callback.message.edit_text(
        get_text("admin.confirm_remove_admin", i18n_language).format(name=full_name),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(AdminManagement.confirming_remove)
    await callback.answer()


@router.callback_query(AdminManagement.confirming_remove, F.data.startswith("remove_admin_"))
async def process_remove_admin(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Process removing an admin"""
    user_id = int(callback.data.split("_")[-1])
    
    # Check if user is trying to remove themselves
    if user_id == callback.from_user.id:
        await callback.answer(get_text("admin.cant_remove_yourself", i18n_language))
        return
    
    # Remove admin status
    user = await remove_admin(session, user_id)
    
    if not user:
        await callback.answer(get_text("admin.user_not_found", i18n_language).format(id=user_id))
        return
    
    # Format user name
    full_name = user.first_name
    if user.last_name:
        full_name += f" {user.last_name}"
    
    await callback.message.edit_text(
        f"{get_text('admin.admin_removed', i18n_language).format(id=user_id)}\n\n"
        f"{full_name}" + (f" (@{user.username})" if user.username else ""),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.back", i18n_language),
                callback_data="back_to_admin_management"
            )
        ]])
    )
    await state.set_state(AdminManagement.viewing_admins)


@router.callback_query(F.data == "back_to_admin_management")
async def back_to_admin_management(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Return to admin management main menu"""
    # Get all admins
    admins = await get_admin_students(session)
    
    # Create the admin management keyboard
    keyboard = [
        [
            types.InlineKeyboardButton(
                text=get_text("admin.admin_list", i18n_language).format(count=len(admins)),
                callback_data="list_admins"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("admin.add_admin", i18n_language),
                callback_data="add_admin"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("admin.remove_admin", i18n_language),
                callback_data="remove_admin"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("buttons.back_to_menu", i18n_language),
                callback_data="back_to_admin_menu"
            )
        ]
    ]
    
    await callback.message.edit_text(
        get_text("admin.admin_management", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(AdminManagement.viewing_admins)
    await callback.answer()


@router.callback_query(F.data == "back_to_admin_menu")
async def back_to_admin_menu(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Return to admin menu"""
    # Use the language from the callback if not provided
    if not i18n_language:
        i18n_language = callback.from_user.language_code
        
    await state.clear()
    await callback.message.edit_text(
        get_text("admin.back_to_menu", i18n_language)
    )
    await callback.message.answer(
        get_text("admin.welcome", i18n_language),
        reply_markup=get_admin_main_keyboard(i18n_language)
    )
    await callback.answer() 