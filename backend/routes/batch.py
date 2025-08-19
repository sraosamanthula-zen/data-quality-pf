"""
Batch processing routes for the Data Quality Platform
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db, JobRecord, FileProcessingMetrics
from models import BatchStatusResponse
from agents.base_config import log_agent_activity

router = APIRouter(prefix="/batch", tags=["batch"])

# Global semaphore to limit concurrent processing jobs to 5
MAX_CONCURRENT_JOBS = 5
job_semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)


class ProcessDirectoryRequest(BaseModel):
    directory_path: str = None  # Optional - will use default from env if not provided
    selected_ucs: List[str]
    reference_file_paths: dict = {}  # UC type -> reference file path mapping


class BatchJobStatus(BaseModel):
    filename: str
    status: str
    job_id: Optional[int] = None
    error: Optional[str] = None


def run_async_background_task(coro):
    """
    Run an async coroutine in the background using asyncio
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def process_file_with_reference_async(
    file_path: str, 
    reference_files_by_uc: dict,  # UC type -> reference file path mapping
    selected_ucs: List[str], 
    job_id: int  # Pass job ID instead of database session
):
    """
    Async version of process_file_with_reference for proper background processing
    Note: Concurrency control is now handled at the caller level
    """
    from agents.base_config import log_agent_activity, log_processing_step, log_performance_metrics, log_agent_error
    from database import SessionLocal  # Import SessionLocal for creating new session
    
    filename = Path(file_path).name
    start_time = datetime.now()
    
    # Create a new database session for this background task
    db = SessionLocal()
    job = None
    
    try:
        # Get the job record
        job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
        if not job:
            log_agent_error("BatchProcessor", "job_not_found", Exception(f"Job {job_id} not found"), {
                "job_id": job_id,
                "filename": filename
            })
            return
        
        # Update job status to processing
        job.status = "processing"
        db.commit()
        
        log_processing_step(job_id, "BatchProcessor", "Starting async file processing with concurrency control", {
            "filename": filename,
            "reference_files": reference_files_by_uc,
            "selected_ucs": selected_ucs,
            "concurrent_slot_acquired": True
        })
        
        # Import processing functions inside the function to avoid circular imports
        from agents.uc1_agent import run_uc1_analysis
        from agents.uc4_agent import run_uc4_analysis
        
        # Create file metrics
        file_size = Path(file_path).stat().st_size
        metrics = FileProcessingMetrics(
            job_id=job_id,
            file_size_bytes=file_size
        )
        db.add(metrics)
        db.commit()
        
        log_processing_step(job_id, "BatchProcessor", "File metrics recorded", {
            "file_size_bytes": file_size
        })
        
        all_results = {}
        
        # Run selected UCs with proper async handling
        for uc in selected_ucs:
            uc_start_time = datetime.now()
            log_processing_step(job_id, f"BatchProcessor_{uc}", f"Starting async {uc} analysis")
            
            # Get the reference file for this UC
            reference_file_path = reference_files_by_uc.get(uc)
            if not reference_file_path:
                error_msg = f"No reference file provided for {uc}"
                log_agent_error(f"BatchProcessor_{uc}", f"{uc}_analysis", Exception(error_msg), {
                    "job_id": job_id,
                    "filename": filename
                })
                all_results[uc] = {"error": error_msg}
                continue
            
            try:
                if uc == "UC1":
                    log_agent_activity("UC1", f"Starting async analysis for {filename}", {"job_id": job_id})
                    uc1_result = await run_uc1_analysis(file_path, reference_file_path)
                    
                    # Convert Pydantic model to dict for JSON serialization
                    if hasattr(uc1_result, 'dict'):
                        all_results["UC1"] = uc1_result.dict()
                    else:
                        all_results["UC1"] = uc1_result
                    
                    log_agent_activity("UC1", f"Async analysis completed for {filename}", {
                        "job_id": job_id,
                        "success": uc1_result.success if hasattr(uc1_result, 'success') else True,
                        "duration_ms": (datetime.now() - uc_start_time).total_seconds() * 1000,
                        "output_file": uc1_result.output_file_path if hasattr(uc1_result, 'output_file_path') else None
                    })
                    
                elif uc == "UC4":
                    log_agent_activity("UC4", f"Starting async analysis for {filename}", {"job_id": job_id})
                    uc4_result = await run_uc4_analysis(file_path, reference_file_path)
                    all_results["UC4"] = uc4_result
                    log_agent_activity("UC4", f"Async analysis completed for {filename}", {
                        "job_id": job_id,
                        "success": True,
                        "duration_ms": (datetime.now() - uc_start_time).total_seconds() * 1000
                    })
                
                uc_duration = (datetime.now() - uc_start_time).total_seconds() * 1000
                log_performance_metrics(f"BatchProcessor_{uc}", f"{uc}_analysis", uc_duration, {
                    "job_id": job_id,
                    "filename": filename
                })
                
            except Exception as uc_error:
                log_agent_error(f"BatchProcessor_{uc}", f"{uc}_analysis", uc_error, {
                    "job_id": job_id,
                    "filename": filename
                })
                all_results[uc] = {"error": str(uc_error)}
        
        # Save results
        results_dir = Path(os.getenv("STORAGE_DIRECTORY", "./storage"))
        results_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"{Path(filename).stem}_results_{timestamp}.json"
        result_path = results_dir / result_filename
        
        import json
        
        # Custom JSON encoder to handle datetime objects and Pydantic models
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if hasattr(obj, 'dict'):  # Pydantic model
                return obj.dict()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(result_path, 'w') as f:
            json.dump(all_results, f, indent=2, default=json_serializer)
        
        log_processing_step(job_id, "BatchProcessor", "Async results saved", {
            "result_file": str(result_path)
        })
        
        # Update job with results
        job.result_file_path = str(result_path)
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        
        # Update metrics safely 
        current_time = datetime.utcnow()
        if job.created_at:
            total_duration = (current_time - job.created_at).total_seconds()
        else:
            total_duration = (datetime.now() - start_time).total_seconds()
            
        metrics.processing_time_seconds = total_duration
        metrics.issues_found = sum([
            result.get('issues_count', 0) 
            for result in all_results.values() 
            if isinstance(result, dict)
        ])
        
        # Commit all changes
        try:
            db.commit()
            log_processing_step(job_id, "BatchProcessor", "Async job completed successfully", {
                "total_duration_seconds": total_duration,
                "status": "completed"
            })
        except Exception as e:
            log_agent_error("BatchProcessor", "save_results_error", e, {"job_id": job_id})
            db.rollback()
            job.status = "failed"
            job.error_message = f"Failed to save results: {str(e)}"
            db.commit()
            raise
        
        log_performance_metrics("BatchProcessor", "complete_async_file_processing", 
                               (datetime.now() - start_time).total_seconds() * 1000, {
                                   "job_id": job_id,
                                   "filename": filename,
                                   "ucs_processed": len(selected_ucs)
                               })
        
        return {"status": "completed", "job_id": job_id}
        
    except Exception as e:
        # Update job status to failed
        if job:
            job.status = "failed"
            job.error_message = str(e)
            try:
                db.commit()
            except Exception:
                db.rollback()
            
            log_agent_error("BatchProcessor", "async_file_processing", e, {
                "job_id": job_id,
                "filename": filename
            })
        else:
            log_agent_error("BatchProcessor", "async_file_processing", e, {
                "filename": filename,
                "stage": "job_creation"
            })
        
        raise e
    
    finally:
        # Always close the database session
        db.close()


