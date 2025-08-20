"""
Core application configuration and settings
"""

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Database
    database_url: str = "sqlite:///./data_quality_platform.db"

    # Directories - Main folders for job processing
    inputs_dir: Path = Path("../data/inputs")      # Contains sub-folders for each job input
    outputs_dir: Path = Path("../data/outputs")    # Contains sub-folders for each job's output
    uploads_dir: Path = Path("../data/uploads")    # Contains user reference files for use cases
    temp_dir: Path = Path("../data/temp")          # Contains intermediate processing results for jobs
    
    # Legacy directory names for backward compatibility
    upload_dir: Path = Path("../data/uploads")
    output_dir: Path = Path("../data/outputs")

    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    # AI/ML
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2023-12-01-preview"
    
    # Model configuration - configurable via environment
    agent_model: str = "gpt-4-turbo"
    agent_temperature: float = 0.1
    agent_max_tokens: int = 4000

    # Processing
    max_concurrent_jobs: int = 5
    max_prompt_rows: int = 10  # Hard limit for data rows in prompts

    # File processing
    max_file_size_mb: int = 100
    allowed_file_extensions: List[str] = [".csv", ".xlsx", ".xls"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()

# Ensure all required directories exist
settings.inputs_dir.mkdir(parents=True, exist_ok=True)
settings.outputs_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.temp_dir.mkdir(parents=True, exist_ok=True)

# Legacy compatibility
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
