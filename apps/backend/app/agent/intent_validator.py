import re
from collections.abc import Iterable
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.agent.extraction import RawTaskExtraction
from app.agent.intent import (
    AgentAction,
    IntentIssue,
    TaskIntent,
    UnderstandingResult,
)
from app.domain.task import TaskPriority


DEFAULT_TIMEZONE = ZoneInfo("Europe/London")
MAX_RELATIVE_DAYS = 3650
DATE_EXPRESSION = re.compile(
    r"("
    r"\b(today|tomorrow|tonight|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"next\s+(week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"in\s+\d+\s+days?)\b|"
    r"\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b|"
    r"\b\d{4}-\d{2}-\d{2}\b|"
    r"\b\d{1,2}\s+"
    r"(january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\b"
    r")",
    re.IGNORECASE,
)
TIME_EXPRESSION = re.compile(
    r"("
    r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b|"
    r"\b([01]?\d|2[0-3]):[0-5]\d\b|"
    r"\b(noon|midnight)\b"
    r")",
    re.IGNORECASE,
)
VAGUE_DEADLINE = re.compile(
    r"\b(later|sometime|whenever|after work|this weekend|next weekend)\b",
    re.IGNORECASE,
)
PRIORITY_EXPRESSIONS = {
    TaskPriority.HIGH: re.compile(
        r"\b(high\s+priority|priority\s*(is|:)?\s*high)\b",
        re.IGNORECASE,
    ),
    TaskPriority.MEDIUM: re.compile(
        r"\b(medium\s+priority|priority\s*(is|:)?\s*medium)\b",
        re.IGNORECASE,
    ),
    TaskPriority.LOW: re.compile(
        r"\b(low\s+priority|priority\s*(is|:)?\s*low)\b",
        re.IGNORECASE,
    ),
}
CONFLICTING_PRIORITY_EXPRESSION = re.compile(
    r"\b(low|medium|high)\s+(and|or)\s+(low|medium|high)\s+priority\b",
    re.IGNORECASE,
)
FIELD_UPDATE_EXPRESSION = re.compile(
    r"^\s*(change|set|make|move)\s+(it|that)\s+(to|for)\b",
    re.IGNORECASE,
)
TASK_CONJUNCTION_EXPRESSION = re.compile(
    r"\b(?:and|then)\b",
    re.IGNORECASE,
)
SINGLE_TASK_COMPOUND_EXPRESSION = re.compile(
    r"\b(?:research and development|health and safety|"
    r"sales and marketing|terms and conditions)\b",
    re.IGNORECASE,
)
WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def _supported_evidence(message: str, evidence: str | None) -> bool:
    if not evidence or not evidence.strip():
        return False
    return _normalized(evidence) in _normalized(message)


def _without_task_metadata(value: str) -> str:
    value = DATE_EXPRESSION.sub(" ", value)
    value = TIME_EXPRESSION.sub(" ", value)
    for pattern in PRIORITY_EXPRESSIONS.values():
        value = pattern.sub(" ", value)
    return value


def _has_multiple_task_shape(message: str) -> bool:
    """Conservatively reject substantial conjunction clauses."""

    scan_message = CONFLICTING_PRIORITY_EXPRESSION.sub(
        lambda match: " " * len(match.group(0)),
        message,
    )
    scan_message = SINGLE_TASK_COMPOUND_EXPRESSION.sub(
        lambda match: " " * len(match.group(0)),
        scan_message,
    )
    conjunctions = list(TASK_CONJUNCTION_EXPRESSION.finditer(scan_message))
    for index, conjunction in enumerate(conjunctions):
        clause_end = (
            conjunctions[index + 1].start()
            if index + 1 < len(conjunctions)
            else len(message)
        )
        raw_clause = message[conjunction.start():clause_end]
        clause = _without_task_metadata(raw_clause)
        meaningful_words = [
            word.casefold()
            for word in re.findall(r"[A-Za-z][A-Za-z'-]*", clause)
            if word.casefold() not in {"and", "then", "at", "by", "on"}
        ]
        if meaningful_words:
            return True
    return False


def _has_alternative_expressions(message: str, pattern: re.Pattern) -> bool:
    matches = list(pattern.finditer(message))
    return any(
        re.search(
            r"\b(?:and|or)\b",
            message[first.end():second.start()],
            re.IGNORECASE,
        )
        for first, second in zip(matches, matches[1:])
    )


def _append_unique(
    values: list[IntentIssue],
    additions: Iterable[IntentIssue],
) -> None:
    for addition in additions:
        if addition not in values:
            values.append(addition)


def _resolve_date(evidence: str, now: datetime) -> date | None:
    normalized = _normalized(evidence)
    if re.search(r"\btoday\b", normalized):
        return now.date()
    if re.search(r"\btomorrow\b", normalized):
        return (now + timedelta(days=1)).date()

    relative_match = re.search(r"\bin\s+(\d+)\s+days?\b", normalized)
    if relative_match:
        try:
            days = int(relative_match.group(1))
        except ValueError:
            return None
        if days > MAX_RELATIVE_DAYS:
            return None
        return (now + timedelta(days=days)).date()

    iso_match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", normalized)
    if iso_match:
        return date(*(int(part) for part in iso_match.groups()))

    numeric_match = re.search(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
        normalized,
    )
    if numeric_match:
        day, month, year = (int(part) for part in numeric_match.groups())
        if year < 100:
            year += 2000
        return date(year, month, day)

    month_match = re.search(
        r"\b(\d{1,2})\s+(" + "|".join(MONTHS) + r")\b",
        normalized,
    )
    if month_match:
        day = int(month_match.group(1))
        month = MONTHS[month_match.group(2)]
        year = now.year
        resolved = date(year, month, day)
        if resolved < now.date():
            resolved = date(year + 1, month, day)
        return resolved

    for name, weekday in WEEKDAYS.items():
        if re.search(rf"\b{name}\b", normalized):
            days_ahead = (weekday - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (now + timedelta(days=days_ahead)).date()
    return None


def _resolve_time(evidence: str) -> time | None:
    normalized = _normalized(evidence)
    if re.search(r"\bnoon\b", normalized):
        return time(12, 0)
    if re.search(r"\bmidnight\b", normalized):
        return time(0, 0)

    twelve_hour = re.search(
        r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
        normalized,
    )
    if twelve_hour:
        hour = int(twelve_hour.group(1))
        minute = int(twelve_hour.group(2) or 0)
        if hour < 1 or hour > 12 or minute > 59:
            return None
        if twelve_hour.group(3) == "am":
            hour %= 12
        else:
            hour = (hour % 12) + 12
        return time(hour, minute)

    twenty_four_hour = re.search(
        r"\b([01]?\d|2[0-3]):([0-5]\d)\b",
        normalized,
    )
    if twenty_four_hour:
        return time(
            int(twenty_four_hour.group(1)),
            int(twenty_four_hour.group(2)),
        )
    return None


def _resolve_deadline(evidence: str, now: datetime) -> datetime | None:
    try:
        resolved_date = _resolve_date(evidence, now)
    except (OverflowError, ValueError):
        return None
    resolved_time = _resolve_time(evidence)
    if resolved_date is None or resolved_time is None:
        return None
    timezone = now.tzinfo or DEFAULT_TIMEZONE
    return datetime.combine(resolved_date, resolved_time, tzinfo=timezone)


def validate_extraction(
    message: str,
    extraction: RawTaskExtraction,
    now: datetime | None = None,
) -> UnderstandingResult:
    """Convert untrusted model output into supported user facts."""

    issues = list(extraction.issues)
    rejected_fields: list[str] = []

    if (
        extraction.task_count > 1
        or _has_multiple_task_shape(message)
    ):
        _append_unique(issues, [IntentIssue.MULTIPLE_TASKS])
    if (
        extraction.task_count == 0
        or IntentIssue.UNSUPPORTED_REQUEST in issues
    ):
        _append_unique(issues, [IntentIssue.UNSUPPORTED_REQUEST])

    if IntentIssue.MULTIPLE_TASKS in issues:
        return UnderstandingResult(
            issues=issues,
            rejected_fields=rejected_fields,
        )
    if IntentIssue.UNSUPPORTED_REQUEST in issues:
        return UnderstandingResult(
            issues=issues,
            rejected_fields=rejected_fields,
        )

    is_field_update = FIELD_UPDATE_EXPRESSION.search(message) is not None
    title = None
    if extraction.title is not None and not is_field_update:
        if _supported_evidence(message, extraction.title_evidence):
            title = extraction.title_evidence.strip().rstrip(".")
        else:
            rejected_fields.append("title")
    if extraction.task_count == 1 and title is None and not is_field_update:
        _append_unique(issues, [IntentIssue.AMBIGUOUS_TITLE])
    elif title is not None and IntentIssue.AMBIGUOUS_TITLE in issues:
        issues.remove(IntentIssue.AMBIGUOUS_TITLE)

    description = None
    if extraction.description is not None:
        duplicates_title = (
            title is not None
            and extraction.description_evidence is not None
            and _normalized(extraction.description_evidence)
            == _normalized(title)
        )
        contains_other_task_fields = (
            DATE_EXPRESSION.search(extraction.description_evidence or "")
            is not None
            or TIME_EXPRESSION.search(extraction.description_evidence or "")
            is not None
            or any(
                pattern.search(extraction.description_evidence or "")
                for pattern in PRIORITY_EXPRESSIONS.values()
            )
        )
        if (
            _supported_evidence(message, extraction.description_evidence)
            and not duplicates_title
            and not contains_other_task_fields
        ):
            description = extraction.description_evidence.strip()
        else:
            rejected_fields.append("description")

    priority = None
    explicit_priorities = [
        value
        for value, pattern in PRIORITY_EXPRESSIONS.items()
        if pattern.search(message)
    ]
    has_priority_conflict = (
        len(explicit_priorities) > 1
        or CONFLICTING_PRIORITY_EXPRESSION.search(message)
        is not None
    )
    if has_priority_conflict:
        _append_unique(issues, [IntentIssue.CONFLICTING_DETAILS])
    if extraction.priority is not None:
        pattern = PRIORITY_EXPRESSIONS[extraction.priority]
        if (
            _supported_evidence(message, extraction.priority_evidence)
            and pattern.search(extraction.priority_evidence)
        ):
            if IntentIssue.CONFLICTING_DETAILS not in issues:
                priority = extraction.priority
        else:
            rejected_fields.append("priority")
    if (
        len(explicit_priorities) == 1
        and IntentIssue.CONFLICTING_DETAILS not in issues
    ):
        priority = explicit_priorities[0]
    if explicit_priorities and priority not in explicit_priorities:
        _append_unique(issues, [IntentIssue.AMBIGUOUS_PRIORITY])
    elif priority is not None and IntentIssue.AMBIGUOUS_PRIORITY in issues:
        issues.remove(IntentIssue.AMBIGUOUS_PRIORITY)

    now = now or datetime.now(DEFAULT_TIMEZONE)
    deadline = None
    has_date = DATE_EXPRESSION.search(message) is not None
    has_time = TIME_EXPRESSION.search(message) is not None
    has_vague_deadline = VAGUE_DEADLINE.search(message) is not None
    has_deadline_conflict = (
        _has_alternative_expressions(message, DATE_EXPRESSION)
        or _has_alternative_expressions(message, TIME_EXPRESSION)
    )
    if has_deadline_conflict:
        _append_unique(issues, [IntentIssue.CONFLICTING_DETAILS])
    if (
        extraction.deadline_evidence is not None
        and (
            IntentIssue.CONFLICTING_DETAILS not in issues
            or (has_priority_conflict and not has_deadline_conflict)
        )
    ):
        if _supported_evidence(message, extraction.deadline_evidence):
            deadline = _resolve_deadline(extraction.deadline_evidence, now)
        if deadline is None and extraction.deadline is not None:
            rejected_fields.append("deadline")
    if (has_date != has_time) or has_vague_deadline:
        _append_unique(issues, [IntentIssue.AMBIGUOUS_DEADLINE])
    elif has_date and has_time and deadline is None:
        _append_unique(issues, [IntentIssue.AMBIGUOUS_DEADLINE])
    elif deadline is not None and IntentIssue.AMBIGUOUS_DEADLINE in issues:
        issues.remove(IntentIssue.AMBIGUOUS_DEADLINE)

    intent = TaskIntent(
        action=extraction.action or AgentAction.CREATE_TASK,
        title=title,
        description=description,
        priority=priority,
        deadline=deadline,
    )
    if not intent.model_dump(exclude_none=True, exclude={"action"}):
        intent = None

    return UnderstandingResult(
        intent=intent,
        issues=issues,
        rejected_fields=rejected_fields,
    )
