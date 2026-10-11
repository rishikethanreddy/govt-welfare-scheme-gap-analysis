"""
Database engine, session factory, and Base declarative class.

Supports PostgreSQL (production) and SQLite (dev fallback).
Connection is driven by DATABASE_URL from config/environment.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.app.config import get_settings


settings = get_settings()

# SQLite needs check_same_thread=False for multi-threaded access.
# This arg is ignored by PostgreSQL drivers.
_connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    echo=settings.DEBUG and not settings.is_production,
    pool_pre_ping=True,  # Verify connections before use (helps with managed PG)
)

# Enable WAL mode for SQLite for better concurrent read performance
if settings.is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_db():
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
