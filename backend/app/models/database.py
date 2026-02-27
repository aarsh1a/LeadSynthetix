"""Database session configuration."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings
from app.models.base import Base

settings = get_settings()

# --- SQLite compatibility shims for PostgreSQL column types ---
# These let the same models work against both Postgres and SQLite.
if settings.database_url.startswith("sqlite"):
    from sqlalchemy.ext.compiler import compiles
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

    @compiles(PG_UUID, "sqlite")
    def _compile_pg_uuid_sqlite(type_, compiler, **kw):
        return "CHAR(36)"

    @compiles(JSONB, "sqlite")
    def _compile_jsonb_sqlite(type_, compiler, **kw):
        return "JSON"


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    # SQLite needs check_same_thread=False for FastAPI's threaded access
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

# Enable SQLite foreign-key enforcement
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import all models so Base.metadata knows about them, then create tables
from app.models import LoanApplication, AgentMemo, AuditLog, IngestedDocument  # noqa: F401

Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
