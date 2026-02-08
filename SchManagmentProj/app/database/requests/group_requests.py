from typing import List
from sqlalchemy import select
from app.database.engine_base import async_session
from app.database.models.group_models import Group


async def get_groups_letters() -> List[str]:
    async with async_session() as session:
        result = await session.execute(select(Group.letter).distinct())
        letters = [letter for letter in result.scalars().all() if letter]
    return letters


async def get_grades_by_letter(letter: str) -> List[int]:
    async with async_session() as session:
        result = await session.execute(select(Group.grade).filter_by(letter=letter).distinct())
        grades = [g for g in result.scalars().all() if g is not None]
    return grades


async def get_group_by_data(letter: str, grade: int) -> Group:
    async with async_session() as session:
        result = await session.execute(
            select(Group).filter_by(letter=letter, grade=grade))
        return result.scalar_one_or_none()


async def check_group_exists(letter: str, grade: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(Group).filter_by(letter=letter, grade=grade))
        return result.scalar_one_or_none() is not None
