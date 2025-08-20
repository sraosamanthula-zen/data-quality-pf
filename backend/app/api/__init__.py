"""
API routes
"""

from .jobs import router as jobs_router
from .upload import router as upload_router
from .batch import router as batch_router
from .stats import router as stats_router

__all__ = ["jobs_router", "upload_router", "batch_router", "stats_router"]
