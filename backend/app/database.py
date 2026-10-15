"""Database connection.

- `engine` is the connection pool to Postgres.
- `SessionLocal()` opens one unit of work (a "session") — think of it as a short conversation with the DB.
- `get_db` hands a session to each API request and closes it afterwards.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Every table class in models.py inherits from this."""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
