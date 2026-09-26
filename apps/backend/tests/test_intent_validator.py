from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.agent.extraction import RawTaskExtraction
from app.agent.intent import IntentIssue
from app.agent.intent_validator import validate_extraction
from app.domain.task import TaskPriority


def test_validator_accepts_supported_facts():
    result = validate_extraction(
        "High priority: submit the lab tomorrow at 5pm",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="submit the lab",
            title_evidence="submit the lab",
            priority=TaskPriority.HIGH,
            priority_evidence="High priority",
            deadline=datetime(2026, 9, 27, 17, tzinfo=timezone.utc),
            deadline_evidence="tomorrow at 5pm",
        ),
        now=datetime(2026, 9, 26, 10, tzinfo=timezone.utc),
    )

    assert result.intent is not None
    assert result.intent.title == "submit the lab"
    assert result.intent.priority == TaskPriority.HIGH
    assert result.intent.deadline == datetime(
        2026, 9, 27, 17, tzinfo=timezone.utc
    )
    assert result.issues == []


def test_validator_discards_invented_deadline_and_priority():
    result = validate_extraction(
        "Read the operating systems paper",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="Read the operating systems paper",
            title_evidence="Read the operating systems paper",
            priority=TaskPriority.HIGH,
            priority_evidence="important",
            deadline=datetime(2026, 9, 27, 17, tzinfo=timezone.utc),
            deadline_evidence="tomorrow",
        ),
    )

    assert result.intent is not None
    assert result.intent.deadline is None
    assert result.intent.priority is None
    assert set(result.rejected_fields) == {"deadline", "priority"}
    assert result.issues == []


def test_validator_requires_both_date_and_time():
    result = validate_extraction(
        "Call Sam Friday",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="Call Sam",
            title_evidence="Call Sam",
            deadline=None,
            deadline_evidence=None,
        ),
    )

    assert result.intent is not None
    assert result.intent.deadline is None
    assert IntentIssue.AMBIGUOUS_DEADLINE in result.issues


def test_validator_resolves_deadline_from_evidence_not_model_guess():
    result = validate_extraction(
        "Revise Dijkstra tomorrow at 3pm",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="Revise Dijkstra",
            title_evidence="Revise Dijkstra",
            deadline=datetime(2026, 9, 28, 15, tzinfo=timezone.utc),
            deadline_evidence="tomorrow at 3pm",
        ),
        now=datetime(2026, 9, 26, 10, tzinfo=timezone.utc),
    )

    assert result.intent is not None
    assert result.intent.deadline == datetime(
        2026, 9, 27, 15, tzinfo=timezone.utc
    )


def test_validator_reports_multiple_tasks_without_selecting_one():
    result = validate_extraction(
        "Email Alex and clean the kitchen",
        RawTaskExtraction(
            action="create_task",
            task_count=2,
            issues=[IntentIssue.MULTIPLE_TASKS],
        ),
    )

    assert result.intent is None
    assert IntentIssue.MULTIPLE_TASKS in result.issues


def test_validator_detects_multiple_tasks_when_model_misses_them():
    result = validate_extraction(
        "Email Alex and clean the kitchen",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="Email Alex",
            title_evidence="Email Alex",
        ),
    )

    assert result.intent is None
    assert IntentIssue.MULTIPLE_TASKS in result.issues


def test_validator_detects_unlisted_second_task_verb():
    result = validate_extraction(
        "Wash the car and mow the lawn",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="Wash the car",
            title_evidence="Wash the car",
        ),
    )

    assert result.intent is None
    assert IntentIssue.MULTIPLE_TASKS in result.issues


def test_validator_detects_two_actions_even_when_full_title_is_evidence():
    result = validate_extraction(
        "Wash the car and mow the lawn",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="Wash the car and mow the lawn",
            title_evidence="Wash the car and mow the lawn",
        ),
    )

    assert result.intent is None
    assert IntentIssue.MULTIPLE_TASKS in result.issues


def test_validator_detects_second_action_with_proper_name_object():
    result = validate_extraction(
        "Email Alex and call Bob",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="Email Alex and call Bob",
            title_evidence="Email Alex and call Bob",
        ),
    )

    assert result.intent is None
    assert IntentIssue.MULTIPLE_TASKS in result.issues


