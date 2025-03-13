from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.models.user import Students
from database.crud.user import (
    get_all_students,
    get_paid_students,
    get_unpaid_students,
    update_payment_status
)
from keyboards.admin import get_admin_main_keyboard
from utils.i18n import get_text, get_all_translations_for_key

router = Router()

class StudentManagement(StatesGroup):
    viewing_students = State()
    viewing_student = State()
    entering_student_id = State()


@router.message(F.text.in_(get_all_translations_for_key("student.management")))
async def student_management_command(message: types.Message, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Handle the student management command"""
    # Get counts for each student category
    all_students = await get_all_students(session)
    paid_students = await get_paid_students(session)
    unpaid_students = await get_unpaid_students(session)
    
    all_count = len(all_students)
    paid_count = len(paid_students)
    unpaid_count = len(unpaid_students)
    
    # Create the student management keyboard
    keyboard = [
        [
            types.InlineKeyboardButton(
                text=get_text("student.all_students", i18n_language).format(count=all_count),
                callback_data="students_all"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("student.paid_students", i18n_language).format(count=paid_count),
                callback_data="students_paid"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("student.unpaid_students", i18n_language).format(count=unpaid_count),
                callback_data="students_unpaid"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("student.enter_id", i18n_language),
                callback_data="enter_student_id"
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
        get_text("student.management", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(StudentManagement.viewing_students)


@router.callback_query(StudentManagement.viewing_students, F.data.startswith("students_"))
async def process_students_list(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Process the students list selection"""
    # Get page from callback data if it exists (format: students_type_page)
    parts = callback.data.split("_")
    students_type = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 1
    items_per_page = 10  # Number of students per page
    
    # Get students based on selection
    if students_type == "all":
        students = await get_all_students(session)
        title = get_text("student.all_students", i18n_language).format(count=len(students))
    elif students_type == "paid":
        students = await get_paid_students(session)
        title = get_text("student.paid_students", i18n_language).format(count=len(students))
    elif students_type == "unpaid":
        students = await get_unpaid_students(session)
        title = get_text("student.unpaid_students", i18n_language).format(count=len(students))
    else:
        await callback.answer(get_text("student.invalid_selection", i18n_language))
        return
    
    # Save the type for future reference
    await state.update_data(students_type=students_type)
    
    if not students:
        await callback.message.edit_text(
            get_text("student.no_students", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back_to_menu", i18n_language),
                    callback_data="back_to_admin_menu"
                )
            ]])
        )
        return
    
    # Calculate pagination
    total_pages = (len(students) + items_per_page - 1) // items_per_page
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    current_page_students = students[start_idx:end_idx]
    
    # Create a keyboard with the students for current page
    keyboard = []
    for student in current_page_students:
        display_name = student.first_name
        if student.last_name:
            display_name += f" {student.last_name}"
            
        # Add an indicator for paid status
        status_emoji = "✅" if student.is_paid else "❌"
        
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"{status_emoji} {display_name} (@{student.username or get_text('student.no_username', i18n_language)})",
                callback_data=f"view_student_{student.user_id}"
            )
        ])
    
    # Add pagination controls
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            types.InlineKeyboardButton(
                text="◀️",
                callback_data=f"students_{students_type}_{page-1}"
            )
        )
    
    pagination_buttons.append(
        types.InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="ignore"
        )
    )
    
    if page < total_pages:
        pagination_buttons.append(
            types.InlineKeyboardButton(
                text="▶️",
                callback_data=f"students_{students_type}_{page+1}"
            )
        )
    
    keyboard.append(pagination_buttons)
    
    # Add back button
    keyboard.append([
        types.InlineKeyboardButton(
            text=get_text("buttons.back", i18n_language),
            callback_data="back_to_student_management"
        )
    ])
    
    # Update the title to show pagination info
    title = f"{title}\n{get_text('student.page_info', i18n_language).format(current=page, total=total_pages)}"
    
    await callback.message.edit_text(
        f"{title}\n{get_text('student.select_student', i18n_language)}",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    """Handle the ignore callback for the page number button"""
    await callback.answer()


@router.callback_query(StudentManagement.viewing_students, F.data.startswith("view_student_"))
async def view_student(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """View a specific student's details"""
    user_id = int(callback.data.split("_")[-1])
    
    # Get the student
    result = await session.execute(select(Students).where(Students.user_id == user_id))
    student = result.scalars().first()
    
    if not student:
        await callback.answer(get_text("student.student_not_found", i18n_language))
        return
    
    # Save the student ID for future reference
    await state.update_data(student_id=user_id)
    
    # Format student information
    full_name = student.first_name
    if student.last_name:
        full_name += f" {student.last_name}"
    
    # Get payment status and other status texts
    payment_status = get_text("student.payment_status_paid", i18n_language) if student.is_paid else get_text("student.payment_status_unpaid", i18n_language)
    admin_status = get_text("student.admin_status_yes", i18n_language) if student.is_admin else get_text("student.admin_status_no", i18n_language)
    blocked_status = get_text("student.blocked_status_yes", i18n_language) if student.is_blocked else get_text("student.blocked_status_no", i18n_language)
    
    # Create student info message
    student_info = (
        f"{get_text('student.student_info', i18n_language)}\n\n"
        f"{get_text('student.id', i18n_language).format(id=student.user_id)}\n"
        f"{get_text('student.name', i18n_language).format(name=full_name)}\n"
    )
    
    if student.username:
        student_info += f"{get_text('student.username', i18n_language).format(username=student.username)}\n"
    
    student_info += (
        f"{get_text('student.language', i18n_language).format(language=student.language)}\n"
        f"{get_text('student.payment_status', i18n_language).format(status=payment_status)}\n"
        f"{get_text('student.admin_status', i18n_language).format(status=admin_status)}\n"
        f"{get_text('student.blocked_status', i18n_language).format(status=blocked_status)}\n"
    )
    
    # Create keyboard for actions
    keyboard = []
    
    # Add payment status change button
    if student.is_paid:
        keyboard.append([
            types.InlineKeyboardButton(
                text=get_text("student.change_to_unpaid", i18n_language),
                callback_data=f"change_payment_{user_id}_false"
            )
        ])
    else:
        keyboard.append([
            types.InlineKeyboardButton(
                text=get_text("student.change_to_paid", i18n_language),
                callback_data=f"change_payment_{user_id}_true"
            )
        ])
    
    # Add back button
    data = await state.get_data()
    students_type = data.get("students_type", "all")
    keyboard.append([
        types.InlineKeyboardButton(
            text=get_text("student.back_to_list", i18n_language),
            callback_data=f"students_{students_type}"
        )
    ])
    
    await callback.message.edit_text(
        student_info,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(StudentManagement.viewing_student)
    await callback.answer()


@router.callback_query(StudentManagement.viewing_student, F.data.startswith("change_payment_"))
async def change_payment_status(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Change a student's payment status"""
    parts = callback.data.split("_")
    user_id = int(parts[2])
    is_paid = parts[3] == "true"
    
    # Update the payment status
    student = await update_payment_status(session, user_id, is_paid)
    
    if not student:
        await callback.answer(get_text("student.student_not_found", i18n_language))
        return
    
    # Get status text
    status_text = get_text("student.payment_status_paid", i18n_language) if is_paid else get_text("student.payment_status_unpaid", i18n_language)
    
    # Format student name
    full_name = student.first_name
    if student.last_name:
        full_name += f" {student.last_name}"
    
    # Notify about successful change
    await callback.answer(
        get_text("student.payment_status_changed", i18n_language).format(
            name=full_name,
            status=status_text
        )
    )
    
    # Go back to viewing the student with updated info
    callback.data = f"view_student_{user_id}"
    await view_student(callback, session, state, i18n_language)


@router.callback_query(F.data == "back_to_student_management")
async def back_to_student_management(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Return to student management main menu"""
    
    # Get counts for each student category
    all_students = await get_all_students(session)
    paid_students = await get_paid_students(session)
    unpaid_students = await get_unpaid_students(session)
    
    all_count = len(all_students)
    paid_count = len(paid_students)
    unpaid_count = len(unpaid_students)
    
    # Create the student management keyboard
    keyboard = [
        [
            types.InlineKeyboardButton(
                text=get_text("student.all_students", i18n_language).format(count=all_count),
                callback_data="students_all"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("student.paid_students", i18n_language).format(count=paid_count),
                callback_data="students_paid"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("student.unpaid_students", i18n_language).format(count=unpaid_count),
                callback_data="students_unpaid"
            )
        ],
        [
            types.InlineKeyboardButton(
                text=get_text("student.enter_id", i18n_language),
                callback_data="enter_student_id"
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
        get_text("student.management", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(StudentManagement.viewing_students)
    await callback.answer()


@router.callback_query(F.data == "back_to_admin_menu")
async def back_to_admin_menu_from_students(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Return to admin menu from student management"""
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


@router.callback_query(StudentManagement.viewing_student, F.data.startswith("students_"))
async def back_to_students_list(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Handle going back to the students list from student details"""
    # First set the state back to viewing_students
    await state.set_state(StudentManagement.viewing_students)
    # Then process the students list
    await process_students_list(callback, session, state, i18n_language)


@router.callback_query(F.data == "enter_student_id")
async def request_student_id(callback: types.CallbackQuery, state: FSMContext, i18n_language=None):
    """Handle the request to enter a student ID manually"""
    await state.set_state(StudentManagement.entering_student_id)
    await callback.message.edit_text(
        get_text("student.enter_id_prompt", i18n_language),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(
                text=get_text("buttons.cancel", i18n_language),
                callback_data="back_to_student_management"
            )
        ]])
    )
    await callback.answer()


@router.message(StudentManagement.entering_student_id)
async def process_student_id(message: types.Message, session: AsyncSession, state: FSMContext, i18n_language=None):
    """Process the entered student ID"""
    try:
        user_id = int(message.text)
        # Try to find the student
        result = await session.execute(select(Students).where(Students.user_id == user_id))
        student = result.scalars().first()
        
        if not student:
            await message.answer(
                get_text("student.not_found", i18n_language),
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton(
                        text=get_text("buttons.back", i18n_language),
                        callback_data="back_to_student_management"
                    )
                ]])
            )
            return
        
        # Format student information
        full_name = student.first_name
        if student.last_name:
            full_name += f" {student.last_name}"
        
        # Get payment status and other status texts
        payment_status = get_text("student.payment_status_paid", i18n_language) if student.is_paid else get_text("student.payment_status_unpaid", i18n_language)
        admin_status = get_text("student.admin_status_yes", i18n_language) if student.is_admin else get_text("student.admin_status_no", i18n_language)
        blocked_status = get_text("student.blocked_status_yes", i18n_language) if student.is_blocked else get_text("student.blocked_status_no", i18n_language)
        
        # Create student info message
        student_info = (
            f"{get_text('student.student_info', i18n_language)}\n\n"
            f"{get_text('student.id', i18n_language).format(id=student.user_id)}\n"
            f"{get_text('student.name', i18n_language).format(name=full_name)}\n"
        )
        
        if student.username:
            student_info += f"{get_text('student.username', i18n_language).format(username=student.username)}\n"
        
        student_info += (
            f"{get_text('student.language', i18n_language).format(language=student.language)}\n"
            f"{get_text('student.payment_status', i18n_language).format(status=payment_status)}\n"
            f"{get_text('student.admin_status', i18n_language).format(status=admin_status)}\n"
            f"{get_text('student.blocked_status', i18n_language).format(status=blocked_status)}\n"
        )
        
        # Create keyboard for actions
        keyboard = []
        
        # Add payment status change button
        if student.is_paid:
            keyboard.append([
                types.InlineKeyboardButton(
                    text=get_text("student.change_to_unpaid", i18n_language),
                    callback_data=f"change_payment_{user_id}_false"
                )
            ])
        else:
            keyboard.append([
                types.InlineKeyboardButton(
                    text=get_text("student.change_to_paid", i18n_language),
                    callback_data=f"change_payment_{user_id}_true"
                )
            ])
        
        # Add back button
        keyboard.append([
            types.InlineKeyboardButton(
                text=get_text("buttons.back", i18n_language),
                callback_data="back_to_student_management"
            )
        ])
        
        await message.answer(
            student_info,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await state.set_state(StudentManagement.viewing_student)
        
    except ValueError:
        await message.answer(
            get_text("student.invalid_id", i18n_language),
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(
                    text=get_text("buttons.back", i18n_language),
                    callback_data="back_to_student_management"
                )
            ]])
        ) 