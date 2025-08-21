"""
Agentic AI Data Quality Platform - FastAPI Backend

This FastAPI application provides endpoints for UC1 (Sparse Data Detection) and UC4 (Duplicate Detection)
using the Agno framework with Azure OpenAI for comprehensive data quality analysis.
"""

# Standard library imports
import logging
from contextlib import asynccontextmanager

from app.api import batch_router, jobs_router, stats_router, upload_router
from app.api.websocket import router as websocket_router
from app.core.logging import setup_logging
from app.db import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize logging first
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Agentic AI Data Quality Platform...")

    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.exception("❌ Database initialization failed")
        raise RuntimeError("Database initialization failed.") from e

    yield


# async def recover_stuck_jobs(auto_restart: bool = False):
#     """
#     Recover jobs that were stuck in processing states when server was restarted.
#     Reset processing jobs to failed status to prevent automatic restart issues.

#     Args:
#         auto_restart: If True, will restart queued jobs. If False, just cleans up stuck jobs.
#     """
#     from app.db import get_db_session

#     with get_db_session() as db:
#         try:
#             # Define stuck statuses that need recovery
#             stuck_processing_statuses = [
#                 "processing",
#                 "processing_uc1",
#                 "processing_uc4",
#                 "analyzing_completeness",
#                 "detecting_duplicates",
#                 "cleaning_file",
#             ]

#             # Mark stuck processing jobs as failed instead of queuing them
#             stuck_jobs = (
#                 db.query(JobRecord)
#                 .filter(JobRecord.status.in_(stuck_processing_statuses))
#                 .all()
#             )

#             for job in stuck_jobs:
#                 previous_status = (
#                     job.status
#                 )  # Store the original status before changing
#                 logger.info(
#                     f"🔄 Marking stuck job {job.id} as failed: {job.filename} (was {previous_status})"
#                 )
#                 job.status = "failed"
#                 job.started_at = None
#                 job.completed_at = datetime.utcnow()
#                 job.error_message = (
#                     f"Job was stuck in {previous_status} state during server restart"
#                 )
#                 log_agent_activity(
#                     "JobRecovery",
#                     f"Marked stuck job {job.id} as failed",
#                     {
#                         "job_id": job.id,
#                         "filename": job.filename,
#                         "previous_status": previous_status,
#                     },
#                 )

#             # Check for jobs with missing files and mark them as failed
#             pending_jobs = (
#                 db.query(JobRecord)
#                 .filter(JobRecord.status.in_(["queued", "uploaded", "pending"]))
#                 .all()
#             )
#             failed_missing_files = []

#             for job in pending_jobs:
#                 if not os.path.exists(job.file_path):
#                     logger.warning(f"❌ Job {job.id} file not found: {job.file_path}")
#                     job.status = "failed"
#                     job.error_message = (
#                         f"File not found during recovery: {job.file_path}"
#                     )
#                     job.completed_at = datetime.utcnow()
#                     failed_missing_files.append(job)
#                     log_agent_activity(
#                         "JobRecovery",
#                         f"Job {job.id} marked as failed - file not found",
#                         {
#                             "job_id": job.id,
#                             "filename": job.filename,
#                             "file_path": job.file_path,
#                         },
#                     )

#             # Get remaining queued jobs after cleanup
#             remaining_queued = (
#                 db.query(JobRecord).filter(JobRecord.status == "queued").all()
#             )

#             logger.info(
#                 f"🔄 Job recovery summary: {len(stuck_jobs)} stuck jobs marked as failed, {len(failed_missing_files)} jobs with missing files failed, {len(remaining_queued)} jobs still queued"
#             )
#             log_agent_activity(
#                 "JobRecovery",
#                 "Job recovery completed",
#                 {
#                     "stuck_jobs_failed": len(stuck_jobs),
#                     "missing_file_jobs_failed": len(failed_missing_files),
#                     "remaining_queued_jobs": len(remaining_queued),
#                     "auto_restart_enabled": auto_restart,
#                 },
#             )

#             # Only restart queued jobs if explicitly requested
#             restart_count = 0
#             if auto_restart and remaining_queued:
#                 logger.info(
#                     f"🚀 Auto-restart enabled: restarting {len(remaining_queued)} queued jobs"
#                 )
#                 try:
#                     # Import here to avoid circular import
#                     from app.api.batch import restart_queued_jobs

