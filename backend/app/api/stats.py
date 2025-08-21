"""
Statistics API endpoints
"""

# Standard library imports
import logging

# Third-party imports
from fastapi import APIRouter
from sqlalchemy.sql import func

# Local application imports
from app.db import get_db_session, JobRecord
from app.schemas import JobStatistics
from app.core.config import settings

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["statistics"])


@router.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Agentic AI Data Quality Platform",
        "version": "1.0.0",
        "status": "running",
        "available_endpoints": {
            "upload": "/upload",
            "jobs": "/jobs",
            "batch": "/batch",
            "statistics": "/stats",
            "health": "/stats/health",
        },
    }


@router.get("/statistics", response_model=JobStatistics)
async def get_statistics():
    """Get job statistics for the dashboard"""
    with get_db_session() as db:
        try:
            total_jobs = db.query(JobRecord).count()

            # Include 'uploaded', 'pending', and 'queued' as pending jobs
            pending_statuses = ["uploaded", "pending", "queued"]
            pending_jobs = (
                db.query(JobRecord)
                .filter(JobRecord.status.in_(pending_statuses))
                .count()
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
                db.query(JobRecord)
                .filter(JobRecord.status.in_(processing_statuses))
                .count()
            )

            completed_jobs = (
                db.query(JobRecord).filter(JobRecord.status == "completed").count()
            )
            failed_jobs = (
                db.query(JobRecord).filter(JobRecord.status == "failed").count()
            )

            # Calculate average quality score
            avg_quality = (
                db.query(func.avg(JobRecord.quality_score))
                .filter(JobRecord.quality_score.isnot(None))
                .scalar()
            )

            return JobStatistics(
                total_jobs=total_jobs,
                pending_jobs=pending_jobs,
                processing_jobs=processing_jobs,
                completed_jobs=completed_jobs,
                failed_jobs=failed_jobs,
                average_quality_score=float(avg_quality) if avg_quality else None,
            )
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise


@router.get("/config")
async def get_app_config():
    """Get application configuration"""

    return {
        "data_directory": str(settings.inputs_dir.resolve()),
        "storage_directory": str(settings.outputs_dir.resolve()),
        "uploads_directory": str(settings.uploads_dir.resolve()),
        "reference_files_directory": str(settings.uploads_dir.resolve()),
        "result_suffix": "_processed",
        "batch_processing_enabled": True,
        "max_concurrent_jobs": settings.max_concurrent_jobs,
        "allowed_file_extensions": settings.allowed_file_extensions,
        "max_file_size_mb": settings.max_file_size_mb,
        "temp_directory": str(settings.temp_dir.resolve()),
    }


# @router.get("/health")
# async def health_check():
#     """Comprehensive health check for the data quality platform"""
#     from app.db import get_db_session
#     from sqlalchemy import text

#     # Test database connection
#     try:
#         with get_db_session() as db:
#             db.execute(text("SELECT 1"))
#         db_status = "healthy"
#     except Exception as e:
#         db_status = f"unhealthy: {str(e)}"

#     # Test upload directory
#     from app.core.config import settings

#     upload_dir_status = (
#         "accessible" if settings.uploads_dir.exists() else "not accessible"
#     )
#     output_dir_status = (
#         "accessible" if settings.outputs_dir.exists() else "not accessible"
#     )

#     return {
#         "status": "healthy" if db_status == "healthy" else "unhealthy",
#         "database": db_status,
#         "upload_directory": upload_dir_status,
#         "output_directory": output_dir_status,
#         "timestamp": "2025-08-20T00:00:00Z",
#     }
