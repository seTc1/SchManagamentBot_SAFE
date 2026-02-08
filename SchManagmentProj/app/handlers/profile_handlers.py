from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from typing import Optional

from app.database.models.user_models import UserRole
from app.database.requests.user_requests import get_user_data, create_user, get_user_by_tg_id

from app.keyboards.profile_keyboards import standard_profile, admin_profile

router = Router()


async def send_profile(message: Message, text: str, keyboard, new_message: bool = False):
    try:
        if (
                message.content_type == "text"
                and message.from_user.id == message.bot.id
                and not new_message
        ):
            await message.edit_text(text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)
    except TelegramBadRequest:
        await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "create_profile")
async def create_profile(callback: CallbackQuery):
    if await get_user_by_tg_id(callback.from_user.id):
        await callback.answer("Пользователь уже существует. Профиль не создан.")
        return
    await create_user(callback.from_user.id)
    await callback.bot.send_message(text="Профиль успешно создан!", chat_id=callback.message.chat.id)
    await cmd_profile(callback.message, user_id=callback.from_user.id, new_message=True)
    await callback.answer()


@router.message(Command("profile"))
async def cmd_profile(message: Message, user_id: Optional[int] = None, new_message: bool = False):
    user_object = await get_user_by_tg_id(user_id if user_id else message.from_user.id)
    user_data = await get_user_data(user_object.id)

    role = user_data.get("role")

    if role == UserRole.user:
        text = (f"Твой профиль:\n"
                f"Роль: Пользователь\n")
        await send_profile(message, text, standard_profile, new_message)
    elif role == UserRole.student:
        text = (f"Твой профиль:\n"
                f"Роль: Ученик\n")
        await send_profile(message, text, standard_profile, new_message)
    elif role == UserRole.teacher:
        text = (f"Твой профиль:\n"
                f"Роль: Учитель: {user_data['full_name']}")
        await send_profile(message, text, admin_profile, new_message)
    elif role == UserRole.management:
        text = (f"Твой профиль:\n"
                f"Роль: Управление [{user_data['user_desc']}]")
        await send_profile(message, text, admin_profile, new_message)
    elif role == UserRole.admin:
        text = (f"Твой профиль:\n"
                f"Роль: Крутой классный админ")
        await send_profile(message, text, admin_profile, new_message)
    else:
        print(role)
        await send_profile(message, "Неизвестная роль пользователя", keyboard=ReplyKeyboardRemove())


@router.callback_query(F.data == "profile")
async def callback_profile(callback: CallbackQuery):
    if not callback.message:
        return
    await cmd_profile(callback.message, user_id=callback.from_user.id)
    await callback.answer()
