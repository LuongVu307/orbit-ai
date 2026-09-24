from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import AgentMessage, TaskCreate, AgentApproval
from app.agent.draft import ConversationStatus
from app.database.connection import get_db
from app.agent.agent import Agent
from app.agent.local_llm import LocalLLM
from app.services.task_service import create_task, get_tasks, complete_task
from app.services.conversation_service import (
    apply_conversation_state,
    conversation_state,
    create_conversation,
    get_conversation,
)
from app.domain.task import TaskPriority

app = FastAPI(title="Orbit AI")
agent = Agent(LocalLLM())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

@app.get("/")
def root():
    return {"message": "Orbit AI is running"}


@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    return {"database": result.scalar()}

@app.post("/tasks")
def create_task_endpoint(
    task: TaskCreate,
    db: Session = Depends(get_db),
):
    return create_task(
        db,
        title=task.title,
        description=task.description,
        priority=task.priority,
        deadline=task.deadline,
    )

@app.get("/tasks")
def get_tasks_endpoint(db: Session = Depends(get_db)):
    return get_tasks(db)

@app.patch("/tasks/{task_id}/complete")
def complete_task_endpoint(
    task_id: int,
    db: Session = Depends(get_db),
):
    task = complete_task(db, task_id)

    if task is None:
        return {"error": "Task not found"}

    return task

@app.post("/agent/message")
def agent_message(
    request: AgentMessage,
    db: Session = Depends(get_db),
):
    conversation = None
    if request.conversation_id is not None:
        conversation = get_conversation(
            db, request.conversation_id, for_update=True
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = create_conversation(db)

    if conversation.status == ConversationStatus.EXECUTED.value:
        response = agent.response_for_state(conversation_state(conversation))
        response.conversation_id = conversation.id
        response.executed_task_id = conversation.executed_task_id
        return response

    state = conversation_state(conversation)
    response = agent.handle_message(request.message, state)

    if response is None:
        db.rollback()
        raise HTTPException(
            status_code=422, detail="I could not understand the request"
        )

    if state.status == ConversationStatus.CONFIRMED:
        task = create_task(
            db,
            title=state.draft_task.title,
            description=state.draft_task.description,
            priority=state.draft_task.priority or TaskPriority.MEDIUM,
            deadline=state.draft_task.deadline,
            commit=False,
        )
        state.status = ConversationStatus.EXECUTED
        conversation.executed_task_id = task.id
        response.status = state.status
        response.executed_task_id = task.id

    apply_conversation_state(conversation, state)
    db.commit()
    response.conversation_id = conversation.id

    return response


@app.get("/agent/conversations/{conversation_id}")
def get_agent_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    state = conversation_state(conversation)
    response = agent.response_for_state(state)
    response.conversation_id = conversation.id
    response.executed_task_id = conversation.executed_task_id
    return response

@app.post("/agent/approve")
def approve_agent_proposal(
    request: AgentApproval,
    db: Session = Depends(get_db),
):
    return agent_message(
        AgentMessage(
            conversation_id=request.conversation_id,
            message="confirm",
        ),
        db,
    )
