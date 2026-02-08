from aiogram.filters.callback_data import CallbackData


class ItemCallback(CallbackData, prefix="item"):
    callback_action: str
    data: str


from aiogram import Router
from app.middlewares.middlewares import RegistrationBarrier
from .registration_handlers import router as registration_router
from .profile_handlers import router as profile_router
from .code_handlers import router as code_router
from app.handlers.event.event_handlers import router as event_router
from app.handlers.event.event_creation_handlers import router as event_creation_router
from .other_handlers import router as other_router
from .settings_handlers import router as settings_router
from .announcement_handlers import router as notifications_router
from app.handlers.task.task_handlers import router as task_router
from app.handlers.task.task_creation_handlers import router as task_creation_router
from app.handlers.task.report_handlers import router as report_router

router = Router()

mw = RegistrationBarrier(
    allowed_commands=["start"],
    allowed_callback_patterns=["^create_profile"]
)

router.message.middleware(mw)
router.callback_query.middleware(mw)

router.include_router(registration_router)
router.include_router(profile_router)
router.include_router(code_router)
router.include_router(event_router)
router.include_router(event_creation_router)
router.include_router(other_router)
router.include_router(settings_router)
router.include_router(notifications_router)
router.include_router(task_router)
router.include_router(task_creation_router)
router.include_router(report_router)
