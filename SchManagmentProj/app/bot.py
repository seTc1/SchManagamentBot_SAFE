
from typing import Optional
from aiogram import Bot

_bot: Optional[Bot] = None


def init_bot(token: str) -> Bot:
    """Инициализировать и вернуть глобальный Bot. Вызывать один раз при старте приложения."""
    global _bot
    if _bot is None:
        _bot = Bot(token=token)
    return _bot


def get_bot() -> Bot:
    """Вернуть инициализированный Bot. Вызывает ошибку, если бот не инициализирован."""
    if _bot is None:
        raise RuntimeError("Bot is not initialized. Call init_bot(token) before using get_bot().")
    return _bot


async def close_bot() -> None:
    """Закрыть сессию бота и обнулить глобальную переменную."""
    global _bot
    if _bot is not None:
        await _bot.session.close()
        _bot = None
