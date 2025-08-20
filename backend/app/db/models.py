"""
SQLAlchemy database models for the Data Quality Platform
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, Boolean, Float, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all database models"""

    pass


class JobRecord(Base):
    """Job processing record model"""

    __tablename__ = "jobs"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # File information
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)

    # Job configuration and folder structure
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    selected_ucs: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # e.g., "uc1,uc4"
    use_case: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Current processing use case
    
    # Directory paths for this job
    inputs_folder: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # inputs/job_<id>
    outputs_folder: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # outputs/job_<id>
    temp_folder: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # temp/job_<id>

    # Reference file information
    is_reference: Mapped[bool] = mapped_column(Boolean, default=False)
    reference_file_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sparse_compared_to_reference: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True
    )

    # Job status and timing
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Results and metrics
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_sparse: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_duplicates: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    duplicate_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duplicate_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_rows_original: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_rows_processed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Result data
    results: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    results_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class FileProcessingMetrics(Base):
    """File processing metrics model"""

    __tablename__ = "file_processing_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # File metrics
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_rows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_columns: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Processing metrics
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    agent_execution_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    issues_found: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class AgentActivityLog(Base):
    """Agent activity logging model"""

    __tablename__ = "agent_activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    activity_type: Mapped[str] = mapped_column(String, nullable=False)
    activity_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class ReferenceFile(Base):
    """Reference file model"""

    __tablename__ = "reference_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uc_type: Mapped[str] = mapped_column(String(10), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
