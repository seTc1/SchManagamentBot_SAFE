from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReactionTypeEmoji
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.database.requests.code_requests import get_registration_code   
from app.database.requests.user_requests import get_user_by_tg_id

from app.database.models.user_models import UserRole

from app.keyboards.profile_keyboards import create_profile
from app.handlers.profile_handlers import cmd_profile

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    if not message.from_user.id:
        return
    if await get_user_by_tg_id(message.from_user.id):
        await cmd_profile(message)
        return
    await message.bot.set_message_reaction(
        chat_id=message.chat.id,
        message_id=message.message_id,
        reaction=[ReactionTypeEmoji(emoji="❤")]
    )
    await message.answer(
        "Привет! Это бот",
        reply_markup=create_profile
    )
