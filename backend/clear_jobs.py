"""
Clear all jobs from the database
"""
import sys

# Add the backend directory to Python path
sys.path.append('/home/sraosamanthula/ZENLABS/RCL_Files/Platform/backend')

from database import SessionLocal, JobRecord, FileProcessingMetrics


def clear_all_jobs():
    """Clear all job records and processing metrics from the database"""
    db = SessionLocal()
    
    try:
        # Count existing records
        job_count = db.query(JobRecord).count()
        metrics_count = db.query(FileProcessingMetrics).count()
        
        print("📊 Current database state:")
        print(f"   Jobs: {job_count}")
        print(f"   Metrics: {metrics_count}")
        
        if job_count == 0 and metrics_count == 0:
            print("✅ Database is already clean - no jobs to clear")
            return
        
        print("\n🗑️  Clearing all jobs and metrics...")
        
        # Delete all processing metrics first (due to foreign key constraints)
        deleted_metrics = db.query(FileProcessingMetrics).delete()
        print(f"   Deleted {deleted_metrics} processing metrics")
        
        # Delete all job records
        deleted_jobs = db.query(JobRecord).delete()
        print(f"   Deleted {deleted_jobs} job records")
        
        # Commit the changes
        db.commit()
        
        print("✅ All jobs and metrics cleared successfully!")
        
        # Verify cleanup
        remaining_jobs = db.query(JobRecord).count()
        remaining_metrics = db.query(FileProcessingMetrics).count()
        
        print("\n📊 After cleanup:")
        print(f"   Jobs: {remaining_jobs}")
        print(f"   Metrics: {remaining_metrics}")
        
    except Exception as e:
        print(f"❌ Error clearing jobs: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_all_jobs()
