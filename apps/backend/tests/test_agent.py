from datetime import datetime, timezone

from app.agent.agent import Agent
from app.agent.draft import ConversationStatus
from app.agent.intent import AgentAction, TaskIntent
from app.agent.llm import LLM
from app.domain.task import Task


class FakeLLM(LLM):
    def understand(self, message: str) -> TaskIntent | None:
        if message == "learn Docker":
            return TaskIntent(
                action=AgentAction.CREATE_TASK,
                title="learn Docker",
            )
        if message == "Saturday evening":
            return TaskIntent(
                deadline=datetime(2026, 9, 26, 18, tzinfo=timezone.utc),
            )
        if message == "change it to Sunday morning":
            return TaskIntent(
                deadline=datetime(2026, 9, 27, 9, tzinfo=timezone.utc),
            )
        return None


def test_understand_learn_task():
    agent = Agent(FakeLLM())

    intent = agent.understand("learn Docker")

    assert intent is not None
    assert intent.action == AgentAction.CREATE_TASK
    assert intent.title == "learn Docker"


def test_agent_requests_only_the_missing_required_field():
    agent = Agent(FakeLLM())

    response = agent.propose("learn Docker")

    assert response is not None
    assert response.proposal is None
    assert response.clarification is not None
    assert response.clarification.missing_fields == ["deadline"]
    assert agent.conversation.status == ConversationStatus.COLLECTING


def test_agent_merges_follow_up_into_the_active_draft():
    agent = Agent(FakeLLM())
    agent.propose("learn Docker")

    response = agent.propose("Saturday evening")

    assert response is not None
    assert response.proposal is not None
    assert response.proposal.draft_task.title == "learn Docker"
    assert response.proposal.draft_task.deadline == datetime(
        2026, 9, 26, 18, tzinfo=timezone.utc
    )
    assert agent.conversation.status == ConversationStatus.READY_FOR_CONFIRMATION


def test_collecting_and_proposing_do_not_persist_a_task(db):
    agent = Agent(FakeLLM())
    task_count_before = db.query(Task).count()

    agent.handle_message("learn Docker", db)
    agent.handle_message("Saturday evening", db)

    assert db.query(Task).count() == task_count_before


def test_agent_updates_a_ready_proposal_without_persisting(db):
    agent = Agent(FakeLLM())
    task_count_before = db.query(Task).count()
    agent.handle_message("learn Docker", db)
    agent.handle_message("Saturday evening", db)

    response = agent.handle_message("change it to Sunday morning", db)

    assert response is not None
    assert response.proposal is not None
    assert response.proposal.draft_task.title == "learn Docker"
    assert response.proposal.draft_task.deadline == datetime(
        2026, 9, 27, 9, tzinfo=timezone.utc
    )
    assert response.status == ConversationStatus.READY_FOR_CONFIRMATION
    assert db.query(Task).count() == task_count_before


def test_approval_executes_the_modified_proposal(db):
    agent = Agent(FakeLLM())
    agent.handle_message("learn Docker", db)
    agent.handle_message("Saturday evening", db)
    agent.handle_message("change it to Sunday morning", db)

    response = agent.handle_message("yes", db)

    assert response is not None
    assert response.executed_task_id is not None
    task = db.get(Task, response.executed_task_id)
    assert task is not None
    assert task.deadline == datetime(2026, 9, 27, 9, tzinfo=timezone.utc)


def test_unapproved_proposal_does_not_execute():
    agent = Agent(FakeLLM())
    agent.propose("learn Docker")
    response = agent.propose("Saturday evening")

    assert response is not None
    assert response.proposal is not None
    assert agent.execute_proposal(None, response.proposal, approved=False) is None
    assert agent.conversation.status == ConversationStatus.CANCELLED


def test_approved_proposal_creates_task(db):
    agent = Agent(FakeLLM())
    agent.propose("learn Docker")
    response = agent.propose("Saturday evening")

    assert response is not None
    assert response.proposal is not None
    task = agent.execute_proposal(db, response.proposal, approved=True)

    assert task is not None
    assert task.title == "learn Docker"
    assert task.deadline == datetime(2026, 9, 26, 18, tzinfo=timezone.utc)
    assert agent.conversation.status == ConversationStatus.EXECUTED


def test_yes_executes_the_ready_proposal(db):
    agent = Agent(FakeLLM())
    agent.handle_message("learn Docker", db)
    agent.handle_message("Saturday evening", db)

    response = agent.handle_message("yes", db)

    assert response is not None
    assert response.executed_task_id is not None
    assert agent.conversation.status == ConversationStatus.EXECUTED
