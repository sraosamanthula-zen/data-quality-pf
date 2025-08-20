"""
Batch processing routes for the Data Quality Platform
"""

# Standard library imports
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Third-party imports
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Local application imports
from agents.base_config import log_agent_activity
from database import get_db, JobRecord, FileProcessingMetrics
from models import BatchStatusResponse

router = APIRouter(prefix="/batch", tags=["batch"])

# Global semaphore to limit concurrent processing jobs to 5
MAX_CONCURRENT_JOBS = 5
job_semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)


async def restart_queued_jobs(queued_jobs: List[JobRecord]):
    """
    Restart queued jobs from server recovery.
    This function processes jobs that were interrupted by server restart.
    """
    from database import SessionLocal
    
    logger = log_agent_activity
    logger("JobRecovery", f"Starting restart of {len(queued_jobs)} queued jobs", {
        "job_count": len(queued_jobs),
        "max_concurrent": MAX_CONCURRENT_JOBS
    })
    
    # Process jobs in batches based on the semaphore limit
    async def restart_single_job(job: JobRecord):
        """Restart a single job with proper error handling"""
        db = SessionLocal()
        try:
            # Refresh job to get current state
            job = db.query(JobRecord).filter(JobRecord.id == job.id).first()
            if not job or job.status != "queued":
                return
            
            # Parse selected UCs and reference file paths
            selected_ucs = job.selected_ucs.split(",") if job.selected_ucs else []
            
            # Parse reference file paths from the stored string
            reference_files_by_uc = {}
            if job.reference_file_path:
                try:
                    # Try to parse as JSON first
                    reference_files_by_uc = json.loads(job.reference_file_path.replace("'", '"'))
                except (json.JSONDecodeError, AttributeError):
                    # Fallback for older format - get active reference files
                    from database import ReferenceFile
                    for uc in selected_ucs:
                        ref_file = db.query(ReferenceFile).filter(
                            ReferenceFile.uc_type == uc,
                            ReferenceFile.is_active
                        ).first()
                        if ref_file:
                            reference_files_by_uc[uc] = ref_file.file_path
            
            # Validate that we have the required data
            if not selected_ucs or not reference_files_by_uc:
                logger("JobRecovery", f"Skipping job {job.id} - missing UC or reference file data", {
                    "job_id": job.id,
                    "selected_ucs": selected_ucs,
                    "reference_files": reference_files_by_uc
                }, "warning")
                return
            
            # Check if file still exists
            if not os.path.exists(job.file_path):
                logger("JobRecovery", f"Skipping job {job.id} - file not found: {job.file_path}", {
                    "job_id": job.id,
                    "file_path": job.file_path
                }, "warning")
                job.status = "failed"
                job.error_message = f"File not found: {job.file_path}"
                db.commit()
                return
            
            logger("JobRecovery", f"Restarting job {job.id}: {job.filename}", {
                "job_id": job.id,
                "filename": job.filename,
                "selected_ucs": selected_ucs,
                "reference_files": list(reference_files_by_uc.keys())
            })
            
            # Start the job processing
            await process_file_with_reference_async(
                job.file_path,
                reference_files_by_uc,
                selected_ucs,
                job.id
            )
            
        except Exception as e:
            logger("JobRecovery", f"Failed to restart job {job.id}", {
                "job_id": job.id,
                "error": str(e)
            }, "error")
            
            # Update job status to failed
            try:
                job.status = "failed"
                job.error_message = f"Recovery failed: {str(e)}"
                db.commit()
            except Exception:
                db.rollback()
        finally:
            db.close()
    
    # Create semaphore-controlled tasks
    async def restart_with_semaphore(job):
        async with job_semaphore:
            await restart_single_job(job)
    
    # Create tasks for all jobs
    tasks = [restart_with_semaphore(job) for job in queued_jobs]
    
    # Run all tasks with concurrency control
    try:
        await asyncio.gather(*tasks, return_exceptions=True)
        logger("JobRecovery", f"Completed restart attempt for {len(queued_jobs)} jobs", {
            "job_count": len(queued_jobs),
            "status": "completed"
        })
    except Exception as e:
        logger("JobRecovery", "Job restart batch failed", {
            "error": str(e),
            "job_count": len(queued_jobs)
        }, "error")


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
        
        # Create file metrics and generate unique filename for this job
        file_size = Path(file_path).stat().st_size
        
        # Generate unique filename based on job ID and timestamp
        unique_filename = f"job_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        metrics = FileProcessingMetrics(
            job_id=job_id,
            file_size_bytes=file_size
        )
        db.add(metrics)
        db.commit()
        
        log_processing_step(job_id, "BatchProcessor", "File metrics recorded with unique filename", {
            "file_size_bytes": file_size,
            "unique_filename": unique_filename
        })
        
        all_results = {}
        output_file_path = None
        
        # Run selected UCs with proper async handling and sequential processing
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
                    uc1_result = await run_uc1_analysis(file_path, reference_file_path, unique_filename=unique_filename)
                    
                    # Store the output file path for tracking
                    if hasattr(uc1_result, 'output_file_path'):
                        output_file_path = uc1_result.output_file_path
                    
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
                    
                    # Use the output file from UC1 if it exists, otherwise use original file
                    input_file_for_uc4 = output_file_path if output_file_path and os.path.exists(output_file_path) else file_path
                    
                    uc4_result = await run_uc4_analysis(input_file_for_uc4, reference_file_path, unique_filename=unique_filename)
                    
                    # Store the final output file path
                    if hasattr(uc4_result, 'output_file_path'):
                        output_file_path = uc4_result.output_file_path
                    
                    # Convert Pydantic model to dict and extract duplicate info
                    if hasattr(uc4_result, 'dict'):
                        all_results["UC4"] = uc4_result.dict()
                        
                        # Update job with duplicate statistics from UC4 result
                        if hasattr(uc4_result, 'duplicate_rows_removed'):
                            job.duplicate_count = uc4_result.duplicate_rows_removed
                        if hasattr(uc4_result, 'duplicate_percentage'):
                            job.duplicate_percentage = uc4_result.duplicate_percentage
                        if hasattr(uc4_result, 'total_rows_original'):
                            job.total_rows_original = uc4_result.total_rows_original
                        if hasattr(uc4_result, 'total_rows_processed'):
                            job.total_rows_processed = uc4_result.total_rows_processed
                        if hasattr(uc4_result, 'duplicate_rows_removed') and uc4_result.duplicate_rows_removed > 0:
                            job.has_duplicates = True
                        else:
                            job.has_duplicates = False
                    else:
                        all_results["UC4"] = uc4_result
                    
                    log_agent_activity("UC4", f"Async analysis completed for {filename}", {
                        "job_id": job_id,
                        "success": True,
                        "duration_ms": (datetime.now() - uc_start_time).total_seconds() * 1000,
                        "duplicates_removed": getattr(uc4_result, 'duplicate_rows_removed', 0),
                        "duplicate_percentage": getattr(uc4_result, 'duplicate_percentage', 0.0)
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
        
        # Update job with results and output file path
        job.result_file_path = str(result_path)
        if output_file_path:
            # Store the actual output CSV file path in a new field
            job.results_json = json.dumps({
                "output_file_path": output_file_path,
                "unique_filename": unique_filename,
                "results": all_results
            }, default=json_serializer)
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
    Process all supported files from input directory against reference files for selected UCs in parallel
    """
    # DEBUG: Log incoming request
    print("🔥 DEBUG: Received batch processing request:")
    print(f"   Directory: {request.directory_path}")
    print(f"   Selected UCs: {request.selected_ucs}")
    print(f"   Reference paths: {request.reference_file_paths}")
    
    # Use provided directory or default input directory from environment
    input_directory = request.directory_path if request.directory_path else os.getenv("INPUT_DIRECTORY", "/home/sraosamanthula/ZENLABS/RCL_Files/input_data")
    output_directory = os.getenv("OUTPUT_DIRECTORY", "/home/sraosamanthula/ZENLABS/RCL_Files/output_data")
    
    if not os.path.exists(input_directory):
        raise HTTPException(status_code=404, detail=f"Input directory not found: {input_directory}")
    
    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)
    
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
    
    # Get all supported files in the input directory (excluding already processed ones)
    result_suffix = os.getenv("RESULT_SUFFIX", "_processed")
    supported_extensions = ['.csv', '.xlsx', '.xls', '.tsv', '.json', '.parquet']
    supported_files = []
    
    for file in os.listdir(input_directory):
        # Check if file has supported extension
        if any(file.lower().endswith(ext) for ext in supported_extensions):
            file_path = os.path.join(input_directory, file)
            if os.path.isfile(file_path):
                # Check if already processed (look in output directory)
                base_name = Path(file).stem
                processed_file = f"{base_name}{result_suffix}.csv"
                if not os.path.exists(os.path.join(output_directory, processed_file)):
                    supported_files.append(file)
    
    if not supported_files:
        raise HTTPException(status_code=404, detail=f"No unprocessed supported files found in directory: {input_directory}. Supported extensions: {', '.join(supported_extensions)}")
    
    # Create jobs for all files first
    job_ids = []
    job_data_list = []
    
    for filename in supported_files:
        file_path = os.path.join(input_directory, filename)
        
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
                "input_directory": input_directory,
                "output_directory": output_directory,
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
                "max_concurrent": MAX_CONCURRENT_JOBS,
                "input_directory": input_directory,
                "output_directory": output_directory
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
        "input_directory": input_directory,
        "output_directory": output_directory,
        "files_count": len(supported_files),
        "selected_ucs": request.selected_ucs,
        "reference_files": reference_files_by_uc,
        "job_ids": job_ids,
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "supported_extensions": supported_extensions
    })
    
    return {
        "message": f"Started parallel processing {len(supported_files)} files from input directory with UCs: {', '.join(request.selected_ucs)} (max {MAX_CONCURRENT_JOBS} concurrent jobs)",
        "job_ids": job_ids,
        "input_directory": input_directory,
        "output_directory": output_directory,
        "total_files": len(supported_files),
        "selected_ucs": request.selected_ucs,
        "reference_files": {uc: os.path.basename(path) for uc, path in reference_files_by_uc.items()},
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "supported_extensions": supported_extensions
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


@router.post("/recover-jobs")
async def manually_recover_jobs(
    auto_restart: bool = False,
    background_tasks: BackgroundTasks = None, 
    db: Session = Depends(get_db)
):
    """
    Manually trigger job recovery for stuck or queued jobs
    
    Args:
        auto_restart: If True, will restart queued jobs automatically
    """
    # Find stuck jobs
    stuck_processing_statuses = ["processing", "processing_uc1", "processing_uc4", 
                               "analyzing_completeness", "detecting_duplicates", "cleaning_file"]
    
    stuck_jobs = db.query(JobRecord).filter(JobRecord.status.in_(stuck_processing_statuses)).all()
    
    # Mark stuck jobs as failed instead of queuing them
    for job in stuck_jobs:
        log_agent_activity("JobRecovery", f"Manually marking stuck job {job.id} as failed", {
            "job_id": job.id,
            "filename": job.filename,
            "previous_status": job.status
        })
        job.status = "failed"
        job.started_at = None
        job.completed_at = datetime.utcnow()
        job.error_message = f"Manually marked as failed - was stuck in {job.status} state"
    
    db.commit()
    
    # Get all queued jobs
    queued_jobs = db.query(JobRecord).filter(JobRecord.status == "queued").all()
    
    restart_count = 0
    # Start recovery in background only if auto_restart is True
    if auto_restart and queued_jobs and background_tasks:
        background_tasks.add_task(restart_queued_jobs, queued_jobs)
        restart_count = len(queued_jobs)
        
    log_agent_activity("JobRecovery", "Manual job recovery initiated", {
        "stuck_jobs_failed": len(stuck_jobs),
        "total_queued_jobs": len(queued_jobs),
        "auto_restart_enabled": auto_restart,
        "will_restart": restart_count
    })
    
    return {
        "message": f"Job recovery completed. Marked {len(stuck_jobs)} stuck jobs as failed. Found {len(queued_jobs)} queued jobs." + 
                  (f" Restarting {restart_count} jobs in background." if auto_restart else " Use auto_restart=true to restart queued jobs."),
        "stuck_jobs_failed": len(stuck_jobs),
        "queued_jobs_found": len(queued_jobs),
        "will_restart_jobs": restart_count,
        "auto_restart_enabled": auto_restart,
        "status": "recovery_completed"
    }


@router.get("/stuck-jobs")
async def get_stuck_jobs(db: Session = Depends(get_db)):
    """
    Get information about stuck or queued jobs
    """
    stuck_processing_statuses = ["processing", "processing_uc1", "processing_uc4", 
                               "analyzing_completeness", "detecting_duplicates", "cleaning_file"]
    
    stuck_jobs = db.query(JobRecord).filter(JobRecord.status.in_(stuck_processing_statuses)).all()
    queued_jobs = db.query(JobRecord).filter(JobRecord.status == "queued").all()
    
    def job_to_dict(job):
        return {
            "id": job.id,
            "filename": job.filename,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "selected_ucs": job.selected_ucs,
            "error_message": job.error_message
        }
    
    return {
        "stuck_jobs": [job_to_dict(job) for job in stuck_jobs],
        "queued_jobs": [job_to_dict(job) for job in queued_jobs],
        "total_stuck": len(stuck_jobs),
        "total_queued": len(queued_jobs),
        "recovery_available": len(stuck_jobs) > 0 or len(queued_jobs) > 0
    }
