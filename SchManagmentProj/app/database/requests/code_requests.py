from sqlalchemy import select, update, delete
from app.database.models.code_models import DistributionType, RegistrationCode
from app.database.models.user_models import UserRole
from app.database.models.group_models import Group
from app.database.engine_base import async_session


async def create_code(data: dict):
    """
    data ожидает структуру:
    {
        "code": str,
        "role": UserRole,
        "created_by": int | None,
        "created_at": datetime,
        "meta": {"full_name": str, "distribution": DistributionType, "group_id": int}
    }
    """
    formatted_data = {
        "code": data["code"],
        "role": data["role"],
        "created_by": data.get("created_by"),
        "created_at": data.get("created_at")
    }

    async with async_session() as session:
        new_code = RegistrationCode(**formatted_data)
        session.add(new_code)
        await session.flush()

        meta = data.get("meta")
        if not meta:
            await session.commit()
            await session.refresh(new_code)
            return new_code

        # Записываем учительские данные в поле full_name самого RegistrationCode
        if formatted_data["role"] == UserRole.teacher:
            teacher_name = meta.get("full_name")
            if teacher_name:
                new_code.full_name = teacher_name

        # Для студента — записываем distribution и group_id в RegistrationCode
        elif formatted_data["role"] == UserRole.student:
            distribution = meta.get("distribution")
            group_id = meta.get("group_id")

            if group_id is not None and distribution is not None:
                new_code.distribution = distribution
                new_code.group_id = group_id

        await session.commit()
        await session.refresh(new_code)
        return new_code


"""async def get_code_group(code_object: RegistrationCode) -> Group:
    async with async_session() as session:
        if code_object.role == UserRole.student:
            student_code_result = await session.execute(
                select(StudentCode).filter_by(code_id=code_object.id)
            )
            student_code_object = student_code_result.scalar_one_or_none()

            student_group_result = await session.execute(
                select(Group).filter_by(id=student_code_object.group_id)
            )
            student_group_object = student_group_result.scalar_one_or_none()
            return student_group_object"""


async def check_code_exist(code: str) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(RegistrationCode).filter_by(code=code)
        )
        return result.scalar_one_or_none() is not None


async def get_registration_code(code: str) -> RegistrationCode:
    async with async_session() as session:
        result = await session.execute(
            select(RegistrationCode).filter_by(code=code)
        )
        return result.scalar_one_or_none()
