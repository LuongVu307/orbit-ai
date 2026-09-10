from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db

app = FastAPI(title="Orbit AI")


@app.get("/")
def root():
    return {"message": "Orbit AI is running"}


@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    return {"database": result.scalar()}