from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, Integer, Boolean, Column, DateTime, ForeignKey
from enum import Enum as PyEnum
from sqlalchemy import Enum as SQLEnum
from app.database.engine_base import Base


class Task(Base):
    __tablename__ = 'task_info'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=True)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("registered_users.id", ondelete="SET NULL"),
                                            nullable=True)
    created_for: Mapped[int] = mapped_column(Integer, ForeignKey("registered_users.id", ondelete="SET NULL"),
                                            nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    complete_desc: Mapped[str] = mapped_column(String(1024), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[int] = mapped_column(Integer, ForeignKey("registered_users.id", ondelete="SET NULL"),
                                            nullable=True)
