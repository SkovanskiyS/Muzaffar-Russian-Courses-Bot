from aiogram.filters import BaseFilter
from aiogram.types import Message
from database.crud.user import check_if_admin


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message, session) -> bool:
        # Only check database for admin status
        return await check_if_admin(session, message.from_user.id)
