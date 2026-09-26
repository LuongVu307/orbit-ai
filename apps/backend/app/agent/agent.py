from app.agent.draft import ConversationState, ConversationStatus
from app.agent.intent import IntentIssue, TaskIntent, UnderstandingResult
from app.agent.llm import LLM
from app.agent.result import AgentClarification, AgentProposal, AgentResponse


REQUIRED_TASK_FIELDS = ("title", "deadline")


class Agent:
    def __init__(self, llm: LLM):
        self.llm = llm

    def understand(self, message: str) -> TaskIntent | None:
        result = self.llm.understand(message)
        return result.intent if result else None

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

        understanding = self.llm.understand(message)
        if understanding is None:
            return None

        if understanding.intent is not None:
            self._merge_intent(conversation, understanding.intent)
        if understanding.issues:
            return self._response_for_issues(conversation, understanding)
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

        understanding = self.llm.understand(message)
        if understanding is not None:
            if understanding.intent is not None:
                self._merge_intent(conversation, understanding.intent)
            if understanding.issues:
                confirmation_noise = {
                    IntentIssue.UNSUPPORTED_REQUEST,
                    IntentIssue.AMBIGUOUS_TITLE,
                }
                if (
                    understanding.intent is None
                    and IntentIssue.UNSUPPORTED_REQUEST
                    in understanding.issues
                    and set(understanding.issues) <= confirmation_noise
                ):
                    return self._confirmation_clarification(conversation)
                return self._response_for_issues(conversation, understanding)
            return self.response_for_state(conversation)

        return self._confirmation_clarification(conversation)

    @staticmethod
    def _confirmation_clarification(
        conversation: ConversationState,
    ) -> AgentResponse:
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

    def _response_for_issues(
        self,
        conversation: ConversationState,
        understanding: UnderstandingResult,
    ) -> AgentResponse:
        relevant_issues = list(understanding.issues)
        if conversation.draft_task.title is not None:
            relevant_issues = [
                issue
                for issue in relevant_issues
                if issue != IntentIssue.AMBIGUOUS_TITLE
            ]
        if not relevant_issues:
            return self.response_for_state(conversation)

        priority = (
            IntentIssue.MULTIPLE_TASKS,
            IntentIssue.CONFLICTING_DETAILS,
            IntentIssue.AMBIGUOUS_DEADLINE,
            IntentIssue.AMBIGUOUS_PRIORITY,
            IntentIssue.AMBIGUOUS_TITLE,
            IntentIssue.UNSUPPORTED_REQUEST,
        )
        issue = next(item for item in priority if item in relevant_issues)
        questions = {
            IntentIssue.MULTIPLE_TASKS: (
                "I found more than one task. Which one should we capture first?"
            ),
            IntentIssue.CONFLICTING_DETAILS: (
                "I found conflicting details. Which option should I use?"
            ),
            IntentIssue.AMBIGUOUS_DEADLINE: (
                "What exact date and time should I use for the deadline?"
            ),
            IntentIssue.AMBIGUOUS_PRIORITY: (
                "What priority should I use: low, medium, or high?"
            ),
            IntentIssue.AMBIGUOUS_TITLE: (
                "What task would you like me to capture?"
            ),
            IntentIssue.UNSUPPORTED_REQUEST: (
                "I can capture one task at a time. What would you like to accomplish?"
            ),
        }
        missing_fields = {
            IntentIssue.AMBIGUOUS_DEADLINE: ["deadline"],
            IntentIssue.AMBIGUOUS_PRIORITY: ["priority"],
            IntentIssue.AMBIGUOUS_TITLE: ["title"],
        }.get(issue, [])
        conversation.status = ConversationStatus.COLLECTING
        return AgentResponse(
            clarification=AgentClarification(
                question=questions[issue],
                missing_fields=missing_fields,
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
