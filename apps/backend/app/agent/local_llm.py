import requests
import json
from datetime import datetime, timedelta
from typing import Callable

from app.agent.intent import TaskIntent
from app.agent.llm import LLM


PROMPT_VERSION = "1"


class LocalLLM(LLM):
    def __init__(
        self,
        model: str = "gemma3",
        *,
        now_provider: Callable[[], datetime] | None = None,
        request_timeout_seconds: float = 30,
    ):
        self.model = model
        self.url = "http://localhost:11434/api/chat"
        self.prompt_version = PROMPT_VERSION
        self._now_provider = now_provider or (lambda: datetime.now().astimezone())
        self.request_timeout_seconds = request_timeout_seconds

    def understand(self, message: str) -> TaskIntent | None:
        now = self._now_provider()
        current_datetime = now.isoformat()
        upcoming_dates = "\n".join(
            (now + timedelta(days=offset)).strftime("%A: %Y-%m-%d")
            for offset in range(15)
        )
        nearest_weekdays = "\n".join(
            (now + timedelta(days=offset)).strftime("%A: %Y-%m-%d")
            for offset in range(1, 8)
        )
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": f"""
                You convert user requests into Orbit task intents.

                The current local date and time is {current_datetime}.
                Resolve relative dates using this value.
                Use this calendar when resolving named weekdays:
                {upcoming_dates}

                The nearest upcoming occurrence of each weekday is:
                {nearest_weekdays}
                When the user names a weekday without saying "next", use the
                date in this nearest-upcoming list.

                Return ONLY valid JSON with these fields:
                - action: "create_task" (optional)
                - title: string or null
                - description: string or null
                - priority: "low", "medium", "high", or null
                - deadline: ISO 8601 datetime or null

                Extract only facts expressed in this message. A follow-up may
                contain just one field, such as a deadline. If no task facts
                can be extracted, return null.

                If the message contains no date, weekday, relative date, or
                time expression, deadline MUST be null. Never invent a date.

                Never infer a priority. Priority must be null unless the user
                explicitly states a priority in the message.
                """,
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ],
                "format": "json",
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
        return self._parse_content(content)

    @staticmethod
    def _parse_content(content: str) -> TaskIntent | None:
        try:
            parsed = json.loads(content)
            return TaskIntent.model_validate(parsed)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
