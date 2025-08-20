"""
Agentic AI Data Quality Platform - FastAPI Backend

This FastAPI application provides endpoints for UC1 (Sparse Data Detection) and UC4 (Duplicate Detection)
using the Agno framework with Azure OpenAI for comprehensive data quality analysis.
"""

# Standard library imports
import logging
import os
from datetime import datetime
from pathlib import Path

# Third-party imports
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Local application imports
from agents.base_config import AgentConfig, log_agent_activity
from database import init_db, JobRecord
from routes import jobs, upload, batch

# Load environment variables
load_dotenv()

# Initialize logging first
logger = logging.getLogger(__name__)


async def recover_stuck_jobs(auto_restart: bool = False):
    """
    Recover jobs that were stuck in processing states when server was restarted.
    Reset processing jobs to failed status to prevent automatic restart issues.
    
    Args:
        auto_restart: If True, will restart queued jobs. If False, just cleans up stuck jobs.
    """
    from database import get_db_session
    
    with get_db_session() as db:
        try:
            # Define stuck statuses that need recovery
            stuck_processing_statuses = ["processing", "processing_uc1", "processing_uc4", 
                                       "analyzing_completeness", "detecting_duplicates", "cleaning_file"]
            
            # Mark stuck processing jobs as failed instead of queuing them
            stuck_jobs = db.query(JobRecord).filter(JobRecord.status.in_(stuck_processing_statuses)).all()
            
            for job in stuck_jobs:
                logger.info(f"🔄 Marking stuck job {job.id} as failed: {job.filename} (was {job.status})")
                job.status = "failed"
                job.started_at = None
                job.completed_at = datetime.utcnow()
                job.error_message = f"Job was stuck in {job.status} state during server restart"
                log_agent_activity("JobRecovery", f"Marked stuck job {job.id} as failed", {
                    "job_id": job.id,
                    "filename": job.filename,
                    "previous_status": job.status
                })
            
            # Check for jobs with missing files and mark them as failed
            pending_jobs = db.query(JobRecord).filter(JobRecord.status.in_(["queued", "uploaded", "pending"])).all()
            failed_missing_files = []
            
            for job in pending_jobs:
                if not os.path.exists(job.file_path):
                    logger.warning(f"❌ Job {job.id} file not found: {job.file_path}")
                    job.status = "failed"
                    job.error_message = f"File not found during recovery: {job.file_path}"
                    job.completed_at = datetime.utcnow()
                    failed_missing_files.append(job)
                    log_agent_activity("JobRecovery", f"Job {job.id} marked as failed - file not found", {
                        "job_id": job.id,
                        "filename": job.filename,
                        "file_path": job.file_path
                    })
            
            # Get remaining queued jobs after cleanup
            remaining_queued = db.query(JobRecord).filter(JobRecord.status == "queued").all()
            
            logger.info(f"🔄 Job recovery summary: {len(stuck_jobs)} stuck jobs marked as failed, {len(failed_missing_files)} jobs with missing files failed, {len(remaining_queued)} jobs still queued")
            log_agent_activity("JobRecovery", "Job recovery completed", {
                "stuck_jobs_failed": len(stuck_jobs),
                "missing_file_jobs_failed": len(failed_missing_files),
                "remaining_queued_jobs": len(remaining_queued),
                "auto_restart_enabled": auto_restart
            })
            
            # Only restart queued jobs if explicitly requested
            restart_count = 0
            if auto_restart and remaining_queued:
                logger.info(f"🚀 Auto-restart enabled: restarting {len(remaining_queued)} queued jobs")
                try:
                    # Import here to avoid circular import
                    from routes.batch import restart_queued_jobs
                    await restart_queued_jobs(remaining_queued)
                    restart_count = len(remaining_queued)
                except Exception as restart_error:
                    logger.error(f"❌ Failed to restart queued jobs: {restart_error}")
                    log_agent_activity("JobRecovery", "Auto-restart failed", {"error": str(restart_error)}, "error")
            else:
                logger.info(f"ℹ️  Auto-restart disabled: {len(remaining_queued)} jobs remain queued (use manual restart if needed)")
            
            return {
                "stuck_jobs_failed": len(stuck_jobs), 
                "missing_file_jobs_failed": len(failed_missing_files),
                "remaining_queued_jobs": len(remaining_queued),
                "restarted_jobs": restart_count
            }
            
        except Exception as e:
            logger.error(f"❌ Job recovery failed: {e}")
            log_agent_activity("JobRecovery", "Job recovery failed", {"error": str(e)}, "error")
            raise


