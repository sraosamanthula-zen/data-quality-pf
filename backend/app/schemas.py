from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class FileUploadResponse(BaseModel):
    job_id: str
    file_id: str
    filename: str
    status: str
    message: str

class JobResponse(BaseModel):
    id: str
    status: JobStatus
    original_filename: str
    enable_uc1: bool
    enable_uc4: bool
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Data quality metrics
    total_rows: Optional[int] = None
    valid_rows: Optional[int] = None
    duplicate_rows: Optional[int] = None
    sparse_data_score: Optional[int] = None

    class Config:
        from_attributes = True

class AgentResult(BaseModel):
    agent_name: str
    issues_found: int
    corrections_made: int
    confidence_score: int
    execution_time_ms: int
    details: Dict[str, Any]

class UC1SparseDataResult(BaseModel):
    """Results from UC1 Sparse Data Detection Agent"""
    completeness_score: int  # 0-100
    missing_values_count: int
    empty_rows_count: int
    sparse_columns: List[str]
    recommendations: List[str]
    is_sparse: bool

class UC4DuplicateResult(BaseModel):
    """Results from UC4 Duplicate Detection Agent"""
    duplicate_records_count: int
    unique_records_count: int
    duplicate_groups: List[List[int]]  # Row indices of duplicate groups
    deduplication_strategy: str
    recommendations: List[str]
    has_duplicates: bool

class DataQualityReport(BaseModel):
    """Overall data quality assessment"""
    overall_score: int  # 0-100
    uc1_results: Optional[UC1SparseDataResult] = None
    uc4_results: Optional[UC4DuplicateResult] = None
    summary: str
    recommendations: List[str]
