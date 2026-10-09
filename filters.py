from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram import Bot

from config import OWNER_ID
from database import get_role


class IsModerator(BaseFilter):
    """Пропускает владельца бота, Telegram-админов и назначенных модеров."""

    async def __call__(self, message: Message, bot: Bot) -> bool:
        if message.from_user is None:
            return False
        user_id = message.from_user.id
        chat_id = message.chat.id

        # владелец бота — везде модер
        if user_id == OWNER_ID:
            return True

        # назначенный модер в БД
        role = await get_role(chat_id, user_id)
        if role in ("moderator", "admin", "owner"):
            return True

        # Telegram-админ в чате
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status in ("creator", "administrator"):
                return True
        except Exception:
            pass

        return False


class IsAdmin(BaseFilter):
    """Пропускает владельца бота и Telegram-админов чата. Только для /setrole."""

    async def __call__(self, message: Message, bot: Bot) -> bool:
        if message.from_user is None:
            return False
        user_id = message.from_user.id
        chat_id = message.chat.id

        if user_id == OWNER_ID:
            return True

        role = await get_role(chat_id, user_id)
        if role in ("admin", "owner"):
            return True

        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status in ("creator", "administrator"):
                return True
        except Exception:
            pass

        return False