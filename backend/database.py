"""
Database configuration and models for the Data Quality Platform
"""

# Standard library imports
import os
from contextlib import contextmanager
from datetime import datetime

# Third-party imports
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

# Database setup with proper connection handling to avoid locking
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data_quality_platform.db")

# SQLite connection parameters to prevent locking
sqlite_connect_args = {
    "check_same_thread": False,
    "timeout": 30,  # 30 second timeout for busy database
    "isolation_level": None,  # Use autocommit mode to prevent locks
} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL, 
    connect_args=sqlite_connect_args,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
    echo=False  # Set to True for SQL query debugging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class JobRecord(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    job_type = Column(String, nullable=False)  # "UC1", "UC4", or comma-separated
    status = Column(String, default="pending")  # pending, processing, completed, failed
    selected_ucs = Column(String, nullable=True)  # Comma-separated list of selected UCs
    is_reference = Column(Boolean, default=False)  # Whether this is a reference file
    reference_file_id = Column(Integer, nullable=True)  # ID of reference file for comparison
    reference_file_path = Column(String, nullable=True)  # Path to reference file
    sparse_compared_to_reference = Column(Boolean, nullable=True)  # Sparse when compared to reference
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results
    quality_score = Column(Float, nullable=True)
    is_sparse = Column(Boolean, nullable=True)
    has_duplicates = Column(Boolean, nullable=True)
    duplicate_count = Column(Integer, nullable=True)  # Number of duplicate records found
    duplicate_percentage = Column(Float, nullable=True)  # Percentage of duplicates
    total_rows_original = Column(Integer, nullable=True)  # Original row count
    total_rows_processed = Column(Integer, nullable=True)  # Processed row count after deduplication
    results = Column(Text, nullable=True)  # JSON results
    results_json = Column(Text, nullable=True)  # JSON results (alternative field name)
    result_file_path = Column(String, nullable=True)  # Path to result file
    error_message = Column(Text, nullable=True)


class FileProcessingMetrics(Base):
    __tablename__ = "file_processing_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    total_rows = Column(Integer, nullable=True)
    total_columns = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    agent_execution_time_ms = Column(Integer, nullable=True)
    issues_found = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())


class AgentActivityLog(Base):
    __tablename__ = "agent_activity"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=True)
    agent_name = Column(String, nullable=False)
    activity_type = Column(String, nullable=False)
    activity_details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=func.now())


class ReferenceFile(Base):
    __tablename__ = "reference_files"
    
    id = Column(Integer, primary_key=True, index=True)
    uc_type = Column(String(10), nullable=False)  # "UC1", "UC4"
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)


# Database dependency with proper error handling
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


# Context manager for database operations
@contextmanager
def get_db_session():
    """Context manager for database sessions with proper cleanup"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


# Initialize database
def init_db():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created/verified")
