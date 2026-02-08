from typing import Any, Optional
from aiogram.exceptions import TelegramNotFound
from sqlalchemy import select

from app.database.engine_base import async_session
from app.database.models.user_models import User
from app.database.requests.user_requests import get_user_data
from app.bot import get_bot


async def send_notification_by_id(user_id: int, send_content: str, sender_tg_id: int = None,
                                  reply_markup: Optional[Any] = None) -> bool:
    # Проверки входных данных
    if not isinstance(user_id, int) or user_id <= 0:
        return False
    if not isinstance(send_content, str) or not send_content.strip():
        return False

    # Получение пользователя из базы, проверки статусов
    try:
        user_data = await get_user_data(user_id)
        if not user_data:
            return False

        if user_data.get("is_banned") or user_data.get("is_deleted"):
            return False
        tg_id = user_data.get("tg_id")
        if not tg_id:
            return False
    except Exception:
        return False

    try:
        bot = get_bot()
    except RuntimeError:
        return False

    try:
        await bot.send_message(chat_id=tg_id, text=send_content, reply_markup=reply_markup)
    except TelegramNotFound:
        return False
    except Exception:
        return False

    return True
