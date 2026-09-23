from sqlalchemy.orm import Session

from app.agent.draft import ConversationState, ConversationStatus
from app.agent.intent import TaskIntent
from app.domain.task import TaskPriority
from app.agent.llm import LLM
from app.agent.result import AgentClarification, AgentProposal, AgentResponse
from app.services.task_service import create_task


REQUIRED_TASK_FIELDS = ("title", "deadline")


class Agent:
    def __init__(self, llm: LLM):
        self.llm = llm
        # Conversation persistence is intentionally deferred for this MVP.
        self.conversation = ConversationState()

    def understand(self, message: str) -> TaskIntent | None:
        return self.llm.understand(message)

    def propose(self, message: str) -> AgentResponse | None:
        """Compatibility entry point for callers that only collect/propose."""
        return self.handle_message(message)

    def handle_message(
        self,
        message: str,
        db: Session | None = None,
    ) -> AgentResponse | None:
        if self.conversation.status == ConversationStatus.READY_FOR_CONFIRMATION:
            return self._handle_confirmation(message, db)
        if self.conversation.status in {
            ConversationStatus.CANCELLED,
            ConversationStatus.EXECUTED,
        }:
            self.conversation = ConversationState()

        intent = self.understand(message)
        if intent is None:
            return None

        self._merge_intent(intent)
        return self._response_for_current_draft()

    def _response_for_current_draft(self) -> AgentResponse:
        missing_fields = self._missing_required_fields()
        if missing_fields:
            self.conversation.status = ConversationStatus.COLLECTING
            return AgentResponse(
                clarification=AgentClarification(
                    question=self._clarification_question(missing_fields),
                    missing_fields=missing_fields,
                ),
                status=self.conversation.status,
            )

        self.conversation.status = ConversationStatus.READY_FOR_CONFIRMATION
        return AgentResponse(
            proposal=AgentProposal(draft_task=self.conversation.draft_task),
            status=self.conversation.status,
        )

    def execute_proposal(
        self,
        db: Session | None,
        proposal: AgentProposal,
        approved: bool,
    ):
        if not approved:
            self.conversation.status = ConversationStatus.CANCELLED
            return None
        if db is None:
            return None
        if self.conversation.status != ConversationStatus.READY_FOR_CONFIRMATION:
            return None
        if proposal.draft_task != self.conversation.draft_task:
            return None

        self.conversation.status = ConversationStatus.CONFIRMED
        task = create_task(
            db,
            title=proposal.draft_task.title,
            description=proposal.draft_task.description,
            priority=proposal.draft_task.priority or TaskPriority.MEDIUM,
            deadline=proposal.draft_task.deadline,
        )
        self.conversation.status = ConversationStatus.EXECUTED
        return task

    def _handle_confirmation(
        self,
        message: str,
        db: Session | None,
    ) -> AgentResponse:
        answer = message.strip().lower()
        if answer in {"yes", "y", "confirm"}:
            proposal = AgentProposal(draft_task=self.conversation.draft_task)
            task = self.execute_proposal(db, proposal, approved=True)
            if task is not None:
                return AgentResponse(
                    status=self.conversation.status,
                    executed_task_id=task.id,
                )
        if answer in {"no", "n", "cancel"}:
            self.conversation.status = ConversationStatus.CANCELLED
            return AgentResponse(status=self.conversation.status)

        intent = self.understand(message)
        if intent is not None:
            self._merge_intent(intent)
            return self._response_for_current_draft()

        return AgentResponse(
            clarification=AgentClarification(
                question=(
                    "Please confirm, cancel, or describe what you would like "
                    "to change."
                ),
                missing_fields=[],
            ),
            status=self.conversation.status,
        )

    def _merge_intent(self, intent: TaskIntent) -> None:
        values = intent.model_dump(exclude_none=True, exclude={"action"})
        self.conversation.draft_task = self.conversation.draft_task.model_copy(
            update=values
        )

    def _missing_required_fields(self) -> list[str]:
        return [
            field
            for field in REQUIRED_TASK_FIELDS
            if getattr(self.conversation.draft_task, field) is None
        ]

    @staticmethod
    def _clarification_question(missing_fields: list[str]) -> str:
        return f"Please provide: {', '.join(missing_fields)}."
