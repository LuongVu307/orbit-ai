from abc import ABC, abstractmethod

from app.agent.intent import TaskIntent


class LLM(ABC):
    @abstractmethod
    def understand(self, message: str) -> TaskIntent | None:
        pass