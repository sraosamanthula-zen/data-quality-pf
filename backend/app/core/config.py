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

    # Directories
    upload_dir: Path = Path("./uploads")
    output_dir: Path = Path("./outputs")

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

    # Processing
    max_concurrent_jobs: int = 5

    # File processing
    max_file_size_mb: int = 100
    allowed_file_extensions: List[str] = [".csv", ".xlsx", ".xls"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
