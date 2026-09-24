import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import requests

from app.agent.intent import TaskIntent
from app.agent.local_llm import LocalLLM


@dataclass
class EvaluationResult:
    name: str
    source: str
    input: str
    passed: bool
    output: dict | None = None
    error: str | None = None


def nearest_weekday(now: datetime, weekday: int) -> datetime:
    days_ahead = (weekday - now.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return now + timedelta(days=days_ahead)


def run_live_case(
    llm: LocalLLM,
    name: str,
    message: str,
    check: Callable[[TaskIntent], bool],
) -> EvaluationResult:
    try:
        intent = llm.understand(message)
        output = intent.model_dump(mode="json") if intent else None
        return EvaluationResult(
            name=name,
            source="ollama",
            input=message,
            output=output,
            passed=intent is not None and check(intent),
        )
    except (requests.RequestException, KeyError, TypeError, ValueError) as error:
        return EvaluationResult(
            name=name,
            source="ollama",
            input=message,
            passed=False,
            error=str(error),
        )


def run_evaluations(model: str) -> dict:
    now = datetime.now().astimezone()
    llm = LocalLLM(model=model, now_provider=lambda: now)
    tomorrow = (now + timedelta(days=1)).date()
    friday = nearest_weekday(now, 4).date()

    cases = [
        (
            "relative_date",
            "Revise Dijkstra tomorrow at 3pm",
            lambda intent: (
                intent.deadline is not None
                and intent.deadline.date() == tomorrow
                and intent.deadline.hour == 15
            ),
        ),
        (
            "named_weekday",
            "Review algorithms Friday at 2pm",
            lambda intent: (
                intent.deadline is not None
                and intent.deadline.date() == friday
                and intent.deadline.hour == 14
            ),
        ),
        (
            "missing_deadline",
            "Learn Docker",
            lambda intent: (
                intent.title is not None
                and intent.description is None
                and intent.priority is None
                and intent.deadline is None
            ),
        ),
        (
            "explicit_priority",
            "High priority: submit the lab tomorrow",
            lambda intent: (
                intent.title is not None
                and intent.priority is not None
                and intent.priority.value == "high"
                and intent.deadline is not None
                and intent.deadline.date() == tomorrow
            ),
        ),
        (
            "prohibited_inference",
            "Read the operating systems paper",
            lambda intent: (
                intent.title is not None
                and intent.description is None
                and intent.deadline is None
                and intent.priority is None
            ),
        ),
    ]

    results = [
        run_live_case(llm, name, message, check)
        for name, message, check in cases
    ]
    results.append(
        EvaluationResult(
            name="malformed_output",
            source="adapter",
            input="not JSON",
            output=None,
            passed=LocalLLM._parse_content("not JSON") is None,
        )
    )

    return {
        "evaluated_at": now.isoformat(),
        "model": llm.model,
        "prompt_version": llm.prompt_version,
        "passed": all(result.passed for result in results),
        "results": [asdict(result) for result in results],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run advisory live Ollama evaluations.")
    parser.add_argument("--model", default="gemma3")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = run_evaluations(args.model)
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
