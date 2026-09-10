import pytest

from app.database.connection import SessionLocal
from app.domain.task import Task


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()

        # Remove tasks created by tests.
        session.query(Task).delete()
        session.commit()

        session.close()

