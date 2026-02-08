from typing import Optional

from sqlalchemy import select, update, delete
from datetime import datetime
from app.database.models.code_models import RegistrationCode, DistributionType
from app.database.models.group_models import Group
from app.database.models.user_models import User, UserRole, ManagementType
from app.database.engine_base import async_session


async def create_role_user(tg_id: int, code_object: RegistrationCode):
    async with async_session() as session:
        # Проверяем, существует ли пользователь
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalar_one_or_none()
        if user:
            return

        # Учитель
        if code_object.role == UserRole.teacher:
            # берём имя учителя из самого кода
            teacher_full_name = getattr(code_object, "full_name", None)
            if not teacher_full_name:
                return False

            new_user_data = User(
                tg_id=tg_id,
                role=UserRole.teacher,
                full_name=teacher_full_name,
                registered_at=datetime.utcnow()
            )
            session.add(new_user_data)
            await session.flush()

            # удаляем использованный код
            await session.delete(code_object)

            await session.commit()
            return True

        # Школьник
        if code_object.role == UserRole.student:
            group_id = getattr(code_object, "group_id", None)
            if not group_id:
                return False

            student_group_result = await session.execute(
                select(Group).filter_by(id=group_id)
            )
            student_group_object = student_group_result.scalar_one_or_none()
            if not student_group_object:
                return False

            # === Проверка лимита группы ===
            if student_group_object.registered_students < student_group_object.students_count:
                new_user_data = User(
                    tg_id=tg_id,
                    role=UserRole.student,
                    group_id=group_id,
                    registered_at=datetime.utcnow()
                )
                session.add(new_user_data)
                await session.flush()

                # Увеличиваем число зарегистрированных студентов
                await session.execute(
                    update(Group)
                    .where(Group.id == student_group_object.id)
                    .values(registered_students=student_group_object.registered_students + 1)
                )

                # Если код персональный — удаляем его
                if code_object.distribution == DistributionType.personal:
                    await session.delete(code_object)
                elif code_object.distribution == DistributionType.public:
                    await session.execute(
                        update(RegistrationCode)
                        .where(RegistrationCode.id == code_object.id)
                        .values(uses_count=code_object.uses_count + 1)
                    )
                await session.commit()
                return True


async def create_user(tg_id: int):
    async with async_session() as session:
        # Проверяем, существует ли пользователь
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        user = result.scalar_one_or_none()
        if user:
            return
        new_user_data = User(
            tg_id=tg_id,
            role=UserRole.user,
            registered_at=datetime.utcnow()
        )
        session.add(new_user_data)
        await session.commit()


async def get_existing_managers():
    async with async_session() as session:
        result = await session.execute(select(User).filter_by(role=UserRole.management))
        return result.scalars().all()


async def get_president():
    async with async_session() as session:
        result = await session.execute(select(User).filter_by(manager_role=ManagementType.president))
        return result.scalar_one_or_none()


async def get_user_by_tg_id(tg_id: int) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(select(User).filter_by(tg_id=tg_id))
        return result.scalar_one_or_none()


async def get_user_data(user_id: int) -> dict:
    async with async_session() as session:
        result = await session.execute(select(User).filter_by(id=user_id))
        user = result.scalar_one_or_none()

        return {
            "id": user.id,
            "tg_id": user.tg_id,
            "role": user.role if user.role else None,
            "manager_role": user.manager_role if user.manager_role else None,
            "user_desc": user.user_desc,
            "registered_at": user.registered_at.isoformat() if isinstance(user.registered_at,
                                                                          datetime) else user.registered_at,
            "is_banned": user.is_banned,
            "full_name": user.full_name,
            "group_id": user.group_id,
            "is_deleted": user.is_deleted,
            "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
            "deleted_by": user.deleted_by,
        }


async def get_users_for_announce() -> list[int]:
    async with async_session() as session:
        result = await session.execute(select(User.tg_id).filter_by(is_banned=False, is_deleted=False))
        return result.scalars().all()
