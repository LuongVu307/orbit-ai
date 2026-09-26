from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.domain.task import TaskPriority


class AgentAction(str, Enum):
    CREATE_TASK = "create_task"


class IntentIssue(str, Enum):
    AMBIGUOUS_DEADLINE = "ambiguous_deadline"
    AMBIGUOUS_PRIORITY = "ambiguous_priority"
    AMBIGUOUS_TITLE = "ambiguous_title"
    CONFLICTING_DETAILS = "conflicting_details"
    MULTIPLE_TASKS = "multiple_tasks"
    UNSUPPORTED_REQUEST = "unsupported_request"


class TaskIntent(BaseModel):
    """Facts extracted from one user message, not conversation state."""

    action: AgentAction = AgentAction.CREATE_TASK
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    deadline: datetime | None = None


class UnderstandingResult(BaseModel):
    """Validated facts and issues from one user message."""

    intent: TaskIntent | None = None
    issues: list[IntentIssue] = Field(default_factory=list)
    rejected_fields: list[str] = Field(default_factory=list)
