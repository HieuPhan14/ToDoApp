from __future__ import annotations
from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import DateTime, ForeignKey, Integer, String, func, Enum as SAEnum
from datetime import UTC, datetime
from enum import Enum


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class Task(Base):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(String(300))
    due_date: Mapped[datetime | None] = mapped_column()
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), default=TaskStatus.pending)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    user: Mapped["User"] = relationship(back_populates="tasks")

    likes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    