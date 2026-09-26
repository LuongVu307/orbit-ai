from collections import defaultdict
from typing import Any

from app.agent.intent import UnderstandingResult


TASK_FIELDS = ("title", "description", "priority", "deadline")


def _normalized(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.casefold().strip().rstrip("?.").split())
    return value


def _actual_fields(result: UnderstandingResult | None) -> dict[str, Any]:
    if result is None or result.intent is None:
        return {field: None for field in TASK_FIELDS}
    dumped = result.intent.model_dump(mode="json")
    return {field: dumped.get(field) for field in TASK_FIELDS}


def score_case(case: dict, result: UnderstandingResult | None) -> dict:
    expected = case["expected"]
    expected_intent = expected.get("intent")
    actual = _actual_fields(result)
    checks: list[dict] = []

    if expected_intent is None:
        checks.append(
            {
                "name": "intent_absent",
                "passed": result is not None and result.intent is None,
            }
        )
    else:
        for field, expected_value in expected_intent.items():
            checks.append(
                {
                    "name": field,
                    "passed": _normalized(actual[field])
                    == _normalized(expected_value),
                    "expected": expected_value,
                    "actual": actual[field],
                }
            )

    for field in expected.get("null_fields", []):
        checks.append(
            {
                "name": field,
                "passed": actual[field] is None,
                "expected": None,
                "actual": actual[field],
            }
        )

    actual_issues = {
        issue.value for issue in (result.issues if result else [])
    }
    for issue in expected.get("required_issues", []):
        checks.append(
            {
                "name": f"issue:{issue}",
                "passed": issue in actual_issues,
                "expected": True,
                "actual": issue in actual_issues,
            }
        )
    if not expected.get("required_issues"):
        checks.append(
            {
                "name": "no_issues",
                "passed": not actual_issues,
                "expected": [],
                "actual": sorted(actual_issues),
            }
        )

    prohibited_inferences = [
        field
        for field in ("deadline", "priority", "description")
        if field in expected.get("null_fields", []) and actual[field] is not None
    ]
    return {
        "name": case["name"],
        "category": case["category"],
        "input": case["message"],
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "output": (
            result.model_dump(mode="json") if result is not None else None
        ),
        "prohibited_inferences": prohibited_inferences,
    }


def summarize_results(results: list[dict]) -> dict:
    categories: dict[str, dict[str, int]] = defaultdict(
        lambda: {"passed": 0, "total": 0}
    )
    fields: dict[str, dict[str, int]] = defaultdict(
        lambda: {"passed": 0, "total": 0}
    )
    prohibited_inferences = 0

    for result in results:
        category = categories[result["category"]]
        category["total"] += 1
        category["passed"] += int(result["passed"])
        prohibited_inferences += len(result["prohibited_inferences"])
        for check in result["checks"]:
            name = check["name"]
            if name in TASK_FIELDS:
                fields[name]["total"] += 1
                fields[name]["passed"] += int(check["passed"])

    passed = sum(result["passed"] for result in results)
    return {
        "passed": passed,
        "total": len(results),
        "pass_rate": passed / len(results) if results else 0,
        "prohibited_inferences": prohibited_inferences,
        "categories": dict(categories),
        "fields": dict(fields),
    }
