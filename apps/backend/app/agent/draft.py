from pydantic import BaseModel
from app.domain.task import TaskPriority

from datetime import datetime
from enum import Enum

class DraftTask(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    deadline: datetime | None = None


class ConversationStatus(str, Enum):
    COLLECTING = "collecting"
    READY_FOR_CONFIRMATION = "ready_for_confirmation"
    CONFIRMED = "confirmed"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


class ConversationState(BaseModel):
    draft_task: DraftTask = DraftTask()
    status: ConversationStatus = ConversationStatus.COLLECTING
