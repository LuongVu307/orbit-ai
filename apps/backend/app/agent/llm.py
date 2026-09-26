from abc import ABC, abstractmethod

from app.agent.intent import UnderstandingResult


class LLM(ABC):
    @abstractmethod
    def understand(self, message: str) -> UnderstandingResult | None:
        pass
