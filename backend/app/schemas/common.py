"""
Common Pydantic schemas for the Data Quality Platform
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class JobResult(BaseModel):
    """Common result structure for all job processing"""
    
    job_id: str = Field(description="Unique identifier for the job")
    use_case: str = Field(description="Use case that was executed (UC1, UC4)")
    input_file_path: str = Field(description="Path to the input file")
    output_file_path: str = Field(description="Path to the output/result file")
    
    # Processing metadata
    processing_time_seconds: float = Field(description="Time taken to process in seconds")
    start_time: datetime = Field(description="When processing started")
    end_time: datetime = Field(description="When processing completed")
    
    # Quality metrics (can be extended based on use case)
    total_rows_processed: Optional[int] = Field(None, description="Total number of rows processed")
    quality_score: Optional[float] = Field(None, description="Overall quality score (0-100)")
    
    # Use case specific results
    uc1_results: Optional[Dict[str, Any]] = Field(None, description="UC1 completeness analysis results")
    uc4_results: Optional[Dict[str, Any]] = Field(None, description="UC4 duplicate detection results")
    
    # Status and error handling
    success: bool = Field(description="Whether the processing was successful")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during processing")


class BatchProcessingRequest(BaseModel):
    """Request model for batch processing"""
    
    directory_path: str = Field(description="Path to directory containing files to process")
    selected_ucs: List[str] = Field(description="List of use cases to execute (UC1, UC4)")
    reference_file_paths: Dict[str, str] = Field(description="Map of UC to reference file path")


class BatchProcessingResponse(BaseModel):
    """Response model for batch processing"""
    
    batch_id: str = Field(description="Unique identifier for this batch")
    total_files: int = Field(description="Total number of files to be processed")
    jobs_created: List[int] = Field(description="List of job IDs created for this batch")
    message: str = Field(description="Status message")