#                     await restart_queued_jobs(remaining_queued)
#                     restart_count = len(remaining_queued)
#                 except Exception as restart_error:
#                     logger.error(f"❌ Failed to restart queued jobs: {restart_error}")
#                     log_agent_activity(
#                         "JobRecovery",
#                         "Auto-restart failed",
#                         {"error": str(restart_error)},
#                         "error",
#                     )
#             else:
#                 logger.info(
#                     f"ℹ️  Auto-restart disabled: {len(remaining_queued)} jobs remain queued (use manual restart if needed)"
#                 )

#             return {
#                 "stuck_jobs_failed": len(stuck_jobs),
#                 "missing_file_jobs_failed": len(failed_missing_files),
#                 "remaining_queued_jobs": len(remaining_queued),
#                 "restarted_jobs": restart_count,
#             }

#         except Exception as e:
#             logger.error(f"❌ Job recovery failed: {e}")
#             log_agent_activity(
#                 "JobRecovery", "Job recovery failed", {"error": str(e)}, "error"
#             )
#             raise


# async def start_background_job_recovery():
#     """
#     Start background job recovery service
#     """
#     try:
#         logger.info("🚀 Starting background job recovery service...")
#         log_agent_activity(
#             "JobRecovery",
#             "Background job recovery service started",
#             {"status": "active"},
#         )
#     except Exception as e:
#         logger.error(f"❌ Background job recovery service failed to start: {e}")
#         log_agent_activity(
#             "JobRecovery",
#             "Background job recovery service failed",
#             {"error": str(e)},
#             "error",
#         )


# FastAPI Application
app = FastAPI(
    title="Agentic AI Data Quality Platform",
    description="Advanced data quality analysis using UC1 (Sparse Data Detection) and UC4 (Duplicate Detection) agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs_router)
app.include_router(upload_router)
app.include_router(batch_router)
app.include_router(stats_router)
app.include_router(websocket_router)


# @app.on_event("startup")
# async def startup_event():
#     """Initialize the application and validate configuration"""
#     logger.info("🚀 Starting Agentic AI Data Quality Platform...")

#     # Initialize database
#     try:
#         init_db()
#         logger.info("✅ Database initialized successfully")
#     except Exception as e:
#         logger.exception("❌ Database initialization failed")
#         raise RuntimeError("Database initialization failed.") from e

#     # # Recover stuck jobs from previous session (but don't auto-restart)
#     # try:
#     #     recovery_result = await recover_stuck_jobs(
#     #         auto_restart=False
#     #     )  # Disable auto-restart to prevent stuck backend
#     #     logger.info(f"✅ Job recovery completed successfully: {recovery_result}")
#     #     log_agent_activity(
#     #         "Platform",
#     #         "Job recovery completed",
#     #         {
#     #             "status": "success",
#     #             "stuck_jobs_failed": recovery_result.get("stuck_jobs_failed", 0),
#     #             "missing_file_jobs_failed": recovery_result.get(
#     #                 "missing_file_jobs_failed", 0
#     #             ),
#     #             "remaining_queued_jobs": recovery_result.get(
#     #                 "remaining_queued_jobs", 0
#     #             ),
#     #             "auto_restart_enabled": False,
#     #         },
#     #     )
#     # except Exception as e:
#     #     logger.error(f"❌ Job recovery failed: {e}")
#     #     log_agent_activity(
#     #         "Platform", "Job recovery failed", {"error": str(e)}, "error"
#     #     )
#     #     # Don't raise here - we want the server to start even if recovery fails

#     # # Start background job recovery service
#     # try:
#     #     await start_background_job_recovery()
#     #     logger.info("✅ Background job recovery service started")
#     #     log_agent_activity(
#     #         "Platform", "Background job recovery service started", {"status": "active"}
#     #     )
#     # except Exception as e:
#     #     logger.error(f"❌ Background job recovery service failed: {e}")
#     #     log_agent_activity(
#     #         "Platform",
#     #         "Background job recovery service failed",
#     #         {"error": str(e)},
#     #         "error",
#     #     )

#     # # Validate Azure OpenAI configuration
#     # try:
#     #     AgentConfig()
#     #     logger.info("✅ Azure OpenAI configuration validated")
#     #     log_agent_activity(
#     #         "Platform", "Azure OpenAI configuration validated", {"status": "success"}
#     #     )
#     # except Exception as e:
#     #     logger.warning(f"⚠️  Warning: Azure OpenAI configuration issue: {e}")
#     #     log_agent_activity(
#     #         "Platform",
#     #         "Azure OpenAI configuration warning",
#     #         {"error": str(e)},
#     #         "warning",
#     #     )

#     # logger.info("✅ Application startup completed successfully")
#     # log_agent_activity("Platform", "Application startup completed", {"status": "ready"})
