import re
from typing import Callable, Dict, Any, Awaitable, Iterable, Pattern, Union, List
from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject
from app.database.requests.user_requests import get_user_by_tg_id

AllowedPattern = Union[str, Pattern]


class RegistrationBarrier(BaseMiddleware):
    def __init__(
            self,
            *,
            allowed_commands: Iterable[str] = (),
            allowed_callback_patterns: Iterable[AllowedPattern] = (),
            blocked_message_text: str = "Ваш профиль не создан. Для информации /start"
    ):
        super().__init__()
        self.allowed_commands = {cmd.lstrip("/").lower() for cmd in allowed_commands}
        self.allowed_callback_patterns: List[Pattern] = []
        for pattern in allowed_callback_patterns:
            if isinstance(pattern, str):
                if pattern.startswith("^") or pattern.endswith("$") or any(ch in pattern for ch in ".*+?[]()"):
                    self.allowed_callback_patterns.append(re.compile(pattern))
                else:
                    self.allowed_callback_patterns.append(re.compile(f"^{re.escape(pattern)}$"))
            else:
                self.allowed_callback_patterns.append(pattern)
        self.blocked_message_text = blocked_message_text

    def _callback_allowed(self, data: str) -> bool:
        if not data:
            return False
        for pattern in self.allowed_callback_patterns:
            if pattern.search(data):
                return True
        return False

    def _message_command(self, message: types.Message) -> Union[str, None]:
        text = (message.text or "").strip()
        if not text:
            return None
        if not text.startswith("/"):
            return None
        cmd = text.split()[0].lstrip("/").lower()
        return cmd

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user_id = getattr(getattr(event, "from_user", None), "id", None)
        if not user_id:
            return await handler(event, data)

        user = await get_user_by_tg_id(user_id)
        if user:
            if getattr(user, "is_banned", False):
                # Попытка уведомить пользователя о блокировке (если доступно)
                ans = getattr(event, "answer", None)
                if ans:
                    try:
                        await ans("Ваш аккаунт заблокирован. Обратитесь к администратору.")
                    except Exception:
                        pass
                return None
            return await handler(event, data)

        state = data.get("state")
        current_state = None
        if state:
            current_state = await state.get_state()

        # MESSAGE
        if isinstance(event, types.Message):
            # если команда и она в белом списке — разрешаем
            cmd = self._message_command(event)
            if cmd:
                if cmd in self.allowed_commands:
                    return await handler(event, data)
                # команда, но не разрешена -> блокируем
                await event.answer(self.blocked_message_text)
                return None

            # обычный текст
            # если пользователь в состоянии ввода кода — разрешаем учитывая что это типо ввод кода
            # if current_state and current_state.split(":")[-1] == "verif_code":
            #   return await handler(event, data)

            # иначе это обычное сообщение от незарегистрированного — блокируем
            await event.answer(self.blocked_message_text)
            return None

        # CALLBACK_QUERY
        if isinstance(event, types.CallbackQuery):
            callback_data = event.data or ""
            if self._callback_allowed(callback_data):
                return await handler(event, data)
            # в состоянии verif_code также не разрешаем произвольные колбеки, только белый список
            await event.answer(self.blocked_message_text, show_alert=False)
            return None

        # Другие типы апдейтов — по умолчанию блокируем с сообщением пользователю, если метод answer доступен
        ans = getattr(event, "answer", None)
        if ans:
            try:
                await ans(self.blocked_message_text)
            except Exception:
                pass
        return None
