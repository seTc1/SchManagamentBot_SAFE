from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, Integer, Boolean, Column, DateTime, ForeignKey
from app.database.engine_base import Base


class Group(Base):
    __tablename__ = 'group_info'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    letter: Mapped[str] = mapped_column(String(1), nullable=False)
    students_count: Mapped[int] = mapped_column(Integer, nullable=False)
    registered_students: Mapped[int] = mapped_column(Integer, nullable=False)
