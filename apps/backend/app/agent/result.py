from pydantic import BaseModel

from app.agent.draft import ConversationStatus, DraftTask


class AgentProposal(BaseModel):
    draft_task: DraftTask
    requires_approval: bool = True

class AgentClarification(BaseModel):
    question: str
    missing_fields: list[str]

class AgentResponse(BaseModel):
    proposal: AgentProposal | None = None
    clarification: AgentClarification | None = None
    status: ConversationStatus
    executed_task_id: int | None = None
