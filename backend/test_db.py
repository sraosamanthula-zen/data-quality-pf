"""
Simple test to verify database models are working correctly
"""

from app.db import init_db, SessionLocal, JobRecord
from datetime import datetime


def test_database_models():
    """Test basic database operations"""
    print("🔄 Testing database models...")

    # Initialize database
    init_db()

    # Test creating a job record
    with SessionLocal() as db:
        try:
            # Create a test job
            test_job = JobRecord(
                filename="test.csv",
                file_path="/test/path.csv",
                job_type="UC1",
                status="pending",
            )

            db.add(test_job)
            db.commit()
            db.refresh(test_job)

            print(f"✅ Created job with ID: {test_job.id}")

            # Test querying
            jobs = db.query(JobRecord).all()
            print(f"✅ Found {len(jobs)} jobs in database")

            # Test updating
            test_job.status = "completed"
            test_job.completed_at = datetime.utcnow()
            db.commit()

            print(f"✅ Updated job status to: {test_job.status}")

            # Cleanup
            db.delete(test_job)
            db.commit()

            print("✅ Database models working correctly!")
            return True

        except Exception as e:
            print(f"❌ Database test failed: {e}")
            return False


if __name__ == "__main__":
    test_database_models()