def test_validator_detects_lowercase_second_action_with_name_object():
    result = validate_extraction(
        "email alex and call bob",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="email alex and call bob",
            title_evidence="email alex and call bob",
        ),
    )

    assert result.intent is None
    assert IntentIssue.MULTIPLE_TASKS in result.issues


def test_validator_detects_lowercase_second_action_after_determiner():
    result = validate_extraction(
        "email the tutor and call bob",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="email the tutor and call bob",
            title_evidence="email the tutor and call bob",
        ),
    )

    assert result.intent is None
    assert IntentIssue.MULTIPLE_TASKS in result.issues


def test_validator_detects_one_word_second_task():
    result = validate_extraction(
        "buy milk and revise",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="buy milk and revise",
            title_evidence="buy milk and revise",
        ),
    )

    assert result.intent is None
    assert IntentIssue.MULTIPLE_TASKS in result.issues


def test_priority_conflict_does_not_hide_multiple_tasks():
    result = validate_extraction(
        "high and low priority: email alex and call bob",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="email alex and call bob",
            title_evidence="email alex and call bob",
        ),
    )

    assert result.intent is None
    assert IntentIssue.MULTIPLE_TASKS in result.issues


def test_validator_detects_second_action_with_pronoun_object():
    result = validate_extraction(
        "Buy milk and email him",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="Buy milk and email him",
            title_evidence="Buy milk and email him",
        ),
    )

    assert result.intent is None
    assert IntentIssue.MULTIPLE_TASKS in result.issues


def test_validator_allows_conjunction_inside_supported_noun_phrase():
    result = validate_extraction(
        "Prepare the research and development report Monday at 3pm",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="Prepare the research and development report",
            title_evidence="Prepare the research and development report",
            deadline=datetime(2026, 9, 28, 15, tzinfo=timezone.utc),
            deadline_evidence="Monday at 3pm",
        ),
        now=datetime(2026, 9, 26, 10, tzinfo=timezone.utc),
    )

    assert result.intent is not None
    assert result.intent.title == (
        "Prepare the research and development report"
    )
    assert IntentIssue.MULTIPLE_TASKS not in result.issues


def test_validator_reports_missing_explicit_priority():
    result = validate_extraction(
        "High priority: submit the form",
        RawTaskExtraction(
            action="create_task",
            task_count=1,
            title="submit the form",
            title_evidence="submit the form",
        ),
    )

    assert result.intent is not None
    assert result.intent.priority == TaskPriority.HIGH
    assert IntentIssue.AMBIGUOUS_PRIORITY not in result.issues


def test_validator_rejects_other_task_fields_as_description():
    result = validate_extraction(
        "Plan the demo Friday at noon, medium priority",
        RawTaskExtraction(
            task_count=1,
            title="Plan the demo",
            title_evidence="Plan the demo",
            description="Friday at noon, medium priority",
            description_evidence="Friday at noon, medium priority",
            priority=TaskPriority.MEDIUM,
            priority_evidence="medium priority",
            deadline=datetime(2026, 10, 2, 12, tzinfo=timezone.utc),
            deadline_evidence="Friday at noon",
        ),
        now=datetime(2026, 9, 26, 10, tzinfo=timezone.utc),
    )

    assert result.intent is not None
    assert result.intent.description is None
    assert "description" in result.rejected_fields


def test_validator_treats_change_it_to_as_a_field_update():
    result = validate_extraction(
        "change it to Sunday at 9am",
        RawTaskExtraction(
            task_count=1,
            title="change it to Sunday at 9am",
            title_evidence="change it to Sunday at 9am",
            deadline=datetime(2026, 9, 27, 9, tzinfo=timezone.utc),
            deadline_evidence="Sunday at 9am",
        ),
        now=datetime(2026, 9, 26, 10, tzinfo=timezone.utc),
    )

    assert result.intent is not None
    assert result.intent.title is None
    assert result.intent.deadline == datetime(
        2026, 9, 27, 9, tzinfo=timezone.utc
    )
    assert IntentIssue.AMBIGUOUS_TITLE not in result.issues


