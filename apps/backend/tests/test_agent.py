from app.agent.agent import Agent
from app.agent.llm import LLM
from app.agent.intent import AgentAction, TaskIntent

class FakeLLM(LLM):
    def understand(self, message: str) -> TaskIntent | None:
        if message == "learn Docker":
            return TaskIntent(
                action=AgentAction.CREATE_TASK,
                title="learn Docker",
            )

        if message == "remind me to study":
            return TaskIntent(
                action=AgentAction.CREATE_TASK,
                title="study",
                needs_clarification=True,
                clarification_question="When would you like to be reminded?",
            )

        return None

agent = Agent(FakeLLM())


def test_understand_learn_task():
    intent = agent.understand("learn Docker")

    assert intent is not None
    assert intent.action == AgentAction.CREATE_TASK
    assert intent.title == "learn Docker"

def test_agent_proposes_task():
    response = agent.propose("learn Docker")

    assert response is not None
    assert response.proposal is not None
    assert response.proposal.intent.title == "learn Docker"

def test_unapproved_proposal_does_not_execute():
    response = agent.propose("learn Docker")

    assert response is not None
    assert response.proposal is not None

    # We don't pass a database here.
    # If approval is required, execution should not happen.
    result = agent.execute_proposal(None, response.proposal, approved=False)

    assert result is None

def test_approved_proposal_creates_task(db):
    response = agent.propose("learn Docker")

    assert response is not None
    assert response.proposal is not None

    task = agent.execute_proposal(
        db,
        response.proposal,
        approved=True,
    )

    assert task is not None
    assert task.title == "learn Docker"

def test_agent_detects_missing_information():
    response = agent.propose("remind me to study")

    assert response is not None
    assert response.proposal is None
    assert response.clarification is not None
    assert response.clarification.question == (
        "When would you like to be reminded?"
    )