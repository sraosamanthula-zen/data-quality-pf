"""
Jobs management routes for the Data Quality Platform
"""

# Standard library imports
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

# Local application imports
from app.core.config import settings
from app.db import AgentActivityLog, FileProcessingMetrics, JobRecord, get_db
from app.schemas import JobResponse, JobStatistics

router = APIRouter(prefix="/jobs", tags=["jobs"])


def extract_base_dataset_name(filename_stem: str) -> str:
    """
    Extract the base dataset name from a processed filename by removing UC suffixes.
    This function is designed to be extensible for future UCs.
    
    Args:
        filename_stem: The filename without extension (e.g., "example_dataset_02_dedup")
        
    Returns:
        The base dataset name (e.g., "example_dataset_02")
    """
    # Get known suffixes from environment variables
    env_suffixes = [
        os.getenv("RESULT_SUFFIX", "_processed"),
        os.getenv("UC1_OUTPUT_SUFFIX", "_uc1_completeness"), 
        os.getenv("UC4_OUTPUT_SUFFIX", "_processed"),
    ]
    
    # Common UC suffix patterns (extensible for future UCs)
    common_patterns = [
        "_dedup",           # UC4: Duplicate detection
        "_completeness",    # UC1: Completeness check  
        "_cleaned",         # General cleaning
        "_validated",       # Validation
        "_enriched",        # Data enrichment
        "_normalized",      # Normalization
        "_standardized",    # Standardization
        "_anonymized",      # Anonymization
        "_transformed",     # General transformation
    ]
    
    # Combine all known suffixes, removing duplicates and empty values
    all_suffixes = list(set([s for s in env_suffixes + common_patterns if s]))
    
    # Sort by length (longest first) to handle nested suffixes correctly
    all_suffixes.sort(key=len, reverse=True)
    
    # Remove the first matching suffix
    base_name = filename_stem
    for suffix in all_suffixes:
        if base_name.endswith(suffix):
            base_name = base_name[:-len(suffix)]
            break
    
    # Additional pattern matching for numbered UC outputs (e.g., "_uc5_quality", "_uc10_format")
    # This regex handles future UC patterns like _ucN_description
    uc_pattern = re.compile(r'_uc\d+_\w+$', re.IGNORECASE)
    if uc_pattern.search(base_name):
        base_name = uc_pattern.sub('', base_name)
    
    # Fallback: if we couldn't extract a meaningful base name, return the original
    return base_name if base_name.strip() else filename_stem


@router.get("/outputs")
async def list_output_files(db: Session = Depends(get_db)):
    """List all output files from completed jobs"""

    outputs_directory = str(settings.outputs_dir)
    allowed_base_dir = os.path.abspath(str(settings.outputs_dir))
    abs_outputs_directory = os.path.abspath(outputs_directory)
    # Basic validation
    if not abs_outputs_directory.startswith(allowed_base_dir):
        return {"files": [], "directory": outputs_directory, "message": "Invalid output directory"}

    if not os.path.exists(abs_outputs_directory):
        return {"files": [], "directory": outputs_directory, "message": "Output directory not found"}

    all_files = []

    # Walk the outputs directory recursively and collect all files
    for root, dirs, files in os.walk(outputs_directory):
        for fname in files:
            try:
                file_path = os.path.join(root, fname)
                if not os.path.isfile(file_path):
                    continue

                stat = os.stat(file_path)
                rel_path = os.path.relpath(file_path, outputs_directory)
                path_parts = rel_path.split(os.sep)

                batch_name = "individual"
                if len(path_parts) >= 2 and path_parts[0].startswith("batch_"):
                    batch_name = path_parts[0]

                # Extract base dataset name using the extensible function
                filename_stem = Path(fname).stem
                base_dataset_name = extract_base_dataset_name(filename_stem)

                # Try to heuristically find a matching job by filename
                job_match = None
                try:
                    # Match on filename since result_file_path field was removed
                    job_match = (
                        db.query(JobRecord)
                        .filter(JobRecord.filename == fname)
                        .first()
                    )
                except Exception:
                    job_match = None

                all_files.append({
                    "filename": fname,
                    "path": file_path,
                    "size": stat.st_size,
                    "created": stat.st_mtime,
                    "status": "available",
                    "batch_name": batch_name,
                    "uc_type": "processed",
                    "relative_path": rel_path,
                    "job_id": job_match.id if job_match else None,
                    "original_filename": job_match.filename if job_match else None,
                    "base_dataset": base_dataset_name,
                })
            except Exception:
                # Skip files that cause stat or permission errors
                continue

    # Group files by base dataset name and keep only the latest file per group
    # This ensures only the final output of the UC pipeline is shown per dataset
    dataset_groups = {}
    for file_info in all_files:
        base_dataset = file_info["base_dataset"]
        if (base_dataset not in dataset_groups or 
            file_info["created"] > dataset_groups[base_dataset]["created"]):
            dataset_groups[base_dataset] = file_info

    # Convert back to list for the response
    output_files = list(dataset_groups.values())
    output_files.sort(key=lambda x: x["created"], reverse=True)

    return {
        "files": output_files,
        "directory": outputs_directory,
        "total_files": len(output_files),
    }


