from datetime import datetime

from sqlalchemy.orm import Session

from app.api.schemas import TaskCreate
from app.domain.task import Task, TaskStatus, TaskPriority


def create_task(
    db: Session,
    title: str,
    description: str | None = None,
    priority: TaskPriority = TaskPriority.MEDIUM,
    deadline: datetime | None = None,
    *,
    commit: bool = True,
) -> Task:
    task = Task(
        title=title,
        description=description,
        priority=priority,
        deadline=deadline,
    )

    db.add(task)
    if commit:
        db.commit()
        db.refresh(task)
    else:
        db.flush()

    return task

def get_tasks(db: Session) -> list[Task]:
    return db.query(Task).all()

def complete_task(db: Session, task_id: int) -> Task | None:
    task = db.get(Task, task_id)

    if task is None:
        return None

    task.status = TaskStatus.COMPLETED

    db.commit()
    db.refresh(task)

    return task
