"""
Clear all jobs from the database
"""

# Standard library imports
import sys

# Add the backend directory to Python path
sys.path.append('/home/sraosamanthula/ZENLABS/RCL_Files/Platform/backend')

# Local application imports
from database import get_db_session, JobRecord, FileProcessingMetrics, AgentActivityLog


def clear_all_jobs():
    """Clear all job records, processing metrics, and activity logs from the database"""
    
    with get_db_session() as db:
        try:
            # Count existing records
            job_count = db.query(JobRecord).count()
            metrics_count = db.query(FileProcessingMetrics).count()
            activity_count = db.query(AgentActivityLog).count()
            
            print("📊 Current database state:")
            print(f"   Jobs: {job_count}")
            print(f"   Metrics: {metrics_count}")
            print(f"   Activity Logs: {activity_count}")
            
            if job_count == 0 and metrics_count == 0 and activity_count == 0:
                print("✅ Database is already clean - no jobs to clear")
                return
            
            print("\n🗑️  Clearing all jobs, metrics, and activity logs...")
            
            # Delete all activity logs first
            deleted_activities = db.query(AgentActivityLog).delete()
            print(f"   Deleted {deleted_activities} activity log entries")
            
            # Delete all processing metrics (due to foreign key constraints)
            deleted_metrics = db.query(FileProcessingMetrics).delete()
            print(f"   Deleted {deleted_metrics} processing metrics")
            
            # Delete all job records
            deleted_jobs = db.query(JobRecord).delete()
            print(f"   Deleted {deleted_jobs} job records")
            
            print("✅ All jobs, metrics, and activity logs cleared successfully!")
            
            # Verify cleanup
            remaining_jobs = db.query(JobRecord).count()
            remaining_metrics = db.query(FileProcessingMetrics).count()
            remaining_activities = db.query(AgentActivityLog).count()
            
            print("\n📊 After cleanup:")
            print(f"   Jobs: {remaining_jobs}")
            print(f"   Metrics: {remaining_metrics}")
            print(f"   Activity Logs: {remaining_activities}")
            
        except Exception as e:
            print(f"❌ Error clearing jobs: {e}")
            raise


if __name__ == "__main__":
    clear_all_jobs()