def test_validator_reports_conflicting_explicit_priorities():
    result = validate_extraction(
        "High and low priority: submit the form tomorrow at 9am",
        RawTaskExtraction(
            task_count=1,
            title="submit the form",
            title_evidence="submit the form",
            priority=TaskPriority.LOW,
            priority_evidence="low priority",
            deadline=datetime(2026, 9, 27, 9, tzinfo=timezone.utc),
            deadline_evidence="tomorrow at 9am",
        ),
        now=datetime(2026, 9, 26, 10, tzinfo=timezone.utc),
    )

    assert result.intent is not None
    assert result.intent.priority is None
    assert result.intent.deadline == datetime(
        2026, 9, 27, 9, tzinfo=timezone.utc
    )
    assert IntentIssue.CONFLICTING_DETAILS in result.issues


def test_validator_applies_target_date_daylight_saving_offset():
    london = ZoneInfo("Europe/London")
    result = validate_extraction(
        "Submit the form tomorrow at 9am",
        RawTaskExtraction(
            task_count=1,
            title="Submit the form",
            title_evidence="Submit the form",
            deadline=datetime(2026, 10, 25, 9, tzinfo=london),
            deadline_evidence="tomorrow at 9am",
        ),
        now=datetime(2026, 10, 24, 10, tzinfo=london),
    )

    assert result.intent is not None
    assert result.intent.deadline == datetime(2026, 10, 25, 9, tzinfo=london)
    assert result.intent.deadline.utcoffset() == timezone.utc.utcoffset(None)


def test_validator_rejects_mixed_conflicting_date_expressions():
    result = validate_extraction(
        "Submit the report tomorrow or Monday at 3pm",
        RawTaskExtraction(
            task_count=1,
            title="Submit the report",
            title_evidence="Submit the report",
            deadline=datetime(2026, 9, 27, 15, tzinfo=timezone.utc),
            deadline_evidence="tomorrow at 3pm",
        ),
        now=datetime(2026, 9, 26, 10, tzinfo=timezone.utc),
    )

    assert result.intent is not None
    assert result.intent.deadline is None
    assert IntentIssue.CONFLICTING_DETAILS in result.issues


def test_validator_rejects_conflicting_explicit_dates():
    result = validate_extraction(
        "Submit the report 4 October or 5 October at 3pm",
        RawTaskExtraction(
            task_count=1,
            title="Submit the report",
            title_evidence="Submit the report",
            deadline=datetime(2026, 10, 4, 15, tzinfo=timezone.utc),
            deadline_evidence="4 October at 3pm",
        ),
        now=datetime(2026, 9, 26, 10, tzinfo=timezone.utc),
    )

    assert result.intent is not None
    assert result.intent.deadline is None
    assert IntentIssue.CONFLICTING_DETAILS in result.issues


def test_validator_rejects_dates_joined_by_and():
    result = validate_extraction(
        "Submit the report Monday and Tuesday at 3pm",
        RawTaskExtraction(
            task_count=1,
            title="Submit the report",
            title_evidence="Submit the report",
            deadline=datetime(2026, 9, 28, 15, tzinfo=timezone.utc),
            deadline_evidence="Monday at 3pm",
        ),
        now=datetime(2026, 9, 26, 10, tzinfo=timezone.utc),
    )

    assert result.intent is not None
    assert result.intent.deadline is None
    assert IntentIssue.CONFLICTING_DETAILS in result.issues


def test_validator_rejects_unbounded_relative_day_count():
    result = validate_extraction(
        "Do x in 999999999999999999999 days at 3pm",
        RawTaskExtraction(
            task_count=1,
            title="Do x",
            title_evidence="Do x",
            deadline=datetime(2026, 9, 27, 15, tzinfo=timezone.utc),
            deadline_evidence="in 999999999999999999999 days at 3pm",
        ),
        now=datetime(2026, 9, 26, 10, tzinfo=timezone.utc),
    )

    assert result.intent is not None
    assert result.intent.deadline is None
    assert IntentIssue.AMBIGUOUS_DEADLINE in result.issues
