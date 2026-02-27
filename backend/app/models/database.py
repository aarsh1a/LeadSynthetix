"""Database session configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings
from app.models.base import Base
from app.models import LoanApplication, AgentMemo, AuditLog, IngestedDocument  # noqa: F401

settings = get_settings()
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
