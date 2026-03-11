from datetime import datetime
from datetime import date
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Role(str, Enum):
    ADMIN = "Admin"
    DEVELOPER = "Developer"
    REVIEWER = "Reviewer"


ROLE_ENUM = SqlEnum(
    Role,
    native_enum=False,
    values_callable=lambda enum_class: [member.value for member in enum_class],
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(ROLE_ENUM, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    audit_sessions: Mapped[list["AuditSession"]] = relationship(back_populates="created_by")


class AuditSession(Base):
    __tablename__ = "audit_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    run_dir: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="clockify", server_default="clockify")
    clockify_workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    clockify_workspace_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(128), nullable=True)
    big_task_hours: Mapped[float | None] = mapped_column(Float(), nullable=True)
    time_stats: Mapped[dict[str, Any] | None] = mapped_column(JSON(), nullable=True)
    overlap_per_user: Mapped[dict[str, Any] | None] = mapped_column(JSON(), nullable=True)
    small_tasks_per_user: Mapped[dict[str, Any] | None] = mapped_column(JSON(), nullable=True)
    big_tasks_per_user: Mapped[dict[str, Any] | None] = mapped_column(JSON(), nullable=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    created_by: Mapped[User] = relationship(back_populates="audit_sessions")