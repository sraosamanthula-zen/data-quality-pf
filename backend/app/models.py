from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

SQLITE_DATABASE_URL = "sqlite:///./data_quality_platform.db"

engine = create_engine(
    SQLITE_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class JobStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, index=True)
    status = Column(String, default=JobStatus.PENDING.value)
    file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    
    # Agentic workflow flags
    enable_uc1 = Column(Boolean, default=True)  # Sparse data detection
    enable_uc4 = Column(Boolean, default=True)  # Duplicate detection
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results and errors
    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Data quality metrics
    total_rows = Column(Integer, nullable=True)
    valid_rows = Column(Integer, nullable=True)
    duplicate_rows = Column(Integer, nullable=True)
    sparse_data_score = Column(Integer, nullable=True)  # 0-100 quality score

class FileProcessing(Base):
    __tablename__ = "file_processing"
    
    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="uploaded")  # uploaded, processing, completed, failed
    
    # File metadata
    file_size = Column(Integer, nullable=True)
    rows_count = Column(Integer, nullable=True)
    columns_count = Column(Integer, nullable=True)
    
    # Processing results
    issues_detected = Column(JSON, nullable=True)
    corrections_applied = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

class AgentActivity(Base):
    __tablename__ = "agent_activity"
    
    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, index=True)
    agent_name = Column(String, nullable=False)  # uc1_sparse_data, uc4_duplicate, etc.
    
    # Agent execution details
    action_type = Column(String, nullable=False)  # detect, correct, validate
    description = Column(Text, nullable=False)
    
    # Results
    issues_found = Column(Integer, default=0)
    corrections_made = Column(Integer, default=0)
    confidence_score = Column(Integer, nullable=True)  # 0-100
    
    # Execution metadata
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DataQualityMetrics(Base):
    __tablename__ = "data_quality_metrics"
    
    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, index=True)
    
    # UC1: Sparse Data Metrics
    completeness_score = Column(Integer, nullable=True)  # 0-100
    missing_values_count = Column(Integer, default=0)
    empty_rows_count = Column(Integer, default=0)
    sparse_columns = Column(JSON, nullable=True)  # List of sparse column names
    
    # UC4: Duplicate Detection Metrics
    duplicate_records_count = Column(Integer, default=0)
    unique_records_count = Column(Integer, default=0)
    duplicate_groups = Column(JSON, nullable=True)  # Groups of duplicate records
    
    # Overall quality assessment
    overall_quality_score = Column(Integer, nullable=True)  # 0-100
    recommendations = Column(JSON, nullable=True)  # Suggested improvements
    
    created_at = Column(DateTime, default=datetime.utcnow)
