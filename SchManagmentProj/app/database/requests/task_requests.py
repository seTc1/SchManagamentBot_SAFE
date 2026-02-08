from datetime import datetime
from sqlalchemy import select, func
from app.database.engine_base import async_session
from app.database.models.task_models import *
from app.database.requests.user_requests import get_user_by_tg_id


async def get_task_by_title(title: str):
    async with async_session() as session:
        result = await session.execute(
            select(Task).filter_by(title=title, is_deleted=False))
        return result.scalar_one_or_none()


async def create_task(compilation: dict):
    async with async_session() as session:
        task = Task(**compilation)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


async def get_user_active_tasks(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Task).filter_by(created_for=user_id, is_completed=False, is_deleted=False))
        return result.scalars().all()


async def get_user_completed_tasks(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Task).filter_by(created_for=user_id, is_completed=True, is_deleted=False))
        return result.scalars().all()


async def get_task_by_id(task_id: int) -> Task | None:
    async with async_session() as session:
        result = await session.execute(
            select(Task).filter_by(id=task_id, is_deleted=False))
        return result.scalar_one_or_none()


async def set_task_completed(task_id: int) -> Task | None:
    async with async_session() as session:
        result = await session.execute(
            select(Task).filter_by(id=task_id, is_deleted=False))
        task = result.scalar_one_or_none()
        if not task:
            return None
        task.is_completed = True
        task.completed_at = datetime.now()
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


async def update_task_complete_desc(task_id: int, description: str) -> Task | None:
    async with async_session() as session:
        result = await session.execute(
            select(Task).filter_by(id=task_id, is_deleted=False))
        task = result.scalar_one_or_none()
        if not task:
            return None

        task.complete_desc = description
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


async def soft_delete_task(task_id: int, deleted_by: int, deleted_at: datetime = None):
    if deleted_at is None:
        deleted_at = datetime.now()
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if not task:
            return None
        task.is_deleted = True
        task.deleted_by = deleted_by
        task.deleted_at = deleted_at
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


async def update_task(task_id: int, compilation: dict) -> Task | None:
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if not task:
            return None
        # Обновляем только переданные поля
        for key, value in compilation.items():
            if hasattr(task, key):
                setattr(task, key, value)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task


async def get_tasks_tracker_stats():
    now = datetime.now()
    month_start = datetime(now.year, now.month, 1)

    async with async_session() as session:
        total_tasks = await session.scalar(
            select(func.count(Task.id)).where(Task.is_deleted.is_(False))
        )

        completed_tasks = await session.scalar(
            select(func.count(Task.id)).where(
                Task.is_deleted.is_(False),
                Task.is_completed.is_(True)
            )
        )

        month_tasks = await session.scalar(
            select(func.count(Task.id)).where(
                Task.is_deleted.is_(False),
                Task.created_at >= month_start
            )
        )

        month_completed_tasks = await session.scalar(
            select(func.count(Task.id)).where(
                Task.is_deleted.is_(False),
                Task.is_completed.is_(True),
                Task.completed_at >= month_start
            )
        )

        return {
            "total": total_tasks or 0,
            "completed": completed_tasks or 0,
            "month_total": month_tasks or 0,
            "month_completed": month_completed_tasks or 0,
        }
