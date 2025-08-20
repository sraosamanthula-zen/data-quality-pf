"""
Database migration utilities
"""

from sqlalchemy import text
from .base import engine, SessionLocal
from .models import Base


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully")


def drop_tables():
    """Drop all tables (use with caution)"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All tables dropped")


def reset_database():
    """Reset the entire database"""
    drop_tables()
    create_tables()
    print("🔄 Database reset completed")


def check_database():
    """Check database connection and tables"""
    try:
        with SessionLocal() as db:
            # Test connection
            db.execute(text("SELECT 1"))

            # Check tables exist
            result = db.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Available tables: {tables}")

        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    print("🔄 Running database migrations...")
    create_tables()
    check_database()
