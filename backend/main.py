"""
Agentic AI Data Quality Platform - FastAPI Backend

This FastAPI application provides endpoints for UC1 (Sparse Data Detection) and UC4 (Duplicate Detection)
using the Agno framework with Azure OpenAI for comprehensive data quality analysis.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import init_db
from routes import jobs, upload, batch
from agents.base_config import AgentConfig, log_agent_activity

# Load environment variables
load_dotenv()

# Initialize logging first
logger = logging.getLogger(__name__)

# Configuration from environment variables
class Config:
    DATA_DIRECTORY = os.getenv("DATA_DIRECTORY", "/home/sraosamanthula/ZENLABS/RCL_Files")
    UPLOADS_DIRECTORY = os.getenv("UPLOADS_DIRECTORY", "./uploads")
    REFERENCE_FILES_DIRECTORY = os.getenv("REFERENCE_FILES_DIRECTORY", "./reference_files")
    STORAGE_DIRECTORY = os.getenv("STORAGE_DIRECTORY", "./storage")
    RESULT_SUFFIX = os.getenv("RESULT_SUFFIX", "_processed")
    BATCH_PROCESSING = os.getenv("BATCH_PROCESSING", "true").lower() == "true"
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.UPLOADS_DIRECTORY,
            cls.REFERENCE_FILES_DIRECTORY,
            cls.STORAGE_DIRECTORY
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            
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
    from database import SessionLocal
    from sqlalchemy.sql import func
    from database import JobRecord
    
    db = SessionLocal()
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
    finally:
        db.close()


@app.get("/config")
async def get_config():
    """Get platform configuration"""
    return {
        "data_directory": config.DATA_DIRECTORY,
        "uploads_directory": config.UPLOADS_DIRECTORY,
        "reference_files_directory": config.REFERENCE_FILES_DIRECTORY,
        "storage_directory": config.STORAGE_DIRECTORY,
        "result_suffix": config.RESULT_SUFFIX,
        "batch_processing_enabled": config.BATCH_PROCESSING
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
    from database import SessionLocal
    from pathlib import Path
    
    # Test database connection
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Test Azure OpenAI configuration
    try:
        AgentConfig()
        agent_status = "configured"
    except Exception as e:
        agent_status = f"configuration_error: {str(e)}"
    
    # Check upload directory
    upload_dir = Path("uploads")
    upload_status = "accessible" if upload_dir.exists() else "missing"
    
    return {
        "status": "healthy" if db_status == "healthy" and "configured" in agent_status else "degraded",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": db_status,
            "agents": agent_status,
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
