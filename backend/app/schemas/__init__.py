"""
Pydantic models for API request/response schemas
"""

# Standard library imports
from datetime import datetime
from typing import List, Optional

# Third-party imports
from pydantic import BaseModel


class JobResponse(BaseModel):
    id: int
    filename: str
    job_type: str
    status: str
    created_at: datetime
    is_sparse: Optional[bool] = None
    has_duplicates: Optional[bool] = None
    selected_ucs: Optional[List[str]] = None
    error_message: Optional[str] = None


class JobDetails(BaseModel):
    id: int
    filename: str
    file_path: str
    job_type: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_sparse: Optional[bool] = None
    has_duplicates: Optional[bool] = None


class UploadResponse(BaseModel):
    job_id: int
    message: str
    filename: str
    job_type: str


class JobStatistics(BaseModel):
    total_jobs: int
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int


class BatchProcessRequest(BaseModel):
    reference_file: str
    selected_files: List[str]
    selected_ucs: List[str]


class BatchJobStatus(BaseModel):
    filename: str
    status: str
    job_id: Optional[int] = None
    error: Optional[str] = None


class BatchStatusResponse(BaseModel):
    overall_status: str
    jobs: List[BatchJobStatus]
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    max_concurrent_jobs: Optional[int] = None
    active_jobs: Optional[int] = None


class JobStatus(BaseModel):
    """Legacy model for backward compatibility"""

    job_id: int
    status: str
    message: Optional[str] = None
