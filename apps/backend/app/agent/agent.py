from sqlalchemy.orm import Session

from app.agent.intent import AgentAction, TaskIntent
from app.agent.llm import LLM
from app.agent.result import AgentProposal, AgentClarification, AgentResponse
from app.services.task_service import create_task


class Agent:
    def __init__(self, llm: LLM):
        self.llm = llm

    def understand(self, message: str) -> TaskIntent | None:
        return self.llm.understand(message)

    def propose(self, message: str) -> AgentResponse | None:
        intent = self.understand(message)

        if intent is None:
            return None

        if intent.needs_clarification:
            return AgentResponse(
                clarification=AgentClarification(
                    question=intent.clarification_question
                )
            )

        return AgentResponse(
            proposal=AgentProposal(
                intent=intent,
                requires_approval=True,
            )
        )
    
    def execute_proposal(
        self,
        db: Session,
        proposal: AgentProposal,
        approved: bool,
    ):
        if not approved:
            return None

        if proposal.intent.action == AgentAction.CREATE_TASK:
            return create_task(
                db,
                title=proposal.intent.title,
                deadline=proposal.intent.deadline,
            )

        return None

