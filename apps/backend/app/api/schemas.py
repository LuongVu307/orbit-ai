from datetime import datetime

from pydantic import BaseModel

from app.domain.task import TaskPriority
from app.agent.result import AgentProposal


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: datetime | None = None

class AgentMessage(BaseModel):
    message: str

class AgentApproval(BaseModel):
    proposal: AgentProposal