from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, Integer, Boolean, Column, DateTime, ForeignKey
from app.database.engine_base import Base


class Event(Base):
    __tablename__ = 'event_info'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=True)

    # ссылка на пользователя в вашей таблице пользователей (если есть)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("registered_users.id", ondelete="SET NULL"),
                                            nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Сроки проведения — портативный вариант
    start_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Картинка — ключ файла в тг
    image_storage_key: Mapped[str] = mapped_column(String(512), nullable=True)

    # group_id: Mapped[int] = mapped_column(Integer, ForeignKey("group_info.id", ondelete="SET NULL"), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[int] = mapped_column(Integer, ForeignKey("registered_users.id", ondelete="SET NULL"),
                                            nullable=True)
