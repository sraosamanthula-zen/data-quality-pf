"""
File upload routes for the Data Quality Platform
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db, JobRecord, FileProcessingMetrics, ReferenceFile
from models import UploadResponse
from agents.base_config import log_agent_activity

router = APIRouter(prefix="/upload", tags=["upload"])

# Get configuration from environment
UPLOAD_DIR = Path(os.getenv("UPLOADS_DIRECTORY", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

REFERENCE_DIR = Path(os.getenv("REFERENCE_FILES_DIRECTORY", "./reference_files"))
REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

class DirectoryRequest(BaseModel):
    directory_path: str


@router.post("", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    selected_ucs: str = "UC1,UC4",  # Comma-separated list of UCs
    is_reference: str = "false",  # Whether this is a reference file
    db: Session = Depends(get_db)
):
    """
    Upload a CSV file and create a job for data quality analysis
    
    Args:
        file: CSV file to analyze
        selected_ucs: Comma-separated list of UCs to run ("UC1", "UC4", or "UC1,UC4")
        is_reference: Whether this file is a reference file ("true" or "false")
        
    Returns:
        Job information (processing starts separately)
    """
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # Parse and validate selected UCs
    uc_list = [uc.strip() for uc in selected_ucs.split(",")]
    valid_ucs = ["UC1", "UC4"]
    invalid_ucs = [uc for uc in uc_list if uc not in valid_ucs]
    
    if invalid_ucs:
        raise HTTPException(status_code=400, detail=f"Invalid UCs: {invalid_ucs}. Valid options: {valid_ucs}")
    
    if not uc_list:
        raise HTTPException(status_code=400, detail="At least one UC must be selected")
    
    # Parse is_reference flag
    is_ref = is_reference.lower() == "true"
    
    try:
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create job record
        job = JobRecord(
            filename=file.filename,
            file_path=str(file_path),
            job_type=",".join(uc_list),  # Store all selected UCs
            selected_ucs=selected_ucs,
            is_reference=is_ref,
            status="uploaded"  # New status: uploaded but not yet processing
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Record file metrics
        file_size = file_path.stat().st_size
        metrics = FileProcessingMetrics(
            job_id=job.id,
            file_size_bytes=file_size
        )
        db.add(metrics)
        db.commit()
        
        log_agent_activity("FileUpload", "File uploaded successfully", 
                         {
                             "job_id": job.id, 
                             "filename": file.filename, 
                             "file_size": file_size, 
                             "selected_ucs": uc_list,
                             "is_reference": is_ref
                         })
        
        return UploadResponse(
            job_id=job.id,
            message=f"File uploaded successfully. Ready to process with: {', '.join(uc_list)}",
            filename=file.filename,
            job_type=",".join(uc_list)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/preview-file")
async def preview_file(filename: str, directory: str = None):
    """Get a preview of a CSV file with first few rows"""
    if directory:
        data_directory = directory
    else:
        data_directory = os.getenv("DATA_DIRECTORY", "/home/sraosamanthula/ZENLABS/RCL_Files")
    
    file_path = os.path.join(data_directory, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    if not filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files can be previewed")
    
    try:
        import csv
        
        headers = []
        rows = []
        total_rows = 0
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
            # Read file to count total rows
            total_rows = sum(1 for line in csvfile) - 1  # Subtract 1 for header
            
            # Reset file pointer
            csvfile.seek(0)
            
            # Read with CSV reader
            csv_reader = csv.reader(csvfile)
            
            # Get headers
            headers = next(csv_reader, [])
            
            # Get first 100 data rows
            for i, row in enumerate(csv_reader):
                if i >= 100:  # Limit to first 100 rows
                    break
                    
                # Ensure row has same length as headers
                while len(row) < len(headers):
                    row.append('')
                    
                rows.append(row[:len(headers)])  # Trim if longer than headers
        
        return {
            "filename": filename,
            "headers": headers,
            "rows": rows,
            "totalRows": total_rows
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.get("/directory-files")
async def get_directory_files(directory: str = None):
    """Get list of all files in the specified or configured data directory with their processing status"""
    if directory:
        data_directory = directory
    else:
        data_directory = os.getenv("DATA_DIRECTORY", "/home/sraosamanthula/ZENLABS/RCL_Files")
    
    result_suffix = os.getenv("RESULT_SUFFIX", "_processed")
    
    if not os.path.exists(data_directory):
        raise HTTPException(status_code=404, detail=f"Data directory not found: {data_directory}")
    
    files = []
    for file in os.listdir(data_directory):
        if file.endswith('.csv'):
            file_path = os.path.join(data_directory, file)
            try:
                file_stat = os.stat(file_path)
                
                # Check if this file has been processed (has a corresponding _processed file)
                processed_file = file.replace('.csv', f'{result_suffix}.csv')
                processed = os.path.exists(os.path.join(data_directory, processed_file))
                
                # Skip already processed files from the list
                if not file.endswith(f'{result_suffix}.csv'):
                    files.append({
                        "name": file,
                        "processed": processed,
                        "size": file_stat.st_size,
                        "lastModified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    })
            except OSError:
                # Skip files that can't be accessed
                continue
    
    return {
        "files": files,
        "directory": data_directory,
        "total_files": len(files),
        "default_directory": os.getenv("DATA_DIRECTORY", "/home/sraosamanthula/ZENLABS/RCL_Files")
    }


@router.post("/set-directory")
async def set_directory(request: DirectoryRequest):
    """Set and validate a new directory for file processing"""
    directory_path = request.directory_path
    
    if not os.path.exists(directory_path):
        raise HTTPException(status_code=404, detail=f"Directory not found: {directory_path}")
    
    if not os.path.isdir(directory_path):
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {directory_path}")
    
    # Check if directory has CSV files
    csv_files = [f for f in os.listdir(directory_path) if f.endswith('.csv')]
    
    return {
        "message": "Directory validated successfully",
        "directory": directory_path,
        "csv_files_count": len(csv_files),
        "has_csv_files": len(csv_files) > 0
    }


@router.get("/reference-files")
async def get_reference_files(uc_type: str = None, db: Session = Depends(get_db)):
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
                "created_at": rf.created_at.isoformat()
            }
            for rf in reference_files
        ]
    }


@router.post("/reference-file")
async def upload_reference_file(
    file: UploadFile = File(...),
    uc_type: str = Form("UC1"),
    description: str = Form("Reference file"),
    db: Session = Depends(get_db)
):
    """Upload a reference file for a specific UC"""
    
    # Validate UC type
    if uc_type not in ["UC1", "UC4"]:
        raise HTTPException(status_code=400, detail="UC type must be UC1 or UC4")
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        # Save reference file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{uc_type}_{timestamp}_{file.filename}"
        file_path = REFERENCE_DIR / safe_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Deactivate previous reference files for this UC type
        db.query(ReferenceFile).filter(
            ReferenceFile.uc_type == uc_type,
            ReferenceFile.is_active
        ).update({"is_active": False})
        
        # Create new reference file record
        ref_file = ReferenceFile(
            uc_type=uc_type,
            filename=file.filename,
            file_path=str(file_path),
            description=description,
            is_active=True
        )
        db.add(ref_file)
        db.commit()
        db.refresh(ref_file)
        
        log_agent_activity("ReferenceFileUpload", f"Reference file uploaded for {uc_type}", 
                         {"uc_type": uc_type, "filename": file.filename, "ref_file_id": ref_file.id})
        
        return {
            "id": ref_file.id,
            "message": f"Reference file uploaded successfully for {uc_type}",
            "filename": file.filename,
            "uc_type": uc_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reference file upload failed: {str(e)}")


@router.delete("/reference-file/{uc_type}")
async def remove_reference_file(uc_type: str, db: Session = Depends(get_db)):
    """Remove/deactivate reference file for a specific UC type"""
    
    # Validate UC type
    if uc_type not in ["UC1", "UC4"]:
        raise HTTPException(status_code=400, detail="UC type must be UC1 or UC4")
    
    try:
        # Deactivate all reference files for this UC type
        updated_count = db.query(ReferenceFile).filter(
            ReferenceFile.uc_type == uc_type,
            ReferenceFile.is_active
        ).update({"is_active": False})
        
        db.commit()
        
        if updated_count == 0:
            raise HTTPException(status_code=404, detail=f"No active reference file found for {uc_type}")
        
        log_agent_activity("ReferenceFileRemoval", f"Reference file removed for {uc_type}", 
                         {"uc_type": uc_type, "removed_count": updated_count})
        
        return {
            "message": f"Reference file removed successfully for {uc_type}",
            "uc_type": uc_type,
            "removed_count": updated_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove reference file: {str(e)}")


@router.get("/reference-file/{uc_type}/history")
async def get_reference_file_history(uc_type: str, db: Session = Depends(get_db)):
    """Get upload history for reference files of a specific UC type"""
    
    # Validate UC type
    if uc_type not in ["UC1", "UC4"]:
        raise HTTPException(status_code=400, detail="UC type must be UC1 or UC4")
    
    reference_files = db.query(ReferenceFile).filter(
        ReferenceFile.uc_type == uc_type
    ).order_by(ReferenceFile.created_at.desc()).all()
    
    return {
        "uc_type": uc_type,
        "history": [
            {
                "id": rf.id,
                "filename": rf.filename,
                "description": rf.description,
                "is_active": rf.is_active,
                "created_at": rf.created_at.isoformat(),
                "file_path": rf.file_path
            }
            for rf in reference_files
        ],
        "total_uploads": len(reference_files),
        "active_count": len([rf for rf in reference_files if rf.is_active])
    }
