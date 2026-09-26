import argparse
import json
from datetime import datetime
from pathlib import Path

import requests

from app.agent.local_llm import (
    LEGACY_PROMPT_VERSION,
    PROMPT_VERSION,
    LocalLLM,
)
from evals.scoring import score_case, summarize_results


DEFAULT_CASES = Path(__file__).parent / "cases" / "intent-v1.json"


def load_corpus(path: Path) -> dict:
    corpus = json.loads(path.read_text(encoding="utf-8"))
    if corpus.get("schema_version") != 1:
        raise ValueError("Unsupported intent corpus schema version")
    if not isinstance(corpus.get("cases"), list) or not corpus["cases"]:
        raise ValueError("Intent corpus must contain at least one case")
    return corpus


def run_evaluations(
    model: str,
    prompt_version: str,
    cases_path: Path = DEFAULT_CASES,
    limit: int | None = None,
) -> dict:
    corpus = load_corpus(cases_path)
    fixed_now = datetime.fromisoformat(corpus["fixed_now"])
    llm = LocalLLM(
        model=model,
        prompt_version=prompt_version,
        now_provider=lambda: fixed_now,
    )
    cases = corpus["cases"][:limit] if limit else corpus["cases"]
    results = []

    for case in cases:
        try:
            understanding = llm.understand(case["message"])
            result = score_case(case, understanding)
            result["error"] = None
        except (requests.RequestException, KeyError, TypeError, ValueError) as error:
            result = score_case(case, None)
            result["passed"] = False
            result["error"] = str(error)
        results.append(result)

    malformed = LocalLLM._parse_content(
        "not JSON",
        source_message="test",
        prompt_version=prompt_version,
    )
    malformed_result = {
        "name": "malformed_output",
        "category": "adapter",
        "input": "not JSON",
        "passed": malformed is None,
        "checks": [
            {
                "name": "safe_parse_failure",
                "passed": malformed is None,
                "expected": None,
                "actual": (
                    malformed.model_dump(mode="json")
                    if malformed is not None
                    else None
                ),
            }
        ],
        "output": None,
        "prohibited_inferences": [],
        "error": None,
    }
    results.append(malformed_result)
    summary = summarize_results(results)

    return {
        "evaluated_at": datetime.now().astimezone().isoformat(),
        "corpus": str(cases_path),
        "corpus_schema_version": corpus["schema_version"],
        "fixed_now": corpus["fixed_now"],
        "model": llm.model,
        "prompt_version": llm.prompt_version,
        "passed": summary["passed"] == summary["total"],
        "summary": summary,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run advisory live Ollama intent evaluations."
    )
    parser.add_argument("--model", default="gemma3")
    parser.add_argument(
        "--prompt-version",
        choices=(LEGACY_PROMPT_VERSION, PROMPT_VERSION),
        default=PROMPT_VERSION,
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = run_evaluations(
        args.model,
        args.prompt_version,
        args.cases,
        args.limit,
    )
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")

    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