async def start_background_job_recovery():
    """
    Start background job recovery service
    """
    try:
        logger.info("🚀 Starting background job recovery service...")
        log_agent_activity("JobRecovery", "Background job recovery service started", {"status": "active"})
    except Exception as e:
        logger.error(f"❌ Background job recovery service failed to start: {e}")
        log_agent_activity("JobRecovery", "Background job recovery service failed", {"error": str(e)}, "error")

# Configuration from environment variables
class Config:
    # Input directory where files are read from
    INPUT_DIRECTORY = os.getenv("INPUT_DIRECTORY", "/home/sraosamanthula/ZENLABS/RCL_Files/input_data")
    
    # Output directory where processed files are written
    OUTPUT_DIRECTORY = os.getenv("OUTPUT_DIRECTORY", "/home/sraosamanthula/ZENLABS/RCL_Files/output_data")
    
    # Legacy directories (keeping for backward compatibility)
    DATA_DIRECTORY = os.getenv("DATA_DIRECTORY", "/home/sraosamanthula/ZENLABS/RCL_Files")
    UPLOADS_DIRECTORY = os.getenv("UPLOADS_DIRECTORY", "./uploads")
    REFERENCE_FILES_DIRECTORY = os.getenv("REFERENCE_FILES_DIRECTORY", "./reference_files")
    STORAGE_DIRECTORY = os.getenv("STORAGE_DIRECTORY", "./storage")
    
    # Result file naming
    RESULT_SUFFIX = os.getenv("RESULT_SUFFIX", "_processed")
    BATCH_PROCESSING = os.getenv("BATCH_PROCESSING", "true").lower() == "true"
    
    # Supported file extensions (flexible for different file types)
    SUPPORTED_EXTENSIONS = ['.csv', '.xlsx', '.xls', '.tsv', '.json', '.parquet']
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.INPUT_DIRECTORY,
            cls.OUTPUT_DIRECTORY,
            cls.UPLOADS_DIRECTORY,
            cls.REFERENCE_FILES_DIRECTORY,
            cls.STORAGE_DIRECTORY
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Directory ensured: {directory}")
            
    @classmethod
    def get_supported_files(cls, directory_path: str):
        """Get all supported files in a directory"""
        supported_files = []
        if os.path.exists(directory_path):
            for file in os.listdir(directory_path):
                if any(file.lower().endswith(ext) for ext in cls.SUPPORTED_EXTENSIONS):
                    # Skip already processed files
                    if not file.endswith(f'{cls.RESULT_SUFFIX}.csv'):
                        supported_files.append(file)
        return supported_files
            
# Global config instance
config = Config()


