from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import AgentMessage, TaskCreate, AgentApproval
from app.database.connection import get_db
from app.agent.agent import Agent
from app.agent.local_llm import LocalLLM
from app.services.task_service import create_task, get_tasks, complete_task

app = FastAPI(title="Orbit AI")
agent = Agent(LocalLLM())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["POST"],
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
    response = agent.handle_message(request.message, db)

    if response is None:
        return {"error": "I could not understand the request"}

    return response

@app.post("/agent/approve")
def approve_agent_proposal(
    request: AgentApproval,
    db: Session = Depends(get_db),
):
    task = agent.execute_proposal(
        db,
        request.proposal,
        approved=True,
    )

    return task
