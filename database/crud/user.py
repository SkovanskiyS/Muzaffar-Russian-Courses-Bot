from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models.user import Students

async def add_user(session: AsyncSession, user_id: int, username: str, fist_name: str, last_name: str | None):
    user = Students(user_id=user_id, username=username, first_name=fist_name, last_name=last_name)
    session.add(user)
    await session.commit()

async def get_user(session: AsyncSession, user_id: int):
    result = await session.execute(select(Students).where(Students.user_id == user_id))
    return result.scalars().first()
