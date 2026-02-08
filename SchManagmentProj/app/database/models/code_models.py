from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, Integer, Boolean, Column, DateTime, ForeignKey
from enum import Enum as PyEnum
from sqlalchemy import Enum as SQLEnum
from app.database.engine_base import Base
from app.database.models.user_models import UserRole


class DistributionType(PyEnum):
    personal = "personal"
    public = "public"


class RegistrationCode(Base):
    __tablename__ = "registration_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole, name="user_role"), nullable=False,
                                           default=UserRole.user)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("registered_users.id", ondelete="SET NULL"),
                                            nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    full_name: Mapped[str] = mapped_column(String(255), nullable=True)

    distribution: Mapped[DistributionType] = mapped_column(SQLEnum(DistributionType, name="code_type"), nullable=False,
                                                           default=DistributionType.personal)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("group_info.id", ondelete="SET NULL"), nullable=True)
    uses_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

