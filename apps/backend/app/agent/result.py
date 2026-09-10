from pydantic import BaseModel

from app.agent.intent import TaskIntent


class AgentProposal(BaseModel):
    intent: TaskIntent
    requires_approval: bool = True