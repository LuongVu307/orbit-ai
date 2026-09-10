from app.agent.agent import understand
from app.agent.intent import AgentAction
from app.agent.agent import execute_proposal, propose


def test_understand_learn_task():
    intent = understand("learn Docker")

    assert intent is not None
    assert intent.action == AgentAction.CREATE_TASK
    assert intent.title == "Docker"

def test_agent_proposes_task():
    proposal = propose("learn Docker")

    assert proposal is not None
    assert proposal.intent.title == "Docker"
    assert proposal.requires_approval is True

def test_unapproved_proposal_does_not_execute():
    proposal = propose("learn Docker")

    assert proposal is not None

    # We don't pass a database here.
    # If approval is required, execution should not happen.
    result = execute_proposal(None, proposal, approved=False)

    assert result is None

def test_approved_proposal_creates_task(db):
    proposal = propose("learn Docker")

    assert proposal is not None

    task = execute_proposal(
        db,
        proposal,
        approved=True,
    )

    assert task is not None
    assert task.title == "Docker"