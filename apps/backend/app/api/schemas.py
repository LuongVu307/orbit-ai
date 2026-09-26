from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.task import TaskPriority


MAX_AGENT_MESSAGE_LENGTH = 4000


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: datetime | None = None


class AgentMessage(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_AGENT_MESSAGE_LENGTH)
    conversation_id: UUID | None = None


class AgentApproval(BaseModel):
    conversation_id: UUID
