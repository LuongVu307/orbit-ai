import requests
import json

from app.agent.intent import TaskIntent
from app.agent.llm import LLM


class LocalLLM(LLM):
    def __init__(self, model: str = "gemma3"):
        self.model = model
        self.url = "http://localhost:11434/api/chat"

    def understand(self, message: str) -> TaskIntent | None:
        response = requests.post(
            self.url,
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": """
                You convert user requests into Orbit task intents.

                Return ONLY valid JSON with these fields:
                - action: "create_task"
                - title: string
                - deadline: ISO 8601 datetime or null

                If the user is not asking to create a task, return null.
                """,
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ],
                "format": "json",
                "stream": False,
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
