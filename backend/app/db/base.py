"""
Database configuration and session management
"""

from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import settings
from .models import Base

# Database setup
DATABASE_URL = settings.database_url

# SQLite connection parameters to prevent locking
sqlite_connect_args = (
    {
        "check_same_thread": False,
        "timeout": 30,
        "isolation_level": None,
    }
    if "sqlite" in DATABASE_URL
    else {}
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args=sqlite_connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize the database"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, Any, None]:
    """Context manager for database session"""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
