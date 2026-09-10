from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import AgentMessage, TaskCreate, AgentApproval
from app.database.connection import get_db
from app.agent.agent import execute_proposal, propose
from app.services.task_service import create_task, get_tasks, complete_task

app = FastAPI(title="Orbit AI")


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
def agent_message(request: AgentMessage):
    proposal = propose(request.message)

    if proposal is None:
        return {"error": "I could not understand the request"}

    return proposal

@app.post("/agent/approve")
def approve_agent_proposal(
    request: AgentApproval,
    db: Session = Depends(get_db),
):
    task = execute_proposal(
        db,
        request.proposal,
        approved=True,
    )

    return task