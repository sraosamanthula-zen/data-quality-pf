"""
Core application configuration and settings
"""

from pathlib import Path
from typing import List

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    data_dir: Path = Path("../data").absolute()

    @computed_field
    @property
    def inputs_dir(self) -> Path:
        dir = self.data_dir / "inputs"
        dir.mkdir(exist_ok=True, parents=True)
        return dir

    @computed_field
    @property
    def outputs_dir(self) -> Path:
        dir = self.data_dir / "outputs"
        dir.mkdir(exist_ok=True, parents=True)
        return dir

    @computed_field
    @property
    def temp_dir(self) -> Path:
        dir = self.data_dir / "temp"
        dir.mkdir(exist_ok=True, parents=True)
        return dir

    @computed_field
    @property
    def uploads_dir(self) -> Path:
        dir = self.data_dir / "uploads"
        dir.mkdir(exist_ok=True, parents=True)
        return dir
    
    @computed_field
    @property
    def logs_dir(self) -> Path:
        dir = self.data_dir / "logs"
        dir.mkdir(exist_ok=True, parents=True)
        return dir

    # Database
    database_url: str = "sqlite:///../data/data_quality_platform.db"

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
