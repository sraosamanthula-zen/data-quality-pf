#!/usr/bin/env python3
"""
Simple script to clear jobs from SQLite database without dependencies
"""

import sqlite3
import os

def clear_all_jobs():
    """Clear all job records, processing metrics, and activity logs from the SQLite database"""
    
    # Database path
    db_path = "data_quality_platform.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path, timeout=30)
        cursor = conn.cursor()
        
        # Count existing records
        cursor.execute("SELECT COUNT(*) FROM jobs")
        job_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM file_processing_metrics")
        metrics_count = cursor.fetchone()[0]
        
        try:
            cursor.execute("SELECT COUNT(*) FROM agent_activity")
            activity_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            activity_count = 0  # Table might not exist
        
        print("📊 Current database state:")
        print(f"   Jobs: {job_count}")
        print(f"   Metrics: {metrics_count}")
        print(f"   Activity Logs: {activity_count}")
        
        if job_count == 0 and metrics_count == 0 and activity_count == 0:
            print("✅ Database is already clean - no jobs to clear")
            conn.close()
            return
        
        print("\n🗑️  Clearing all jobs, metrics, and activity logs...")
        
        # Delete all activity logs first (if table exists)
        try:
            cursor.execute("DELETE FROM agent_activity")
            deleted_activities = cursor.rowcount
            print(f"   Deleted {deleted_activities} activity log entries")
        except sqlite3.OperationalError:
            print("   Activity logs table not found, skipping...")
        
        # Delete all processing metrics (due to foreign key constraints)
        cursor.execute("DELETE FROM file_processing_metrics")
        deleted_metrics = cursor.rowcount
        print(f"   Deleted {deleted_metrics} processing metrics")
        
        # Delete all job records
        cursor.execute("DELETE FROM jobs")
        deleted_jobs = cursor.rowcount
        print(f"   Deleted {deleted_jobs} job records")
        
        # Commit changes
        conn.commit()
        
        print("✅ All jobs, metrics, and activity logs cleared successfully!")
        
        # Verify cleanup
        cursor.execute("SELECT COUNT(*) FROM jobs")
        remaining_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM file_processing_metrics")
        remaining_metrics = cursor.fetchone()[0]
        
        try:
            cursor.execute("SELECT COUNT(*) FROM agent_activity")
            remaining_activities = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            remaining_activities = 0
        
        print("\n📊 After cleanup:")
        print(f"   Jobs: {remaining_jobs}")
        print(f"   Metrics: {remaining_metrics}")
        print(f"   Activity Logs: {remaining_activities}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error clearing jobs: {e}")
        if 'conn' in locals():
            conn.close()
        raise


if __name__ == "__main__":
    clear_all_jobs()
