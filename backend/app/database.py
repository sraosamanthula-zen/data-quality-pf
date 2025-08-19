from sqlalchemy import create_engine

# Database configuration
SQLITE_DATABASE_URL = "sqlite:///./data_quality_platform.db"

engine = create_engine(
    SQLITE_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Will be configured after installing dependencies
SessionLocal = None
