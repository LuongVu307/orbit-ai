from sqlalchemy.orm import Session

from app.agent.intent import AgentAction, TaskIntent
from app.agent.result import AgentProposal
from app.services.task_service import create_task

def understand(message: str) -> TaskIntent | None:
    message = message.strip()

    if message.lower().startswith("learn "):
        title = message[6:].strip()

        return TaskIntent(
            action=AgentAction.CREATE_TASK,
            title=title,
        )

    return None

def propose(message: str) -> AgentProposal | None:
    intent = understand(message)

    if intent is None:
        return None

    return AgentProposal(
        intent=intent,
        requires_approval=True,
    )

def execute_proposal(
    db: Session | None,
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