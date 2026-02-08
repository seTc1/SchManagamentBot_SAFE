from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, Integer, Boolean, Column, DateTime, ForeignKey
from enum import Enum as PyEnum
from sqlalchemy import Enum as SQLEnum
from app.database.engine_base import Base


class UserRole(PyEnum):
    user = "user"
    student = "student"
    teacher = "teacher"
    management = "management"
    admin = "admin"


class ManagementType(PyEnum):
    president = "president"
    media = "media"
    culture = "culture"
    patriot = "patriot"
    volunteer = "volunteer"
    sport = "sport"
    labor = "labor"
    proforientation = "proforientation"
    digit = "digit"


class User(Base):
    __tablename__ = 'registered_users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, name="user_role"), nullable=False,
                                           default=UserRole.user)
    manager_role: Mapped[ManagementType] = mapped_column(SQLEnum(ManagementType, name="manager_role"), nullable=True)
    user_desc: Mapped[str] = mapped_column(String(255), nullable=True)
    registered_at: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    full_name: Mapped[str] = mapped_column(String(64), nullable=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("group_info.id", ondelete="SET NULL"), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    deleted_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[int] = mapped_column(Integer, ForeignKey("registered_users.id", ondelete="SET NULL"),
                                            nullable=True)
