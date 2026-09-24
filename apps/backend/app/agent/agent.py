from app.agent.draft import ConversationState, ConversationStatus
from app.agent.intent import TaskIntent
from app.agent.llm import LLM
from app.agent.result import AgentClarification, AgentProposal, AgentResponse


REQUIRED_TASK_FIELDS = ("title", "deadline")


class Agent:
    def __init__(self, llm: LLM):
        self.llm = llm

    def understand(self, message: str) -> TaskIntent | None:
        return self.llm.understand(message)

    def propose(
        self,
        message: str,
        conversation: ConversationState | None = None,
    ) -> AgentResponse | None:
        """Compatibility entry point for callers that only collect/propose."""
        return self.handle_message(message, conversation or ConversationState())

    def handle_message(
        self,
        message: str,
        conversation: ConversationState,
    ) -> AgentResponse | None:
        if conversation.status == ConversationStatus.READY_FOR_CONFIRMATION:
            return self._handle_confirmation(message, conversation)
        if conversation.status in {ConversationStatus.CANCELLED, ConversationStatus.EXECUTED}:
            return AgentResponse(status=conversation.status)

        intent = self.understand(message)
        if intent is None:
            return None

        self._merge_intent(conversation, intent)
        return self.response_for_state(conversation)

    def response_for_state(self, conversation: ConversationState) -> AgentResponse:
        if conversation.status in {
            ConversationStatus.CANCELLED,
            ConversationStatus.CONFIRMED,
            ConversationStatus.EXECUTED,
        }:
            return AgentResponse(status=conversation.status)

        missing_fields = self._missing_required_fields(conversation)
        if missing_fields:
            conversation.status = ConversationStatus.COLLECTING
            return AgentResponse(
                clarification=AgentClarification(
                    question=self._clarification_question(missing_fields),
                    missing_fields=missing_fields,
                ),
                status=conversation.status,
            )

        conversation.status = ConversationStatus.READY_FOR_CONFIRMATION
        return AgentResponse(
            proposal=AgentProposal(draft_task=conversation.draft_task),
            status=conversation.status,
        )

    def _handle_confirmation(
        self,
        message: str,
        conversation: ConversationState,
    ) -> AgentResponse:
        answer = message.strip().lower()
        if answer in {"yes", "y", "confirm"}:
            conversation.status = ConversationStatus.CONFIRMED
            return AgentResponse(status=conversation.status)
        if answer in {"no", "n", "cancel"}:
            conversation.status = ConversationStatus.CANCELLED
            return AgentResponse(status=conversation.status)

        intent = self.understand(message)
        if intent is not None:
            self._merge_intent(conversation, intent)
            return self.response_for_state(conversation)

        return AgentResponse(
            clarification=AgentClarification(
                question=(
                    "Please confirm, cancel, or describe what you would like "
                    "to change."
                ),
                missing_fields=[],
            ),
            status=conversation.status,
        )

    @staticmethod
    def _merge_intent(conversation: ConversationState, intent: TaskIntent) -> None:
        values = intent.model_dump(exclude_none=True, exclude={"action"})
        conversation.draft_task = conversation.draft_task.model_copy(
            update=values
        )

    @staticmethod
    def _missing_required_fields(conversation: ConversationState) -> list[str]:
        return [
            field
            for field in REQUIRED_TASK_FIELDS
            if getattr(conversation.draft_task, field) is None
        ]

    @staticmethod
    def _clarification_question(missing_fields: list[str]) -> str:
        return f"Please provide: {', '.join(missing_fields)}."
