import os

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

TEST_DATABASE_URL = os.environ.setdefault(
    "ORBIT_DATABASE_URL",
    "postgresql+psycopg://orbit:orbit@localhost:5432/orbit_test",
)

database_name = make_url(TEST_DATABASE_URL).database
if database_name is None or not database_name.endswith("_test"):
    raise RuntimeError(
        "Backend tests require ORBIT_DATABASE_URL to name a database ending "
        "in '_test'; refusing to use a development or production database."
    )

from app.database.connection import engine


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