async def process_file_with_reference(
    file_path: str, 
    reference_files_by_uc: dict,  # UC type -> reference file path mapping
    selected_ucs: List[str], 
    job_id: int  # Pass job ID instead of database session
):
    """
    Process a single file against reference files with selected UCs
    Background task function with its own database session
    """
    from agents.base_config import log_agent_activity, log_processing_step, log_performance_metrics, log_agent_error
    from database import SessionLocal  # Import SessionLocal for creating new session
    
    filename = Path(file_path).name
    start_time = datetime.now()
    
    # Create a new database session for this background task
    db = SessionLocal()
    job = None
    
    try:
        # Get the job record
        job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
        if not job:
            log_agent_error("BatchProcessor", "job_not_found", Exception(f"Job {job_id} not found"), {
                "job_id": job_id,
                "filename": filename
            })
            return
        
        # Update job status to processing
        job.status = "processing"
        db.commit()
        
        log_processing_step(job_id, "BatchProcessor", "Starting file processing", {
            "filename": filename,
            "reference_files": reference_files_by_uc,
            "selected_ucs": selected_ucs
        })
        
        # Import processing functions inside the function to avoid circular imports
        from agents.uc1_agent import run_uc1_analysis
        from agents.uc4_agent import run_uc4_analysis
        
        # Create file metrics
        file_size = Path(file_path).stat().st_size
        metrics = FileProcessingMetrics(
            job_id=job_id,
            file_size_bytes=file_size
        )
        db.add(metrics)
        db.commit()
        
        log_processing_step(job_id, "BatchProcessor", "File metrics recorded", {
            "file_size_bytes": file_size
        })
        
        all_results = {}
        
        # Run selected UCs
        for uc in selected_ucs:
            uc_start_time = datetime.now()
            log_processing_step(job_id, f"BatchProcessor_{uc}", f"Starting {uc} analysis")
            
            # Get the reference file for this UC
            reference_file_path = reference_files_by_uc.get(uc)
            if not reference_file_path:
                error_msg = f"No reference file provided for {uc}"
                log_agent_error(f"BatchProcessor_{uc}", f"{uc}_analysis", Exception(error_msg), {
                    "job_id": job_id,
                    "filename": filename
                })
                all_results[uc] = {"error": error_msg}
                continue
            
            try:
                if uc == "UC1":
                    log_agent_activity("UC1", f"Starting analysis for {filename}", {"job_id": job_id})
                    uc1_result = await run_uc1_analysis(file_path, reference_file_path)
                    all_results["UC1"] = uc1_result
                    log_agent_activity("UC1", f"Analysis completed for {filename}", {
                        "job_id": job_id,
                        "success": True,
                        "duration_ms": (datetime.now() - uc_start_time).total_seconds() * 1000
                    })
                    
                elif uc == "UC4":
                    log_agent_activity("UC4", f"Starting analysis for {filename}", {"job_id": job_id})
                    uc4_result = await run_uc4_analysis(file_path, reference_file_path)
                    all_results["UC4"] = uc4_result
                    log_agent_activity("UC4", f"Analysis completed for {filename}", {
                        "job_id": job_id,
                        "success": True,
                        "duration_ms": (datetime.now() - uc_start_time).total_seconds() * 1000
                    })
                
                uc_duration = (datetime.now() - uc_start_time).total_seconds() * 1000
                log_performance_metrics(f"BatchProcessor_{uc}", f"{uc}_analysis", uc_duration, {
                    "job_id": job_id,
                    "filename": filename
                })
                
            except Exception as uc_error:
                log_agent_error(f"BatchProcessor_{uc}", f"{uc}_analysis", uc_error, {
                    "job_id": job_id,
                    "filename": filename
                })
                all_results[uc] = {"error": str(uc_error)}
        
        # Save results
        results_dir = Path(os.getenv("STORAGE_DIRECTORY", "./storage"))
        results_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"{Path(filename).stem}_results_{timestamp}.json"
        result_path = results_dir / result_filename
        
        import json
        with open(result_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        log_processing_step(job_id, "BatchProcessor", "Results saved", {
            "result_file": str(result_path)
        })
        
        # Update job with results
        job.result_file_path = str(result_path)
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        
        # Update metrics safely 
        current_time = datetime.utcnow()
        if job.created_at:
            total_duration = (current_time - job.created_at).total_seconds()
        else:
            total_duration = (datetime.now() - start_time).total_seconds()
            
        metrics.processing_time_seconds = total_duration
        metrics.issues_found = sum([
            result.get('issues_count', 0) 
            for result in all_results.values() 
            if isinstance(result, dict)
        ])
        
        # Commit all changes
        try:
            db.commit()
            log_processing_step(job_id, "BatchProcessor", "Job completed successfully", {
                "total_duration_seconds": total_duration,
                "status": "completed"
            })
        except Exception as e:
            log_agent_error("BatchProcessor", "save_results_error", e, {"job_id": job_id})
            db.rollback()
            job.status = "failed"
            job.error_message = f"Failed to save results: {str(e)}"
            db.commit()
            raise
        
        log_performance_metrics("BatchProcessor", "complete_file_processing", 
                               (datetime.now() - start_time).total_seconds() * 1000, {
                                   "job_id": job_id,
                                   "filename": filename,
                                   "ucs_processed": len(selected_ucs)
                               })
        
        return {"status": "completed", "job_id": job_id}
        
    except Exception as e:
        # Update job status to failed
        if job:
            job.status = "failed"
            job.error_message = str(e)
            try:
                db.commit()
            except Exception:
                db.rollback()
            
            log_agent_error("BatchProcessor", "file_processing", e, {
                "job_id": job_id,
                "filename": filename
            })
        else:
            log_agent_error("BatchProcessor", "file_processing", e, {
                "filename": filename,
                "stage": "job_creation"
            })
        
        raise e
    
    finally:
        # Always close the database session
        db.close()


@router.post("/process-directory")
async def process_directory(
    request: ProcessDirectoryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process all CSV files from directory against reference files for selected UCs in parallel
    """
    # DEBUG: Log incoming request
    print("🔥 DEBUG: Received batch processing request:")
    print(f"   Directory: {request.directory_path}")
    print(f"   Selected UCs: {request.selected_ucs}")
    print(f"   Reference paths: {request.reference_file_paths}")
    
    # Use provided directory or default from environment
    data_directory = request.directory_path if request.directory_path else os.getenv("DATA_DIRECTORY", "/home/sraosamanthula/ZENLABS/RCL_Files")
    
    if not os.path.exists(data_directory):
        raise HTTPException(status_code=404, detail=f"Data directory not found: {data_directory}")
    
    # Validate UCs
    valid_ucs = ["UC1", "UC4"]
    invalid_ucs = [uc for uc in request.selected_ucs if uc not in valid_ucs]
    if invalid_ucs:
        raise HTTPException(status_code=400, detail=f"Invalid UCs: {invalid_ucs}")
    
    if not request.selected_ucs:
        raise HTTPException(status_code=400, detail="At least one UC must be selected")
    
    # Validate reference files for selected UCs
    from database import ReferenceFile
    reference_files_by_uc = {}
    
    for uc in request.selected_ucs:
        # Get the active reference file for this UC
        ref_file = db.query(ReferenceFile).filter(
            ReferenceFile.uc_type == uc,
            ReferenceFile.is_active
        ).first()
        
        if not ref_file:
            raise HTTPException(status_code=400, detail=f"No active reference file found for {uc}")
        
        if not os.path.exists(ref_file.file_path):
            raise HTTPException(status_code=404, detail=f"Reference file not found for {uc}: {ref_file.file_path}")
        
        reference_files_by_uc[uc] = ref_file.file_path
    
    # Get all CSV files in the directory (excluding already processed ones)
    result_suffix = os.getenv("RESULT_SUFFIX", "_processed")
    csv_files = []
    
    for file in os.listdir(data_directory):
        if file.endswith('.csv') and not file.endswith(f'{result_suffix}.csv'):
            file_path = os.path.join(data_directory, file)
            if os.path.isfile(file_path):
                csv_files.append(file)
    
    if not csv_files:
        raise HTTPException(status_code=404, detail=f"No unprocessed CSV files found in directory: {data_directory}")
    
    # Create jobs for all files first
    job_ids = []
    job_data_list = []
    
    for filename in csv_files:
        file_path = os.path.join(data_directory, filename)
        
        # Create placeholder job for immediate response
        job = JobRecord(
            filename=filename,
            file_path=file_path,
            job_type=",".join(request.selected_ucs),
            selected_ucs=",".join(request.selected_ucs),
            is_reference=False,
            reference_file_path=str(reference_files_by_uc),  # Store reference file mapping
            status="queued"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_ids.append(job.id)
        
        # Store job data for processing
        job_data_list.append({
            "file_path": file_path,
            "reference_files": reference_files_by_uc,
            "selected_ucs": request.selected_ucs,
            "job_id": job.id
        })
    
    # Start parallel processing in background with proper concurrency control
    async def run_parallel_processing_with_queue():
        """Run processing tasks with proper concurrency control using a queue"""
        try:
            log_agent_activity("BatchProcessor", "Starting parallel processing with queue", {
                "total_jobs": len(job_data_list),
                "max_concurrent": MAX_CONCURRENT_JOBS,
                "directory": data_directory,
                "selected_ucs": request.selected_ucs
            })
            
            # Create a semaphore for this batch specifically
            batch_semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)
            
            async def process_with_semaphore(job_data):
                """Process a single job with semaphore control"""
                async with batch_semaphore:
                    return await process_file_with_reference_async(
                        job_data["file_path"],
                        job_data["reference_files"],
                        job_data["selected_ucs"],
                        job_data["job_id"]
                    )
            
            # Create tasks for all jobs
            tasks = [process_with_semaphore(job_data) for job_data in job_data_list]
            
            # Run all tasks with semaphore controlling concurrency
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            successful_jobs = sum(1 for r in results if not isinstance(r, Exception))
            failed_jobs = len(results) - successful_jobs
            
            log_agent_activity("BatchProcessor", "Parallel processing completed", {
                "total_jobs": len(results),
                "successful_jobs": successful_jobs,
                "failed_jobs": failed_jobs,
                "max_concurrent": MAX_CONCURRENT_JOBS
            })
            
            return results
            
        except Exception as e:
            log_agent_activity("BatchProcessor", "Parallel processing failed", {
                "error": str(e),
                "total_jobs": len(job_data_list)
            })
            raise
    
    # Add the parallel processing task to background tasks
    background_tasks.add_task(run_async_background_task, run_parallel_processing_with_queue())
    
    log_agent_activity("BatchProcessor", "Directory processing started with parallel execution", {
        "directory": data_directory,
        "files_count": len(csv_files),
        "selected_ucs": request.selected_ucs,
        "reference_files": reference_files_by_uc,
        "job_ids": job_ids,
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS
    })
    
    return {
        "message": f"Started parallel processing {len(csv_files)} files from directory with UCs: {', '.join(request.selected_ucs)} (max {MAX_CONCURRENT_JOBS} concurrent jobs)",
        "job_ids": job_ids,
        "directory": data_directory,
        "total_files": len(csv_files),
        "selected_ucs": request.selected_ucs,
        "reference_files": {uc: os.path.basename(path) for uc, path in reference_files_by_uc.items()},
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS
    }


@router.post("/test-async")
async def test_async_processing(background_tasks: BackgroundTasks):
    """
    Test endpoint to verify async background processing is working
    """
    async def test_async_task():
        """Simple async task for testing"""
        await asyncio.sleep(2)  # Simulate async work
        log_agent_activity("TestProcessor", "Async test completed", {
            "duration": 2,
            "status": "success"
        })
        return "Test completed"
    
    background_tasks.add_task(run_async_background_task, test_async_task())
    
    return {
        "message": "Async test task started",
        "status": "queued"
    }


@router.get("/status/{job_ids}")
async def get_batch_status(job_ids: str, db: Session = Depends(get_db)):
    """
    Get status of multiple batch processing jobs
    """
    try:
        # Parse comma-separated job IDs
        job_id_list = [int(job_id.strip()) for job_id in job_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    jobs = db.query(JobRecord).filter(JobRecord.id.in_(job_id_list)).all()
    
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found")
    
    job_statuses = []
    for job in jobs:
        status = BatchJobStatus(
            filename=job.filename,
            status=job.status,
            job_id=job.id,
            error=job.error_message
        )
        job_statuses.append(status)
    
    # Calculate overall status
    statuses = [job.status for job in jobs]
    if all(status == "completed" for status in statuses):
        overall_status = "completed"
    elif any(status == "failed" for status in statuses):
        overall_status = "partial_failure"
    elif any(status in ["processing", "queued"] for status in statuses):
        overall_status = "in_progress"
    else:
        overall_status = "unknown"
    
    return BatchStatusResponse(
        overall_status=overall_status,
        jobs=job_statuses,
        total_jobs=len(jobs),
        completed_jobs=len([j for j in jobs if j.status == "completed"]),
        failed_jobs=len([j for j in jobs if j.status == "failed"]),
        max_concurrent_jobs=MAX_CONCURRENT_JOBS,
        active_jobs=MAX_CONCURRENT_JOBS - job_semaphore._value
    )


@router.get("/concurrency-info")
async def get_concurrency_info():
    """
    Get information about current concurrency settings
    """
    return {
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "current_available_slots": job_semaphore._value,
        "active_jobs": MAX_CONCURRENT_JOBS - job_semaphore._value
    }


@router.post("/update-concurrency")
async def update_concurrency(max_jobs: int = 5):
    """
    Update the maximum number of concurrent jobs (requires restart to take effect)
    """
    global MAX_CONCURRENT_JOBS, job_semaphore
    
    if max_jobs < 1 or max_jobs > 20:
        raise HTTPException(status_code=400, detail="Max concurrent jobs must be between 1 and 20")
    
    old_max = MAX_CONCURRENT_JOBS
    MAX_CONCURRENT_JOBS = max_jobs
    
    # Note: Existing semaphore cannot be updated, this setting will take effect on restart
    log_agent_activity("BatchProcessor", "Concurrency setting updated", {
        "old_max_concurrent": old_max,
        "new_max_concurrent": MAX_CONCURRENT_JOBS,
        "note": "Change will take effect on application restart"
    })
    
    return {
        "message": f"Max concurrent jobs updated from {old_max} to {MAX_CONCURRENT_JOBS}",
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "note": "Change will take effect on application restart"
    }
