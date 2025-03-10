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
