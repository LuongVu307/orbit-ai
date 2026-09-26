from app.agent.intent import IntentIssue, TaskIntent, UnderstandingResult
from app.domain.task import TaskPriority
from evals.scoring import score_case, summarize_results


def test_scoring_tracks_fields_categories_and_prohibited_inference():
    case = {
        "name": "no_inference",
        "category": "prohibited_inference",
        "message": "Read the paper",
        "expected": {
            "intent": {"title": "Read the paper"},
            "null_fields": ["description", "priority", "deadline"],
            "required_issues": [],
        },
    }
    result = UnderstandingResult(
        intent=TaskIntent(
            title="Read the paper",
            priority=TaskPriority.HIGH,
        )
    )

    scored = score_case(case, result)
    summary = summarize_results([scored])

    assert scored["passed"] is False
    assert scored["prohibited_inferences"] == ["priority"]
    assert summary["prohibited_inferences"] == 1
    assert summary["categories"]["prohibited_inference"]["total"] == 1


def test_scoring_accepts_required_issue_without_an_intent():
    case = {
        "name": "multiple",
        "category": "multiple_tasks",
        "message": "Do one and two",
        "expected": {
            "intent": None,
            "null_fields": [],
            "required_issues": ["multiple_tasks"],
        },
    }
    result = UnderstandingResult(issues=[IntentIssue.MULTIPLE_TASKS])

    scored = score_case(case, result)

    assert scored["passed"] is True
