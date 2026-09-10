from sqlalchemy.orm import Session

from app.api.schemas import TaskCreate
from app.domain.task import Task


def create_task(db: Session, task_data: TaskCreate) -> Task:
    task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        deadline=task_data.deadline,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


def get_tasks(db: Session) -> list[Task]:
    return db.query(Task).all()