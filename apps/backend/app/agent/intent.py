from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from app.domain.task import TaskPriority


class AgentAction(str, Enum):
    CREATE_TASK = "create_task"


class TaskIntent(BaseModel):
    """Facts extracted from one user message, not conversation state."""

    action: AgentAction = AgentAction.CREATE_TASK
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    deadline: datetime | None = None
