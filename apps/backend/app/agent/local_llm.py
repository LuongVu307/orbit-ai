import requests
import json
from datetime import datetime, timedelta

from app.agent.intent import TaskIntent
from app.agent.llm import LLM


class LocalLLM(LLM):
    def __init__(self, model: str = "gemma3"):
        self.model = model
        self.url = "http://localhost:11434/api/chat"

    def understand(self, message: str) -> TaskIntent | None:
        now = datetime.now().astimezone()
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
        )

        response.raise_for_status()

        data = response.json()

        content = data["message"]["content"]
        try:
            parsed = json.loads(content)
            return TaskIntent.model_validate(parsed)
        except (json.JSONDecodeError, ValueError):
            return None
