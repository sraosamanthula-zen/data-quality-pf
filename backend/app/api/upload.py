"""
File upload routes for the Data Quality Platform
"""

# Standard library imports
import os
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Third-party imports
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

# Local application imports
from app.core.config import settings
from app.services.agents.base_config import log_agent_activity
from app.db import get_db, JobRecord, FileProcessingMetrics, ReferenceFile

# Setup logging
logger = logging.getLogger(__name__)
from app.schemas import UploadResponse

router = APIRouter(prefix="/upload", tags=["upload"])


class DirectoryRequest(BaseModel):
    directory_path: str


@router.post("", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    selected_ucs: str = "UC1,UC4",  # Comma-separated list of UCs
    is_reference: str = "false",  # Whether this is a reference file
    db: Session = Depends(get_db),
):
    """
    Upload a file and create a job for data quality analysis

    Args:
        file: File to analyze (supports CSV, XLSX, XLS, TSV, JSON, Parquet)
        selected_ucs: Comma-separated list of UCs to run ("UC1", "UC4", or "UC1,UC4")
        is_reference: Whether this file is a reference file ("true" or "false")

    Returns:
        Job information (processing starts separately)
    """

    # Supported file extensions
    supported_extensions = [".csv", ".xlsx", ".xls", ".tsv", ".json", ".parquet"]

    # Validate filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file type
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_extension}. Supported types: {', '.join(supported_extensions)}",
        )

    # Parse and validate selected UCs
    uc_list = [uc.strip() for uc in selected_ucs.split(",")]
    valid_ucs = ["UC1", "UC4"]
    invalid_ucs = [uc for uc in uc_list if uc not in valid_ucs]

    if invalid_ucs:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid UCs: {invalid_ucs}. Valid options: {valid_ucs}",
        )

    if not uc_list:
        raise HTTPException(status_code=400, detail="At least one UC must be selected")

    # Parse is_reference flag
    is_ref = is_reference.lower() == "true"

    try:
        # Determine destination based on file type
        if is_ref:
            # Save reference files to uploads directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = settings.uploads_dir / safe_filename
        else:
            # For regular files, we'll save them temporarily first
            # They will be moved to proper job folders during processing
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{file.filename}"
            file_path = settings.uploads_dir / safe_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create job record with folder paths that will be created during processing
        job = JobRecord(
            filename=file.filename,
            file_path=str(file_path),
            job_type=",".join(uc_list),  # Store all selected UCs
            selected_ucs=selected_ucs,
            is_reference=is_ref,
            status="uploaded",  # New status: uploaded but not yet processing
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Record file metrics
        file_size = file_path.stat().st_size
        metrics = FileProcessingMetrics(job_id=job.id, file_size_bytes=file_size)
        db.add(metrics)
        db.commit()

        log_agent_activity(
            "FileUpload",
            "File uploaded successfully",
            {
                "job_id": job.id,
                "filename": file.filename,
                "file_extension": file_extension,
                "file_size": file_size,
                "selected_ucs": uc_list,
                "is_reference": is_ref,
            },
        )

        return UploadResponse(
            job_id=job.id,
            message=f"File uploaded successfully. Ready to process with: {', '.join(uc_list)}",
            filename=file.filename,
            job_type=",".join(uc_list),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/preview-file")
async def preview_file(filepath: str = None, filename: str = None, directory: str = None):
    """Preview a CSV file with limited rows"""
    try:
        # Determine the file path
        if filepath:
            file_path = Path(filepath)
        elif filename and directory:
            file_path = Path(directory) / filename
        elif filename:
            # Use default data directory if no directory specified
            data_directory = os.getenv("INPUT_DIRECTORY", str(settings.inputs_dir))
            file_path = Path(data_directory) / filename
        else:
            raise HTTPException(status_code=400, detail="Either filepath or filename must be provided")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        file_extension = file_path.suffix.lower()
        if file_extension not in ['.csv', '.tsv']:
            raise HTTPException(status_code=400, detail="Only CSV and TSV files can be previewed")
        
        import pandas as pd
        
        # Determine delimiter
        delimiter = '\t' if file_extension == '.tsv' else ','
        
        # Read only the first 100 rows for preview
        df = pd.read_csv(file_path, nrows=100, delimiter=delimiter)
        
        # Get total row count efficiently
        with open(file_path, 'r', encoding='utf-8') as f:
            total_rows = sum(1 for line in f) - 1  # Subtract header row
        
        return {
            "headers": df.columns.tolist(),
            "rows": df.fillna('').astype(str).values.tolist(),
            "totalRows": total_rows,
            "filename": file_path.name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing file: {str(e)}")

    try:
        import csv

        headers = []
        rows = []
        total_rows = 0

        # Determine delimiter based on file extension
        delimiter = "\t" if file_extension == ".tsv" else ","

        with open(file_path, "r", encoding="utf-8", errors="ignore") as csvfile:
            # Read file to count total rows
            total_rows = sum(1 for line in csvfile) - 1  # Subtract 1 for header

            # Reset file pointer
            csvfile.seek(0)

            # Read with CSV reader
            csv_reader = csv.reader(csvfile, delimiter=delimiter)

            # Get headers
            headers = next(csv_reader, [])

            # Get first 100 data rows
            for i, row in enumerate(csv_reader):
                if i >= 100:  # Limit to first 100 rows
                    break

                # Ensure row has same length as headers
                while len(row) < len(headers):
                    row.append("")

                rows.append(row[: len(headers)])  # Trim if longer than headers

        return {
            "filename": filename,
            "file_extension": file_extension,
            "delimiter": delimiter,
            "headers": headers,
            "rows": rows,
            "totalRows": total_rows,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.get("/files")
async def get_directory_files(directory: Optional[str] = None):
    """Get list of all supported files in the specified or configured input directory with their processing status"""
    if directory:
        data_directory = directory
    else:
        data_directory = os.getenv("INPUT_DIRECTORY", "./input_data")

    result_suffix = os.getenv("RESULT_SUFFIX", "_processed")
    output_directory = os.getenv("OUTPUT_DIRECTORY", "./output_data")

    # Supported file extensions (flexible for different file types)
    supported_extensions = [".csv", ".xlsx", ".xls", ".tsv", ".json", ".parquet"]

    if not os.path.exists(data_directory):
        raise HTTPException(
            status_code=404, detail=f"Input directory not found: {data_directory}"
        )

    files = []
    for file in os.listdir(data_directory):
        # Check if file has supported extension
        if any(file.lower().endswith(ext) for ext in supported_extensions):
            file_path = os.path.join(data_directory, file)
            try:
                file_stat = os.stat(file_path)

                # Check if this file has been processed (look in output directory)
                base_name = Path(file).stem
                processed_file = f"{base_name}{result_suffix}.csv"
                processed = os.path.exists(
                    os.path.join(output_directory, processed_file)
                )

                # Skip already processed files from the list (if they exist in input directory)
                if not file.endswith(f"{result_suffix}.csv"):
                    files.append(
                        {
                            "name": file,
                            "extension": Path(file).suffix.lower(),
                            "processed": processed,
                            "size": file_stat.st_size,
                            "lastModified": datetime.fromtimestamp(
                                file_stat.st_mtime
                            ).isoformat(),
                            "processedFile": processed_file if processed else None,
                        }
                    )
            except OSError:
                # Skip files that can't be accessed
                continue

    return {
        "files": files,
        "input_directory": data_directory,
        "output_directory": output_directory,
        "total_files": len(files),
        "supported_extensions": supported_extensions,
        "default_input_directory": os.getenv("INPUT_DIRECTORY", "./input_data"),
    }


@router.post("/set-directory")
async def set_directory(request: DirectoryRequest):
    """Set and validate a new directory for file processing"""
    directory_path = request.directory_path

    if not os.path.exists(directory_path):
        raise HTTPException(
            status_code=404, detail=f"Directory not found: {directory_path}"
        )

    if not os.path.isdir(directory_path):
        raise HTTPException(
            status_code=400, detail=f"Path is not a directory: {directory_path}"
        )

    # Check if directory has CSV files
    csv_files = [f for f in os.listdir(directory_path) if f.endswith(".csv")]

    return {
        "message": "Directory validated successfully",
        "directory": directory_path,
        "csv_files_count": len(csv_files),
        "has_csv_files": len(csv_files) > 0,
    }


@router.get("/reference-files")
async def get_reference_files(
    uc_type: Optional[str] = None, db: Session = Depends(get_db)
):
    """Get all reference files, optionally filtered by UC type"""
    query = db.query(ReferenceFile).filter(ReferenceFile.is_active)
    if uc_type:
        query = query.filter(ReferenceFile.uc_type == uc_type)

    reference_files = query.order_by(ReferenceFile.created_at.desc()).all()

    return {
        "reference_files": [
            {
                "id": rf.id,
                "uc_type": rf.uc_type,
                "filename": rf.filename,
                "description": rf.description,
                "created_at": rf.created_at.isoformat(),
            }
            for rf in reference_files
        ]
    }


@router.post("/reference-file")
async def upload_reference_file(
    file: UploadFile = File(...),
    uc_type: str = Form("UC1"),
    description: str = Form("Reference file"),
    db: Session = Depends(get_db),
):
    """Upload a reference file for a specific UC"""

    # Validate UC type
    if uc_type not in ["UC1", "UC4"]:
        raise HTTPException(status_code=400, detail="UC type must be UC1 or UC4")

    # Validate filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        # Save reference file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{uc_type}_{timestamp}_{file.filename}"
        file_path = settings.uploads_dir / safe_filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Deactivate previous reference files for this UC type
        db.query(ReferenceFile).filter(
            ReferenceFile.uc_type == uc_type, ReferenceFile.is_active
        ).update({"is_active": False})

        # Create new reference file record
        ref_file = ReferenceFile(
            uc_type=uc_type,
            filename=file.filename,
            file_path=str(file_path),
            description=description,
            is_active=True,
        )
        db.add(ref_file)
        db.commit()
        db.refresh(ref_file)

        log_agent_activity(
            "ReferenceFileUpload",
            f"Reference file uploaded for {uc_type}",
            {"uc_type": uc_type, "filename": file.filename, "ref_file_id": ref_file.id},
        )

        return {
            "id": ref_file.id,
            "message": f"Reference file uploaded successfully for {uc_type}",
            "filename": file.filename,
            "uc_type": uc_type,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Reference file upload failed: {str(e)}"
        )


@router.delete("/reference-file/{uc_type}")
async def remove_reference_file(uc_type: str, db: Session = Depends(get_db)):
    """Remove/deactivate reference file for a specific UC type"""

    # Validate UC type
    if uc_type not in ["UC1", "UC4"]:
        raise HTTPException(status_code=400, detail="UC type must be UC1 or UC4")

    try:
        # Deactivate all reference files for this UC type
        updated_count = (
            db.query(ReferenceFile)
            .filter(ReferenceFile.uc_type == uc_type, ReferenceFile.is_active)
            .update({"is_active": False})
        )

        db.commit()

        if updated_count == 0:
            raise HTTPException(
                status_code=404, detail=f"No active reference file found for {uc_type}"
            )

        log_agent_activity(
            "ReferenceFileRemoval",
            f"Reference file removed for {uc_type}",
            {"uc_type": uc_type, "removed_count": updated_count},
        )

        return {
            "message": f"Reference file removed successfully for {uc_type}",
            "uc_type": uc_type,
            "removed_count": updated_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove reference file: {str(e)}"
        )


@router.get("/reference-file/{uc_type}/history")
async def get_reference_file_history(uc_type: str, db: Session = Depends(get_db)):
    """Get upload history for reference files of a specific UC type"""

    # Validate UC type
    if uc_type not in ["UC1", "UC4"]:
        raise HTTPException(status_code=400, detail="UC type must be UC1 or UC4")

    reference_files = (
        db.query(ReferenceFile)
        .filter(ReferenceFile.uc_type == uc_type)
        .order_by(ReferenceFile.created_at.desc())
        .all()
    )

    return {
        "uc_type": uc_type,
        "history": [
            {
                "id": rf.id,
                "filename": rf.filename,
                "description": rf.description,
                "is_active": rf.is_active,
                "created_at": rf.created_at.isoformat(),
                "file_path": rf.file_path,
            }
            for rf in reference_files
        ],
        "total_uploads": len(reference_files),
        "active_count": len([rf for rf in reference_files if rf.is_active]),
    }


@router.post("/start-job-processing")
async def start_job_processing(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start processing a job using the JobProcessor with proper folder structure
    """
    from app.services.job_manager import JobProcessor
    
    # Get job record
    job = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job.status not in ["uploaded", "queued"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Job {job_id} cannot be processed. Current status: {job.status}"
        )
    
    if not job.selected_ucs:
        raise HTTPException(status_code=400, detail="No use cases selected for this job")
    
    # Parse selected use cases
    selected_ucs = [uc.strip() for uc in job.selected_ucs.split(",")]
    
    async def run_job_workflow():
        """Background task to execute job workflow using JobProcessor"""
        from app.db import SessionLocal
        job_db = None
        
        try:
            # Create fresh database session for the background task
            job_db = SessionLocal()
            
            # Create job processor
            processor = JobProcessor(job_db)
            
            # Get fresh job record
            job_record = job_db.query(JobRecord).filter(JobRecord.id == job_id).first()
            if not job_record:
                logger.error(f"Job {job_id} not found in database")
                return
            
            # If this is not a reference file, move it to the inputs folder
            if not job_record.is_reference:
                job_structure = processor.setup_job_folders(job_id)
                
                # Move uploaded file to inputs folder
                uploaded_file = Path(job_record.file_path)
                if uploaded_file.exists():
                    input_file = job_structure.inputs_folder / job_record.filename
                    shutil.move(str(uploaded_file), str(input_file))
                    
                    # Update job record with new file path
                    job_record.file_path = str(input_file)
                    job_db.commit()
            
            # Execute the complete workflow
            result = await processor.execute_job_workflow(job_id, selected_ucs)
            
            log_agent_activity(
                "JobProcessor",
                f"Job {job_id} workflow completed",
                {"job_id": job_id, "result": result},
            )
            
        except Exception as e:
            log_agent_activity(
                "JobProcessor",
                f"Job {job_id} workflow failed",
                {"job_id": job_id, "error": str(e)},
                "error",
            )
            
            # Update job status to failed with fresh session if needed
            try:
                if not job_db:
                    job_db = SessionLocal()
                job_record = job_db.query(JobRecord).filter(JobRecord.id == job_id).first()
                if job_record:
                    job_record.status = "failed"
                    job_record.error_message = str(e)
                    job_record.completed_at = datetime.utcnow()
                    job_db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update job status to failed: {db_error}")
        finally:
            if job_db:
                job_db.close()
    
    # Add task to background processing
    background_tasks.add_task(run_job_workflow)
    
    # Update job status to processing
    job.status = "queued"
    job.started_at = datetime.utcnow()
    db.commit()
    
    log_agent_activity(
        "JobProcessor",
        f"Started job {job_id} with JobProcessor",
        {"job_id": job_id, "selected_ucs": selected_ucs},
    )
    
    return {
        "message": f"Job {job_id} started with JobProcessor",
        "job_id": job_id,
        "status": "queued",
        "selected_ucs": selected_ucs,
        "workflow_features": [
            "Automatic folder structure creation",
            "CSV file detection in inputs folder",
            "Use case processing with proper temp folders",
            "Final output organization",
            "Comprehensive result archival"
        ]
    }


@router.get("/list-directories")
async def list_directories(path: str = ""):
    """List available directories for browsing"""
    try:
        base_path = Path.home() if not path else Path(path)
        if not base_path.exists() or not base_path.is_dir():
            base_path = Path.home()
        
        directories = []
        try:
            for item in base_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    directories.append(str(item.resolve()))
        except PermissionError:
            pass
        
        return {
            "directories": sorted(directories),
            "current_path": str(base_path.resolve())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing directories: {str(e)}")


@router.get("/download-file")
async def download_file(filepath: Optional[str] = None, filename: Optional[str] = None, directory: Optional[str] = None):
    """Download a file from the specified path"""
    try:
        # Determine the file path
        if filepath:
            file_path = Path(filepath)
        elif filename and directory:
            file_path = Path(directory) / filename
        else:
            raise HTTPException(status_code=400, detail="Either filepath or both filename and directory must be provided")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")
