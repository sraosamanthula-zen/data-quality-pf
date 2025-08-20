"""
Base configuration and utilities for all Agno agents in the Data Quality Platform
"""

# Standard library imports
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Third-party imports
from agno.models.azure import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Configure detailed logging
def setup_logging():
    """Setup comprehensive logging for the platform"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create formatters
    detailed_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s"
    )

    simple_formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler with colored output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)

    # File handler for all logs
    file_handler = logging.FileHandler(log_dir / "data_quality_platform.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Separate handler for agent activities
    agent_handler = logging.FileHandler(log_dir / "agent_activities.log")
    agent_handler.setLevel(logging.INFO)
    agent_handler.setFormatter(detailed_formatter)

    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Create agent-specific logger
    agent_logger = logging.getLogger("agents")
    agent_logger.addHandler(agent_handler)

    return root_logger


# Initialize logging
logger = setup_logging()


class AgentConfig:
    """Configuration manager for Azure OpenAI models and agent settings"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AgentConfig")

        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_version = os.getenv(
            "AZURE_OPENAI_API_VERSION", "2023-12-01-preview"
        )
        self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

        # Data processing configuration
        self.storage_directory = os.getenv("STORAGE_DIRECTORY", "./storage")
        self.uc4_output_directory = os.getenv(
            "UC4_OUTPUT_DIRECTORY", self.storage_directory
        )
        self.uc4_output_suffix = os.getenv("UC4_OUTPUT_SUFFIX", "_processed")
        self.uc1_output_directory = os.getenv(
            "UC1_OUTPUT_DIRECTORY", self.storage_directory
        )
        self.uc1_output_suffix = os.getenv("UC1_OUTPUT_SUFFIX", "_uc1_completeness")

        if not all([self.azure_api_key, self.azure_endpoint]):
            self.logger.error(
                "Azure OpenAI credentials not found in environment variables"
            )
            raise ValueError(
                "Azure OpenAI credentials not found in environment variables"
            )

        self.logger.info(
            f"AgentConfig initialized with endpoint: {self.azure_endpoint}"
        )
        self.logger.debug(
            f"UC4 output config: directory={self.uc4_output_directory}, suffix={self.uc4_output_suffix}"
        )
        self.logger.debug(
            f"UC1 output config: directory={self.uc1_output_directory}, suffix={self.uc1_output_suffix}"
        )

    def get_azure_openai_model(self, temperature: float = 0.1) -> AzureOpenAI:
        """Get configured Azure OpenAI client"""
        self.logger.debug(
            f"Creating Azure OpenAI model with temperature: {temperature}"
        )
        return AzureOpenAI(
            id=self.azure_deployment,
            api_key=self.azure_api_key,
            azure_endpoint=self.azure_endpoint,
            api_version=self.azure_api_version,
        )

    def get_agent_storage(self, agent_name: str) -> str:
        """Get storage path for agent"""
        storage_path = f"./storage/{agent_name}"
        os.makedirs(storage_path, exist_ok=True)
        self.logger.debug(f"Created storage path for {agent_name}: {storage_path}")
        return storage_path


class BaseAgentResults:
    """Standard result structure for all agents"""

    @staticmethod
    def create_result(
        agent_name: str,
        file_path: str,
        start_time: datetime,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create standardized agent result"""
        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        base_result = {
            "agent_name": agent_name,
            "file_path": file_path,
            "analysis_timestamp": start_time.isoformat(),
            "execution_time_ms": int(execution_time),
            "success": success,
            "platform_version": "1.0.0",
        }

        if error:
            base_result["error"] = error

        base_result.update(kwargs)

        # Log the result creation
        logger = logging.getLogger("agents")
        if success:
            logger.info(
                f"[{agent_name}] Analysis completed successfully in {execution_time:.1f}ms"
            )
        else:
            logger.error(f"[{agent_name}] Analysis failed: {error}")

        return base_result


def log_agent_activity(
    agent_name: str, activity: str, details: Dict[str, Any] = None, level: str = "info"
):
    """Enhanced agent activity logging with multiple levels and database storage"""
    timestamp = datetime.now()
    details = details or {}

    # Create structured log entry
    log_entry = {
        "timestamp": timestamp.isoformat(),
        "agent_name": agent_name,
        "activity": activity,
        "details": details,
    }

    # Get agent logger
    agent_logger = logging.getLogger("agents")

    # Format message for console/file logging
    details_str = (
        json.dumps(details, indent=None, separators=(",", ":")) if details else ""
    )
    message = f"[{agent_name}] {activity}"
    if details_str:
        message += f" | {details_str}"

    # Log at appropriate level
    if level.lower() == "debug":
        agent_logger.debug(message)
    elif level.lower() == "warning":
        agent_logger.warning(message)
    elif level.lower() == "error":
        agent_logger.error(message)
    else:
        agent_logger.info(message)

    # Also store in database for API access
    try:
        store_agent_activity_in_db(agent_name, activity, details, timestamp)
    except Exception as e:
        agent_logger.warning(f"Failed to store activity in database: {e}")

    return log_entry


def store_agent_activity_in_db(
    agent_name: str, activity: str, details: Dict[str, Any], timestamp: datetime
):
    """Store agent activity in database for API access"""
    try:
        from app.db import SessionLocal, AgentActivityLog

        db = SessionLocal()
        try:
            # Extract job_id if present in details
            job_id = details.get("job_id") if details else None

            activity_log = AgentActivityLog(
                job_id=job_id,
                agent_name=agent_name,
                activity_type=activity,
                activity_details=json.dumps(details) if details else None,
                timestamp=timestamp,
            )

            db.add(activity_log)
            db.commit()
        finally:
            db.close()

    except ImportError:
        # Database not available yet, skip
        pass
    except Exception as e:
        # Log error but don't fail the main operation
        logging.getLogger("agents").warning(f"Failed to store activity in DB: {e}")


def log_processing_step(
    job_id: int, agent_name: str, step: str, details: Dict[str, Any] = None
):
    """Log processing steps with job context"""
    step_details = {"job_id": job_id, "step": step}
    if details:
        step_details.update(details)

    log_agent_activity(agent_name, f"Processing Step: {step}", step_details)


def log_performance_metrics(
    agent_name: str, operation: str, duration_ms: float, details: Dict[str, Any] = None
):
    """Log performance metrics for monitoring"""
    perf_details = {
        "operation": operation,
        "duration_ms": duration_ms,
        "performance_category": "slow"
        if duration_ms > 5000
        else "normal"
        if duration_ms > 1000
        else "fast",
    }
    if details:
        perf_details.update(details)

    level = "warning" if duration_ms > 10000 else "info"
    log_agent_activity(agent_name, f"Performance: {operation}", perf_details, level)


def log_agent_error(
    agent_name: str, operation: str, error: Exception, context: Dict[str, Any] = None
):
    """Log agent errors with full context"""
    error_details = {
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {},
    }

    log_agent_activity(agent_name, f"Error: {operation}", error_details, "error")
