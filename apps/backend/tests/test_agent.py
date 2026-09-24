from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.agent.agent import Agent
from app.agent.draft import ConversationState, ConversationStatus
from app.agent.intent import AgentAction, TaskIntent
from app.agent.llm import LLM
from app.api.schemas import AgentApproval, AgentMessage
from app.domain.conversation import DraftConversation
from app.domain.task import Task
from app.main import agent_message, approve_agent_proposal, get_agent_conversation


class FakeLLM(LLM):
    def understand(self, message: str) -> TaskIntent | None:
        if message == "learn Docker":
            return TaskIntent(action=AgentAction.CREATE_TASK, title="learn Docker")
        if message == "write report":
            return TaskIntent(action=AgentAction.CREATE_TASK, title="write report")
        if message == "Saturday evening":
            return TaskIntent(
                deadline=datetime(2026, 9, 26, 18, tzinfo=timezone.utc)
            )
        if message == "change it to Sunday morning":
            return TaskIntent(
                deadline=datetime(2026, 9, 27, 9, tzinfo=timezone.utc)
            )
        return None


@pytest.fixture(autouse=True)
def fake_api_agent(monkeypatch):
    monkeypatch.setattr("app.main.agent", Agent(FakeLLM()))


def test_understand_learn_task():
    intent = Agent(FakeLLM()).understand("learn Docker")

    assert intent is not None
    assert intent.action == AgentAction.CREATE_TASK
    assert intent.title == "learn Docker"


def test_agent_requests_only_the_missing_required_field():
    state = ConversationState()

    response = Agent(FakeLLM()).handle_message("learn Docker", state)

    assert response is not None
    assert response.proposal is None
    assert response.clarification is not None
    assert response.clarification.missing_fields == ["deadline"]
    assert state.status == ConversationStatus.COLLECTING


def test_agent_merges_follow_up_into_the_supplied_draft():
    agent = Agent(FakeLLM())
    state = ConversationState()
    agent.handle_message("learn Docker", state)

    response = agent.handle_message("Saturday evening", state)

    assert response is not None
    assert response.proposal is not None
    assert response.proposal.draft_task.title == "learn Docker"
    assert response.proposal.draft_task.deadline == datetime(
        2026, 9, 26, 18, tzinfo=timezone.utc
    )
    assert state.status == ConversationStatus.READY_FOR_CONFIRMATION


def test_agent_updates_a_ready_proposal():
    agent = Agent(FakeLLM())
    state = ConversationState()
    agent.handle_message("learn Docker", state)
    agent.handle_message("Saturday evening", state)

    response = agent.handle_message("change it to Sunday morning", state)

    assert response is not None
    assert response.proposal is not None
    assert response.proposal.draft_task.deadline == datetime(
        2026, 9, 27, 9, tzinfo=timezone.utc
    )
    assert response.status == ConversationStatus.READY_FOR_CONFIRMATION


def test_agent_confirmation_marks_state_without_creating_a_task(db):
    agent = Agent(FakeLLM())
    state = ConversationState()
    agent.handle_message("learn Docker", state)
    agent.handle_message("Saturday evening", state)
    task_count_before = db.query(Task).count()

    response = agent.handle_message("yes", state)

    assert response is not None
    assert response.status == ConversationStatus.CONFIRMED
    assert state.status == ConversationStatus.CONFIRMED
    assert db.query(Task).count() == task_count_before


def test_conversation_is_persisted_and_restored(db):
    created = agent_message(AgentMessage(message="learn Docker"), db)
    conversation_id = created.conversation_id

    assert isinstance(conversation_id, UUID)
    db.expire_all()
    assert db.get(DraftConversation, conversation_id) is not None

    restored = get_agent_conversation(conversation_id, db)

    assert restored.conversation_id == conversation_id
    assert restored.clarification is not None
    assert restored.clarification.missing_fields == ["deadline"]


def test_conversations_are_isolated(db):
    first = agent_message(AgentMessage(message="learn Docker"), db)
    second = agent_message(AgentMessage(message="write report"), db)

    agent_message(
        AgentMessage(
            conversation_id=first.conversation_id,
            message="Saturday evening",
        ),
        db,
    )
    restored_second = get_agent_conversation(second.conversation_id, db)

    assert restored_second.clarification is not None
    assert restored_second.clarification.missing_fields == ["deadline"]
    assert restored_second.proposal is None


def test_approval_is_idempotent_and_uses_stored_draft(db):
    first = agent_message(AgentMessage(message="learn Docker"), db)
    ready = agent_message(
        AgentMessage(
            conversation_id=first.conversation_id,
            message="Saturday evening",
        ),
        db,
    )
    task_count_before = db.query(Task).count()

    approved = approve_agent_proposal(
        AgentApproval(conversation_id=ready.conversation_id), db
    )
    repeated = approve_agent_proposal(
        AgentApproval(conversation_id=ready.conversation_id), db
    )

    assert approved.executed_task_id == repeated.executed_task_id
    assert db.query(Task).count() == task_count_before + 1


def test_cancellation_does_not_create_a_task(db):
    first = agent_message(AgentMessage(message="learn Docker"), db)
    ready = agent_message(
        AgentMessage(
            conversation_id=first.conversation_id,
            message="Saturday evening",
        ),
        db,
    )
    task_count_before = db.query(Task).count()

    cancelled = agent_message(
        AgentMessage(
            conversation_id=ready.conversation_id,
            message="cancel",
        ),
        db,
    )

    assert cancelled.status == ConversationStatus.CANCELLED
    assert db.query(Task).count() == task_count_before


def test_unknown_conversation_returns_not_found(db):
    with pytest.raises(HTTPException) as error:
        get_agent_conversation(uuid4(), db)

    assert error.value.status_code == 404
