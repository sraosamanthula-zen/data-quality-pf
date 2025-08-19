"""
Database migration script to add missing columns to existing database
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add missing columns to existing database"""
    db_path = "data_quality_platform.db"
    
    if not os.path.exists(db_path):
        print("Database doesn't exist, it will be created with full schema")
        return
    
    print(f"🔄 Starting database migration: {datetime.now()}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("PRAGMA table_info(jobs)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Current columns: {existing_columns}")
        
        # Define missing columns to add
        missing_columns = [
            ("selected_ucs", "VARCHAR"),
            ("is_reference", "BOOLEAN DEFAULT FALSE"),
            ("reference_file_id", "INTEGER"),
            ("reference_file_path", "VARCHAR"),
            ("sparse_compared_to_reference", "BOOLEAN"),
            ("results", "TEXT"),  # Alternative to results_json
            ("result_file_path", "VARCHAR")
        ]
        
        # Add missing columns
        for column_name, column_type in missing_columns:
            if column_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE jobs ADD COLUMN {column_name} {column_type}"
                    cursor.execute(alter_sql)
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    print(f"⚠️  Failed to add column {column_name}: {e}")
        
        # Check if file_processing_metrics table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_processing_metrics'")
        if not cursor.fetchone():
            print("📊 Creating file_processing_metrics table...")
            cursor.execute("""
                CREATE TABLE file_processing_metrics (
                    id INTEGER PRIMARY KEY,
                    job_id INTEGER NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    total_rows INTEGER,
                    total_columns INTEGER,
                    processing_time_ms INTEGER,
                    processing_time_seconds REAL,
                    agent_execution_time_ms INTEGER,
                    issues_found INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created file_processing_metrics table")
        
        # Check if agent_activity table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_activity'")
        if not cursor.fetchone():
            print("🤖 Creating agent_activity table...")
            cursor.execute("""
                CREATE TABLE agent_activity (
                    id INTEGER PRIMARY KEY,
                    job_id INTEGER,
                    agent_name VARCHAR NOT NULL,
                    activity_type VARCHAR NOT NULL,
                    activity_details TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created agent_activity table")
        
        conn.commit()
        
        # Verify final schema
        cursor.execute("PRAGMA table_info(jobs)")
        final_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Final columns: {final_columns}")
        
        print(f"✅ Database migration completed successfully: {datetime.now()}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
