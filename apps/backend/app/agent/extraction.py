from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.agent.intent import AgentAction, IntentIssue
from app.domain.task import TaskPriority


class RawTaskExtraction(BaseModel):
    """Untrusted structured output returned by an LLM."""

    model_config = ConfigDict(extra="forbid")

    action: AgentAction | None = None
    task_count: int = Field(default=0, ge=0)
    title: str | None = None
    title_evidence: str | None = None
    description: str | None = None
    description_evidence: str | None = None
    priority: TaskPriority | None = None
    priority_evidence: str | None = None
    deadline: datetime | None = None
    deadline_evidence: str | None = None
    issues: list[IntentIssue] = Field(default_factory=list)

    @field_validator("issues", mode="before")
    @classmethod
    def normalize_null_issues(cls, value):
        return [] if value is None else value
