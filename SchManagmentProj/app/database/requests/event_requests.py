from datetime import datetime, date, time, timedelta
from sqlalchemy import select
from app.database.models.event_models import Event
from app.database.engine_base import async_session


async def create_event(data: dict):
    formatted_data = {
        "title": data["title"],
        "description": data.get("description"),
        "created_by": data.get("created_by"),
        "created_at": data.get("created_at"),
        "start_at": data["start_at"],
        "end_at": data["end_at"],
        "image_storage_key": data.get("image_storage_key"),  # <- сохранение ключа фото
    }

    async with async_session() as session:
        new_event = Event(**formatted_data)
        session.add(new_event)
        await session.commit()
        await session.refresh(new_event)
        return new_event


async def get_event_by_name(event_name: str) -> Event:
    async with async_session() as session:
        result = await session.execute(
            select(Event).filter_by(title=event_name, is_deleted=False)
        )
    return result.scalar_one_or_none() is not None


async def get_events_by_date(day_date: date):
    start = datetime.combine(day_date, time.min)
    end = start + timedelta(days=1)
    async with async_session() as session:
        result = await session.execute(
            # ищем события, которые пересекают этот день:
            # start_at < end_of_day AND end_at >= start_of_day
            select(Event).filter(Event.start_at < end, Event.end_at >= start, Event.is_deleted == False)
        )
        return result.scalars().all()


async def get_events_in_range(start_dt: datetime, end_dt: datetime):
    async with async_session() as session:
        result = await session.execute(
            # ищем события, которые пересекают диапазон [start_dt, end_dt]:
            # start_at < end_dt AND end_at >= start_dt
            select(Event).filter(Event.start_at < end_dt, Event.end_at >= start_dt, Event.is_deleted == False)
        )
        return result.scalars().all()


async def soft_delete_event(event_id: int, deleted_by: int, deleted_at: datetime = None):
    if deleted_at is None:
        deleted_at = datetime.now()
    async with async_session() as session:
        event = await session.get(Event, event_id)
        if not event:
            return None
        event.is_deleted = True
        event.deleted_by = deleted_by
        event.deleted_at = deleted_at
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event


async def get_event_by_id(event_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Event).filter_by(id=event_id, is_deleted=False)
        )
        return result.scalar_one_or_none()


async def get_event_data(event_id: int) -> dict:
    async with async_session() as session:
        result = await session.execute(
            select(Event).filter_by(id=event_id, is_deleted=False)
        )
        event = result.scalar_one_or_none()

        return {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "created_by": event.created_by,
            "created_at": event.created_at.isoformat() if isinstance(event.created_at, datetime) else None,
            "is_active": event.is_active,
            "start_at": event.start_at.isoformat() if isinstance(event.start_at, datetime) else None,
            "end_at": event.end_at.isoformat() if isinstance(event.end_at, datetime) else None,
            "image_storage_key": event.image_storage_key,
            "is_deleted": event.is_deleted,
            "deleted_at": event.deleted_at.isoformat() if event.deleted_at else None,
            "deleted_by": event.deleted_by,
        }


async def update_event(event_id: int, compilation: dict) -> Event | None:
    async with async_session() as session:
        event = await session.get(Event, event_id)
        if not event:
            return None
        for key, value in compilation.items():
            if hasattr(event, key):
                setattr(event, key, value)
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event
