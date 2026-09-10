from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class AgentAction(str, Enum):
    CREATE_TASK = "create_task"


class TaskIntent(BaseModel):
    action: AgentAction
    title: str
    deadline: datetime | None = None
    needs_clarification: bool = False
    clarification_question: str | None = None