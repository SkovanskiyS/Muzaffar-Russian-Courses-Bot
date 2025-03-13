from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models.user import Students
from utils.i18n import LanguageCode

async def add_user(session: AsyncSession, user_id: int, username: str, first_name: str, last_name: str | None, language: str = "ru"):
    user = Students(
        user_id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        language=language
    )
    session.add(user)
    await session.commit()

async def get_user(session: AsyncSession, user_id: int):
    result = await session.execute(select(Students).where(Students.user_id == user_id))
    return result.scalars().first()

async def update_user_language(session: AsyncSession, user_id: int, language: str):
    user = await get_user(session, user_id)
    if user:
        user.language = language
        await session.commit()
    return user

async def get_all_students(session: AsyncSession):
    """Get all students from the database"""
    result = await session.execute(select(Students))
    return result.scalars().all()

async def get_paid_students(session: AsyncSession):
    """Get only students who have paid"""
    result = await session.execute(select(Students).where(Students.is_paid == True))
    return result.scalars().all()

async def get_unpaid_students(session: AsyncSession):
    """Get only students who haven't paid"""
    result = await session.execute(select(Students).where(Students.is_paid == False))
    return result.scalars().all()

async def update_payment_status(session: AsyncSession, user_id: int, is_paid: bool):
    """Update a student's payment status"""
    user = await get_user(session, user_id)
    if user:
        user.is_paid = is_paid
        await session.commit()
    return user

async def get_admin_students(session: AsyncSession):
    """Get only admin students"""
    result = await session.execute(select(Students).where(Students.is_admin == True))
    return result.scalars().all()

async def add_admin(session: AsyncSession, user_id: int):
    """Make a student an admin"""
    user = await get_user(session, user_id)
    if user:
        user.is_admin = True
        await session.commit()
    return user

async def remove_admin(session: AsyncSession, user_id: int):
    """Remove admin status from a student"""
    user = await get_user(session, user_id)
    if user:
        user.is_admin = False
        await session.commit()
    return user

async def check_if_admin(session: AsyncSession, user_id: int):
    """Check if a user is an admin"""
    user = await get_user(session, user_id)
    if user:
        return user.is_admin
    return False
