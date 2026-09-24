from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.task import TaskPriority
class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: datetime | None = None

class AgentMessage(BaseModel):
    message: str
    conversation_id: UUID | None = None

class AgentApproval(BaseModel):
    conversation_id: UUID
