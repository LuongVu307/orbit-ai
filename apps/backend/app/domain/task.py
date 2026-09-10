from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    COMPLETED = "completed"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str]
    description: Mapped[str | None]

    priority: Mapped[TaskPriority] = mapped_column(
        default=TaskPriority.MEDIUM
    )

    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    status: Mapped[TaskStatus] = mapped_column(
        default=TaskStatus.NOT_STARTED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )