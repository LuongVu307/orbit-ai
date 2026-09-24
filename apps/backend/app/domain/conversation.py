from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.agent.draft import ConversationStatus
from app.database.base import Base
from app.domain.task import TaskPriority


class DraftConversation(Base):
    __tablename__ = "draft_conversations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    title: Mapped[str | None]
    description: Mapped[str | None]
    priority: Mapped[str | None] = mapped_column(String(20))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(30), default=ConversationStatus.COLLECTING.value
    )
    executed_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id"), unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def task_priority(self) -> TaskPriority | None:
        return TaskPriority(self.priority) if self.priority else None