# FastAPI Application
app = FastAPI(
    title="Agentic AI Data Quality Platform",
    description="Advanced data quality analysis using UC1 (Sparse Data Detection) and UC4 (Duplicate Detection) agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router)
app.include_router(upload.router)
app.include_router(batch.router)


# Add direct statistics route for frontend compatibility
@app.get("/statistics")
async def get_statistics():
    """Direct statistics endpoint for frontend compatibility"""
    from database import get_db_session
    from sqlalchemy.sql import func
    from database import JobRecord
    
    with get_db_session() as db:
        try:
            total_jobs = db.query(JobRecord).count()
            
            # Include 'uploaded', 'pending', and 'queued' as pending jobs
            pending_statuses = ["uploaded", "pending", "queued"]
            pending_jobs = db.query(JobRecord).filter(JobRecord.status.in_(pending_statuses)).count()
            
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
            
            return {
                "total_jobs": total_jobs,
                "pending_jobs": pending_jobs,
                "processing_jobs": processing_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "average_quality_score": float(avg_quality) if avg_quality else None
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise


@app.get("/config")
async def get_config():
    """Get platform configuration"""
    return {
        "input_directory": config.INPUT_DIRECTORY,
        "output_directory": config.OUTPUT_DIRECTORY,
        "data_directory": config.DATA_DIRECTORY,  # Legacy
        "uploads_directory": config.UPLOADS_DIRECTORY,
        "reference_files_directory": config.REFERENCE_FILES_DIRECTORY,
        "storage_directory": config.STORAGE_DIRECTORY,
        "result_suffix": config.RESULT_SUFFIX,
        "batch_processing_enabled": config.BATCH_PROCESSING,
        "supported_extensions": config.SUPPORTED_EXTENSIONS
    }


@app.on_event("startup")
async def startup_event():
    """Initialize the application and validate configuration"""
    logger.info("🚀 Starting Agentic AI Data Quality Platform...")
    log_agent_activity("Platform", "Application startup initiated", {
        "version": "1.0.0",
        "startup_time": datetime.now().isoformat()
    })
    
    # Ensure directories exist
    try:
        config.ensure_directories()
        logger.info("✅ Directories created/validated successfully")
        log_agent_activity("Platform", "Directory setup completed", {"status": "success"})
    except Exception as e:
        logger.error(f"❌ Directory setup failed: {e}")
        log_agent_activity("Platform", "Directory setup failed", {"error": str(e)}, "error")
        raise
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
        log_agent_activity("Platform", "Database initialization completed", {"status": "success"})
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        log_agent_activity("Platform", "Database initialization failed", {"error": str(e)}, "error")
        raise
    
    # Recover stuck jobs from previous session (but don't auto-restart)
    try:
        recovery_result = await recover_stuck_jobs(auto_restart=False)  # Disable auto-restart to prevent stuck backend
        logger.info(f"✅ Job recovery completed successfully: {recovery_result}")
        log_agent_activity("Platform", "Job recovery completed", {
            "status": "success",
            "stuck_jobs_failed": recovery_result.get("stuck_jobs_failed", 0),
            "missing_file_jobs_failed": recovery_result.get("missing_file_jobs_failed", 0),
            "remaining_queued_jobs": recovery_result.get("remaining_queued_jobs", 0),
            "auto_restart_enabled": False
        })
    except Exception as e:
        logger.error(f"❌ Job recovery failed: {e}")
        log_agent_activity("Platform", "Job recovery failed", {"error": str(e)}, "error")
        # Don't raise here - we want the server to start even if recovery fails
    
    # Start background job recovery service
    try:
        await start_background_job_recovery()
        logger.info("✅ Background job recovery service started")
        log_agent_activity("Platform", "Background job recovery service started", {"status": "active"})
    except Exception as e:
        logger.error(f"❌ Background job recovery service failed: {e}")
        log_agent_activity("Platform", "Background job recovery service failed", {"error": str(e)}, "error")
    
    # Validate Azure OpenAI configuration
    try:
        AgentConfig()
        logger.info("✅ Azure OpenAI configuration validated")
        log_agent_activity("Platform", "Azure OpenAI configuration validated", {"status": "success"})
    except Exception as e:
        logger.warning(f"⚠️  Warning: Azure OpenAI configuration issue: {e}")
        log_agent_activity("Platform", "Azure OpenAI configuration warning", {"error": str(e)}, "warning")
    
    logger.info("✅ Application startup completed successfully")
    log_agent_activity("Platform", "Application startup completed", {"status": "ready"})


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Agentic AI Data Quality Platform",
        "version": "1.0.0",
        "status": "running",
        "available_endpoints": {
            "upload": "/upload",
            "jobs": "/jobs",
            "batch": "/batch",
            "job_details": "/jobs/{job_id}",
            "statistics": "/jobs/statistics"
        }
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check for the data quality platform"""
    from database import get_db_session
    from pathlib import Path
    
    # Test database connection
    try:
        with get_db_session() as db:
            db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Test Azure OpenAI configuration
    try:
        AgentConfig()
        agent_status = "configured"
    except Exception as e:
        agent_status = f"configuration_error: {str(e)}"
    
    # Check directories
    input_dir = Path(config.INPUT_DIRECTORY)
    output_dir = Path(config.OUTPUT_DIRECTORY)
    upload_dir = Path(config.UPLOADS_DIRECTORY)
    
    input_status = "accessible" if input_dir.exists() else "missing"
    output_status = "accessible" if output_dir.exists() else "missing"
    upload_status = "accessible" if upload_dir.exists() else "missing"
    
    return {
        "status": "healthy" if db_status == "healthy" and "configured" in agent_status else "degraded",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": db_status,
            "agents": agent_status,
            "input_directory": input_status,
            "output_directory": output_status,
            "upload_directory": upload_status
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=["./"]
    )