@router.get("/outputs/{filename}/download")
async def download_output_file(filename: str):
    """Download a specific output file (searches in batch directories)"""

    outputs_directory = str(settings.outputs_dir)

    # Search for the file in all subdirectories
    file_path = None
    for root, dirs, files in os.walk(outputs_directory):
        if filename in files:
            file_path = os.path.join(root, filename)
            break

    # Also check direct outputs directory
    if not file_path:
        direct_path = os.path.join(outputs_directory, filename)
        if os.path.exists(direct_path):
            file_path = direct_path

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, detail=f"Output file not found: {filename}"
        )

    return FileResponse(path=file_path, filename=filename, media_type="text/csv")


@router.get("/outputs/{filename}/preview")
async def preview_output_file(filename: str):
    """Preview the contents of an output file (searches in batch directories)"""
    import csv

    outputs_directory = str(settings.outputs_dir)

    # Search for the file in all subdirectories
    file_path = None
    for root, dirs, files in os.walk(outputs_directory):
        if filename in files:
            file_path = os.path.join(root, filename)
            break

    # Also check direct outputs directory
    if not file_path:
        direct_path = os.path.join(outputs_directory, filename)
        if os.path.exists(direct_path):
            file_path = direct_path

    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, detail=f"Output file not found: {filename}"
        )

    try:
        headers = []
        rows = []
        total_rows = 0

        with open(file_path, "r", encoding="utf-8") as csvfile:
            # Create CSV reader
            reader = csv.reader(csvfile)

            # Get headers
            headers = next(reader, [])

            # Read up to 100 rows for preview
            for i, row in enumerate(reader):
                if i < 100:
                    rows.append(row)
                total_rows = i + 1

        return {
            "headers": headers,
            "rows": rows,
            "totalRows": total_rows,
            "filename": filename,
            "file_path": file_path,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.get("/statistics", response_model=JobStatistics)
async def get_job_statistics(db: Session = Depends(get_db)):
    """Get overall job statistics and metrics"""

    total_jobs = db.query(JobRecord).count()

    # Include 'uploaded', 'pending', and 'queued' as pending jobs
    pending_statuses = ["uploaded", "pending", "queued"]
    pending_jobs = (
        db.query(JobRecord).filter(JobRecord.status.in_(pending_statuses)).count()
    )

    # Count all processing-related statuses
    processing_statuses = [
        "processing",
        "processing_uc1",
        "processing_uc4",
        "analyzing_completeness",
        "detecting_duplicates",
        "cleaning_file",
    ]
    processing_jobs = (
        db.query(JobRecord).filter(JobRecord.status.in_(processing_statuses)).count()
    )

    completed_jobs = db.query(JobRecord).filter(JobRecord.status == "completed").count()
    failed_jobs = db.query(JobRecord).filter(JobRecord.status == "failed").count()

    return JobStatistics(
        total_jobs=total_jobs,
        pending_jobs=pending_jobs,
        processing_jobs=processing_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
    )


@router.get("", response_model=List[JobResponse])
async def get_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all jobs with pagination, including duplicate information"""
    jobs = (
        db.query(JobRecord)
        .order_by(JobRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Convert to dict to include simplified job information
    job_list = []
    for job in jobs:
        # Convert selected_ucs from string to list
        selected_ucs_list = []
        if job.selected_ucs:
            selected_ucs_list = [uc.strip() for uc in job.selected_ucs.split(',')]
        
        job_dict = {
            "id": job.id,
            "filename": job.filename,
            "file_path": job.file_path,
            "job_type": job.job_type,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "is_sparse": job.is_sparse,
            "has_duplicates": job.has_duplicates,
            "selected_ucs": selected_ucs_list,
            "is_reference": job.is_reference,
            "error_message": job.error_message,
        }
        job_list.append(job_dict)

    return job_list


@router.get("/activity")
async def get_agent_activity(
    limit: int = 50,
    agent_name: Optional[str] = None,
    job_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Get recent agent activity logs for debugging and monitoring"""

    query = db.query(AgentActivityLog).order_by(AgentActivityLog.timestamp.desc())

    if agent_name:
        query = query.filter(AgentActivityLog.agent_name == agent_name)

    if job_id:
        query = query.filter(AgentActivityLog.job_id == job_id)

    activities = query.limit(limit).all()

    return {
        "activities": [
            {
                "id": activity.id,
                "timestamp": activity.timestamp.isoformat(),
                "agent_name": activity.agent_name,
                "activity_type": activity.activity_type,
                "activity_details": activity.activity_details,
                "job_id": activity.job_id,
            }
            for activity in activities
        ],
        "total_count": len(activities),
        "filters": {"agent_name": agent_name, "job_id": job_id, "limit": limit},
    }


@router.get("/logs")
async def list_available_logs():
    """List available log files"""
    log_dir = Path("logs")
    if not log_dir.exists():
        return {"logs": [], "message": "No logs directory found"}

    log_files = []
    for log_file in log_dir.glob("*.log"):
        stat = log_file.stat()
        log_files.append(
            {
                "name": log_file.name,
                "type": log_file.stem,
                "size_bytes": stat.st_size,
                "modified": stat.st_mtime,
                "download_url": f"/jobs/logs/{log_file.stem}",
            }
        )

    return {"logs": log_files, "log_directory": str(log_dir.absolute())}


@router.get("/logs/{log_type}")
async def download_logs(log_type: str):
    """Download application logs for debugging"""
    log_dir = Path("logs")

    if log_type == "platform":
        log_file = log_dir / "data_quality_platform.log"
    elif log_type == "agents":
        log_file = log_dir / "agent_activities.log"
    else:
        raise HTTPException(
            status_code=400, detail="Invalid log type. Use 'platform' or 'agents'"
        )

    if not log_file.exists():
        raise HTTPException(status_code=404, detail=f"Log file not found: {log_file}")

    return FileResponse(
        path=str(log_file), filename=log_file.name, media_type="text/plain"
    )


@router.get("/{job_id}")
async def get_job_details(job_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific job"""
    job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # No need to parse results JSON since we removed that functionality
    
    # Convert selected_ucs from string to list
    selected_ucs_list = []
    if job.selected_ucs:
        selected_ucs_list = [uc.strip() for uc in job.selected_ucs.split(',')]
    
    return {
        "id": job.id,
        "filename": job.filename,
        "file_path": job.file_path,
        "job_type": job.job_type,
        "status": job.status,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "is_sparse": job.is_sparse,
        "has_duplicates": job.has_duplicates,
        "selected_ucs": selected_ucs_list,
        "is_reference": job.is_reference,
        "reference_file_path": job.reference_file_path,
        "error_message": job.error_message,
    }


@router.post("/{job_id}/start")
async def start_job_processing(job_id: int, db: Session = Depends(get_db)):
    """Start processing an uploaded job"""
    job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in ["uploaded", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Job cannot be started. Current status: {job.status}",
        )

    # Update status to processing
    job.status = "processing"
    job.started_at = datetime.now()
    db.commit()

    return {
        "message": "Job processing started",
        "job_id": job.id,
        "status": "processing",
    }


@router.delete("/{job_id}")
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job and its associated files"""
    job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete associated file
    try:
        if os.path.exists(job.file_path):
            os.remove(job.file_path)
    except Exception as e:
        print(f"Warning: Could not delete file {job.file_path}: {e}")

    # Delete job and related records
    db.query(FileProcessingMetrics).filter(
        FileProcessingMetrics.job_id == job_id
    ).delete()
    db.query(AgentActivityLog).filter(AgentActivityLog.job_id == job_id).delete()
    db.delete(job)
    db.commit()

    return {"message": f"Job {job_id} deleted successfully"}


@router.get("/{job_id}/download")
async def download_job_result(job_id: int, db: Session = Depends(get_db)):
    """Download the result file for a specific job"""
    job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Look for result files in the outputs directory
    storage_directory = os.getenv("STORAGE_DIRECTORY", "./storage")
    outputs_directory = os.path.join(storage_directory, "outputs")

    # Also check the 'outputs' directory at the root level
    if not os.path.exists(outputs_directory):
        outputs_directory = "./outputs"

    # Build expected output filename
    result_suffix = os.getenv("RESULT_SUFFIX", "_processed")
    base_filename = Path(job.filename).stem
    output_filename = f"{base_filename}{result_suffix}.csv"
    output_path = os.path.join(outputs_directory, output_filename)

    if not os.path.exists(output_path):
        raise HTTPException(
            status_code=404, detail=f"Result file not found for job {job_id}"
        )

    return FileResponse(
        path=output_path, filename=output_filename, media_type="text/csv"
    )
