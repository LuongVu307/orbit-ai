import json
from datetime import datetime, timedelta
from typing import Callable

import requests

from app.agent.extraction import RawTaskExtraction
from app.agent.intent import TaskIntent, UnderstandingResult
from app.agent.intent_validator import DEFAULT_TIMEZONE, validate_extraction
from app.agent.llm import LLM


LEGACY_PROMPT_VERSION = "1"
PROMPT_VERSION = "2"
SUPPORTED_PROMPT_VERSIONS = {LEGACY_PROMPT_VERSION, PROMPT_VERSION}


class LocalLLM(LLM):
    def __init__(
        self,
        model: str = "gemma3",
        *,
        prompt_version: str = PROMPT_VERSION,
        now_provider: Callable[[], datetime] | None = None,
        request_timeout_seconds: float = 30,
    ):
        if prompt_version not in SUPPORTED_PROMPT_VERSIONS:
            raise ValueError(f"Unsupported prompt version: {prompt_version}")
        self.model = model
        self.url = "http://localhost:11434/api/chat"
        self.prompt_version = prompt_version
        self._now_provider = now_provider or (
            lambda: datetime.now(DEFAULT_TIMEZONE)
        )
        self.request_timeout_seconds = request_timeout_seconds

    def understand(self, message: str) -> UnderstandingResult | None:
        now = self._now_provider()
        response_format = (
            RawTaskExtraction.model_json_schema()
            if self.prompt_version == PROMPT_VERSION
            else "json"
        )
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": self._system_prompt(now),
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ],
                "format": response_format,
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=self.request_timeout_seconds,
        )
        response.raise_for_status()

        try:
            data = response.json()
        except ValueError:
            return None
        if not isinstance(data, dict):
            return None
        message_data = data.get("message")
        if not isinstance(message_data, dict):
            return None
        content = message_data.get("content")
        if not isinstance(content, str):
            return None
        return self._parse_content(
            content,
            source_message=message,
            prompt_version=self.prompt_version,
            now=now,
        )

    def _system_prompt(self, now: datetime) -> str:
        current_datetime = now.isoformat()
        upcoming_dates = "\n".join(
            (now + timedelta(days=offset)).strftime("%A: %Y-%m-%d")
            for offset in range(15)
        )
        nearest_weekdays = "\n".join(
            (now + timedelta(days=offset)).strftime("%A: %Y-%m-%d")
            for offset in range(1, 8)
        )
        calendar_context = f"""
The current local date and time is {current_datetime}.
Resolve relative dates using this value.
Use this calendar when resolving named weekdays:
{upcoming_dates}

The nearest upcoming occurrence of each weekday is:
{nearest_weekdays}
When the user names a weekday without saying "next", use the date in this
nearest-upcoming list.
"""
        if self.prompt_version == LEGACY_PROMPT_VERSION:
            return f"""
You convert user requests into Orbit task intents.

{calendar_context}

Return ONLY valid JSON with these fields:
- action: "create_task" (optional)
- title: string or null
- description: string or null
- priority: "low", "medium", "high", or null
- deadline: ISO 8601 datetime or null

Extract only facts expressed in this message. A follow-up may contain just one
field, such as a deadline. If no task facts can be extracted, return null.

If the message contains no date, weekday, relative date, or time expression,
deadline MUST be null. Never invent a date.

Never infer a priority. Priority must be null unless the user explicitly states
a priority in the message.
"""

        return f"""
You extract user-provided facts for Orbit. Your output is untrusted and will be
validated. Prefer null and an issue over guessing.

{calendar_context}

Return ONLY one valid JSON object with exactly these fields:
- action: "create_task" or null
- task_count: number of distinct tasks in this message
- title: concise task title or null
- title_evidence: the exact smallest user substring supporting title, or null
- description: explicit context or constraint, or null
- description_evidence: exact supporting user substring, or null
- priority: "low", "medium", "high", or null
- priority_evidence: exact supporting user substring, or null
- deadline: timezone-aware ISO 8601 datetime or null
- deadline_evidence: exact supporting user substring, or null
- issues: zero or more of "ambiguous_deadline", "ambiguous_priority",
  "ambiguous_title", "conflicting_details", "multiple_tasks",
  "unsupported_request"

Evidence must be copied exactly from the user message. Do not use this system
message, the clock, or the calendar as evidence.

Rules:
- Extract facts only from this user message. A follow-up may contain one field.
- For a task-field follow-up, use task_count 1 even when it has no title.
- Never invent a deadline, time, priority, description, or task.
- A deadline requires both an unambiguous date and time. Otherwise return a
  null deadline and include "ambiguous_deadline".
- Priority is valid only when the user explicitly says low, medium, or high
  priority.
- If the message contains more than one task, set task_count accordingly and
  include "multiple_tasks". Do not choose one.
- If dates or other important details conflict, include
  "conflicting_details". Do not choose one.
- For non-task conversation, use task_count 0 and "unsupported_request".
- Do not include fields beyond the exact schema.
"""

    @staticmethod
    def _parse_content(
        content: str,
        *,
        source_message: str = "",
        prompt_version: str = PROMPT_VERSION,
        now: datetime | None = None,
    ) -> UnderstandingResult | None:
        try:
            parsed = json.loads(content)
            if prompt_version == LEGACY_PROMPT_VERSION:
                if parsed is None:
                    return None
                return UnderstandingResult(
                    intent=TaskIntent.model_validate(parsed)
                )
            extraction = RawTaskExtraction.model_validate(parsed)
            return validate_extraction(source_message, extraction, now)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
