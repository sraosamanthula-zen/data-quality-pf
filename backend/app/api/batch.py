"""
Batch processing routes for the Data Quality Platform
"""

# Standard library imports
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Local application imports
from app.core.config import settings
from app.db import get_db, JobRecord
from app.schemas.common import BatchProcessingResponse
from app.services.job_manager import JobProcessor

router = APIRouter(prefix="/batch", tags=["batch"])


class DirectoryProcessingRequest(BaseModel):
    directory_path: str
    selected_ucs: List[str]
    reference_file_paths: Optional[Dict[str, str]] = None


@router.post("/process-directory", response_model=BatchProcessingResponse)
async def process_directory(
    request: DirectoryProcessingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Process all CSV files in a directory using job_manager service
    
    Frontend usage: FileUpload.tsx calls this endpoint for batch directory processing
    """
    directory_path = Path(request.directory_path)
    
    if not directory_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Directory not found: {directory_path}"
        )
    
    if not directory_path.is_dir():
        raise HTTPException(
            status_code=400, detail=f"Path is not a directory: {directory_path}"
        )

    # Find all CSV files in the directory
    csv_files = list(directory_path.glob("*.csv"))
    
    if not csv_files:
        raise HTTPException(
            status_code=404, detail="No CSV files found in the specified directory"
        )

    # Validate selected UCs
    valid_ucs = ["UC1", "UC4"]
    invalid_ucs = [uc for uc in request.selected_ucs if uc not in valid_ucs]
    if invalid_ucs:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid UCs: {invalid_ucs}. Valid options: {valid_ucs}",
        )

    # Create job records for each CSV file
    job_ids = []
    for csv_file in csv_files:
        # Copy file to uploads directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{csv_file.name}"
        uploaded_file_path = settings.uploads_dir / safe_filename
        
        # Copy the file
        import shutil
        shutil.copy2(csv_file, uploaded_file_path)
        
        # Create job record
        job = JobRecord(
            filename=csv_file.name,
            file_path=str(uploaded_file_path),
            job_type=",".join(request.selected_ucs),
            selected_ucs=",".join(request.selected_ucs),
            status="uploaded",
            is_reference=False,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_ids.append(job.id)

    # Process jobs in background using job_manager
    async def execute_batch_jobs():
        """Background task to process all jobs using JobProcessor"""
        from app.db import SessionLocal
        job_db = SessionLocal()
        
        try:
            processor = JobProcessor(job_db)
            
            for job_id in job_ids:
                try:
                    # Execute job workflow using job_manager
                    result = await processor.execute_job_workflow(
                        job_id, request.selected_ucs
                    )
                    print(f"Job {job_id} completed successfully: {result}")
                    
                except Exception as e:
                    print(f"Job {job_id} failed: {str(e)}")
                    
                    # Update job status to failed
                    job_record = job_db.query(JobRecord).filter(JobRecord.id == job_id).first()
                    if job_record:
                        job_record.status = "failed"
                        job_record.error_message = str(e)
                        job_record.completed_at = datetime.utcnow()
                        job_db.commit()
                        
        except Exception as e:
            print(f"Batch processing failed: {str(e)}")
        finally:
            job_db.close()

    # Add background task
    background_tasks.add_task(execute_batch_jobs)

    # Prepare file information for response
    files = []
    for i, csv_file in enumerate(csv_files):
        files.append({
            "filename": csv_file.name,
            "job_id": job_ids[i],
            "status": "queued",
            "size": csv_file.stat().st_size,
        })

    return BatchProcessingResponse(
        message=f"Batch processing started for {len(csv_files)} files",
        batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        total_files=len(csv_files),
        job_ids=job_ids,
        files=files,
        selected_ucs=request.selected_ucs,
    )


@router.post("/batch-process")
async def batch_process(
    background_tasks: BackgroundTasks,
    selected_ucs: str = "UC1,UC4",
    db: Session = Depends(get_db),
):
    """
    Process files from the default inputs directory
    
    Frontend usage: BatchProcessor.tsx and FileUpload_new.tsx call this endpoint
    """
    # Parse selected UCs
    uc_list = [uc.strip() for uc in selected_ucs.split(",")]
    
    # Validate UCs
    valid_ucs = ["UC1", "UC4"]
    invalid_ucs = [uc for uc in uc_list if uc not in valid_ucs]
    if invalid_ucs:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid UCs: {invalid_ucs}. Valid options: {valid_ucs}",
        )

    # Find CSV files in the inputs directory
    inputs_dir = settings.inputs_dir
    csv_files = list(inputs_dir.glob("*.csv"))
    
    if not csv_files:
        raise HTTPException(
            status_code=404, 
            detail=f"No CSV files found in inputs directory: {inputs_dir}"
        )

    # Create job records for each CSV file
    job_ids = []
    for csv_file in csv_files:
        # For files already in inputs directory, no need to copy
        job = JobRecord(
            filename=csv_file.name,
            file_path=str(csv_file),
            job_type=",".join(uc_list),
            selected_ucs=",".join(uc_list),
            status="uploaded",
            is_reference=False,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_ids.append(job.id)

    # Process jobs in background using job_manager
    async def execute_batch_jobs():
        """Background task to process all jobs using JobProcessor"""
        from app.db import SessionLocal
        job_db = SessionLocal()
        
        try:
            processor = JobProcessor(job_db)
            
            for job_id in job_ids:
                try:
                    # Execute job workflow using job_manager
                    result = await processor.execute_job_workflow(job_id, uc_list)
                    print(f"Job {job_id} completed successfully: {result}")
                    
                except Exception as e:
                    print(f"Job {job_id} failed: {str(e)}")
                    
                    # Update job status to failed
                    job_record = job_db.query(JobRecord).filter(JobRecord.id == job_id).first()
                    if job_record:
                        job_record.status = "failed"
                        job_record.error_message = str(e)
                        job_record.completed_at = datetime.utcnow()
                        job_db.commit()
                        
        except Exception as e:
            print(f"Batch processing failed: {str(e)}")
        finally:
            job_db.close()

    # Add background task
    background_tasks.add_task(execute_batch_jobs)

    # Prepare file information for response
    files = []
    for i, csv_file in enumerate(csv_files):
        files.append({
            "filename": csv_file.name,
            "job_id": job_ids[i],
            "status": "queued",
            "size": csv_file.stat().st_size,
        })

    return {
        "message": f"Batch processing started for {len(csv_files)} files",
        "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "total_files": len(csv_files),
        "job_ids": job_ids,
        "files": files,
        "selected_ucs": uc_list,
        "processing_status": "started",
    }


@router.get("/status")
async def get_batch_status(batch_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Get status of batch processing jobs"""
    
    # Get recent jobs if no specific batch_id provided
    jobs_query = db.query(JobRecord).order_by(JobRecord.created_at.desc())
    
    if batch_id:
        # Filter by batch timeframe if batch_id format is batch_YYYYMMDD_HHMMSS
        if batch_id.startswith("batch_") and len(batch_id) == 21:
            timestamp_str = batch_id[6:]  # Remove "batch_" prefix
            try:
                batch_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                # Get jobs created within 1 hour of batch time
                jobs_query = jobs_query.filter(
                    JobRecord.created_at >= batch_time,
                    JobRecord.created_at <= batch_time.replace(hour=batch_time.hour + 1)
                )
            except ValueError:
                pass  # Invalid timestamp format, ignore filter
    
    jobs = jobs_query.limit(50).all()
    
    # Categorize jobs by status
    status_counts = {
        "pending": 0,
        "processing": 0, 
        "completed": 0,
        "failed": 0,
    }
    
    job_details = []
    for job in jobs:
        # Map job statuses to categories
        if job.status in ["uploaded", "queued"]:
            category = "pending"
        elif job.status in ["processing", "processing_uc1", "processing_uc4"]:
            category = "processing"
        elif job.status == "completed":
            category = "completed"
        elif job.status == "failed":
            category = "failed"
        else:
            category = "pending"
            
        status_counts[category] += 1
        
        # Get result info if available
        result_info = None
        if job.results_json:
            try:
                results = json.loads(job.results_json)
                result_info = {
                    "output_file_path": results.get("output_file_path"),
                    "use_cases_processed": results.get("use_cases_processed", []),
                    "completion_time": results.get("completion_time"),
                }
            except (json.JSONDecodeError, KeyError):
                pass
        
        job_details.append({
            "job_id": job.id,
            "filename": job.filename,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "selected_ucs": job.selected_ucs,
            "error_message": job.error_message,
            "results": result_info,
        })
    
    return {
        "batch_id": batch_id,
        "total_jobs": len(jobs),
        "status_summary": status_counts,
        "jobs": job_details,
        "last_updated": datetime.utcnow().isoformat(),
    }
