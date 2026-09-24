import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DEFAULT_DATABASE_URL = "postgresql+psycopg://orbit:orbit@localhost:5432/orbit"
DATABASE_URL = os.environ.get("ORBIT_DATABASE_URL", DEFAULT_DATABASE_URL)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def get_db():
    db: Session = SessionLocal()

    try:
        yield db
    finally:
        db.close()
