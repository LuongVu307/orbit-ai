from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.draft import ConversationState, ConversationStatus, DraftTask
from app.domain.conversation import DraftConversation


def create_conversation(db: Session) -> DraftConversation:
    conversation = DraftConversation()
    db.add(conversation)
    db.flush()
    return conversation


def get_conversation(
    db: Session,
    conversation_id: UUID,
    *,
    for_update: bool = False,
) -> DraftConversation | None:
    statement = select(DraftConversation).where(
        DraftConversation.id == conversation_id
    )
    if for_update:
        statement = statement.with_for_update()
    return db.scalar(statement)


def conversation_state(conversation: DraftConversation) -> ConversationState:
    return ConversationState(
        draft_task=DraftTask(
            title=conversation.title,
            description=conversation.description,
            priority=conversation.task_priority,
            deadline=conversation.deadline,
        ),
        status=ConversationStatus(conversation.status),
    )


def apply_conversation_state(
    conversation: DraftConversation,
    state: ConversationState,
) -> None:
    conversation.title = state.draft_task.title
    conversation.description = state.draft_task.description
    conversation.priority = (
        state.draft_task.priority.value if state.draft_task.priority else None
    )
    conversation.deadline = state.draft_task.deadline
    conversation.status = state.status.value
