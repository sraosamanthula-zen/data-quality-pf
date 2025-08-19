"""
Jobs management routes for the Data Quality Platform
"""

from typing import List
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from database import get_db, JobRecord, FileProcessingMetrics, AgentActivityLog
from models import JobResponse, JobStatistics

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=List[JobResponse])
async def get_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all jobs with pagination"""
    jobs = db.query(JobRecord).order_by(JobRecord.created_at.desc()).offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}")
async def get_job_details(job_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific job"""
    job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Parse results JSON if available
    results = None
    if job.results_json:
        try:
            import json
            results = json.loads(job.results_json)
        except Exception:
            results = {"raw_results": job.results_json}
    
    return {
        "id": job.id,
        "filename": job.filename,
        "file_path": job.file_path,
        "job_type": job.job_type,
        "status": job.status,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "quality_score": job.quality_score,
        "is_sparse": job.is_sparse,
        "has_duplicates": job.has_duplicates,
        "results": results,
        "error_message": job.error_message,
        "selected_ucs": job.selected_ucs,
        "is_reference": job.is_reference,
        "reference_file_path": job.reference_file_path
    }


@router.post("/{job_id}/start")
async def start_job_processing(job_id: int, db: Session = Depends(get_db)):
    """Start processing an uploaded job"""
    job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in ["uploaded", "failed"]:
        raise HTTPException(status_code=400, detail=f"Job cannot be started. Current status: {job.status}")
    
    # Update status to processing
    job.status = "processing"
    job.started_at = datetime.now()
    db.commit()
    
    return {"message": "Job processing started", "job_id": job.id, "status": "processing"}


@router.delete("/{job_id}")
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job and its associated files"""
    job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete associated file
    try:
        import os
        if os.path.exists(job.file_path):
            os.remove(job.file_path)
    except Exception as e:
        print(f"Warning: Could not delete file {job.file_path}: {e}")
    
    # Delete job and related records
    db.query(FileProcessingMetrics).filter(FileProcessingMetrics.job_id == job_id).delete()
    db.query(AgentActivityLog).filter(AgentActivityLog.job_id == job_id).delete()
    db.delete(job)
    db.commit()
    
    return {"message": f"Job {job_id} deleted successfully"}


@router.get("/activity")
async def get_agent_activity(
    limit: int = 50,
    agent_name: str = None,
    job_id: int = None,
    db: Session = Depends(get_db)
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
                "job_id": activity.job_id
            }
            for activity in activities
        ],
        "total_count": len(activities),
        "filters": {
            "agent_name": agent_name,
            "job_id": job_id,
            "limit": limit
        }
    }


@router.get("/statistics", response_model=JobStatistics)
async def get_job_statistics(db: Session = Depends(get_db)):
    """Get overall job statistics and metrics"""
    
    total_jobs = db.query(JobRecord).count()
    pending_jobs = db.query(JobRecord).filter(JobRecord.status == "pending").count()
    
    # Count all processing-related statuses
    processing_statuses = [
        "processing", "processing_uc1", "processing_uc4", 
        "analyzing_completeness", "detecting_duplicates", "cleaning_file"
    ]
    processing_jobs = db.query(JobRecord).filter(JobRecord.status.in_(processing_statuses)).count()
    
    completed_jobs = db.query(JobRecord).filter(JobRecord.status == "completed").count()
    failed_jobs = db.query(JobRecord).filter(JobRecord.status == "failed").count()
    
    # Calculate average quality score
    avg_quality = db.query(func.avg(JobRecord.quality_score)).filter(
        JobRecord.quality_score.isnot(None)
    ).scalar()
    
    return JobStatistics(
        total_jobs=total_jobs,
        pending_jobs=pending_jobs,
        processing_jobs=processing_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        average_quality_score=float(avg_quality) if avg_quality else None
    )


@router.get("/logs")
async def list_available_logs():
    """List available log files"""
    log_dir = Path("logs")
    if not log_dir.exists():
        return {"logs": [], "message": "No logs directory found"}
    
    log_files = []
    for log_file in log_dir.glob("*.log"):
        stat = log_file.stat()
        log_files.append({
            "name": log_file.name,
            "type": log_file.stem,
            "size_bytes": stat.st_size,
            "modified": stat.st_mtime,
            "download_url": f"/jobs/logs/{log_file.stem}"
        })
    
    return {
        "logs": log_files,
        "log_directory": str(log_dir.absolute())
    }


@router.get("/logs/{log_type}")
async def download_logs(log_type: str):
    """Download application logs for debugging"""
    log_dir = Path("logs")
    
    if log_type == "platform":
        log_file = log_dir / "data_quality_platform.log"
    elif log_type == "agents":
        log_file = log_dir / "agent_activities.log"
    else:
        raise HTTPException(status_code=400, detail="Invalid log type. Use 'platform' or 'agents'")
    
    if not log_file.exists():
        raise HTTPException(status_code=404, detail=f"Log file not found: {log_file}")
    
    return FileResponse(
        path=str(log_file),
        filename=log_file.name,
        media_type="text/plain"
    )
