from pydantic import BaseModel

from app.agent.intent import TaskIntent


class AgentProposal(BaseModel):
    intent: TaskIntent
    requires_approval: bool = True

class AgentClarification(BaseModel):
    question: str

class AgentResponse(BaseModel):
    proposal: AgentProposal | None = None
    clarification: AgentClarification | None = None