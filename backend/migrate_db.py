"""
Database migration script to add missing columns to jobs table
"""

import sqlite3
from pathlib import Path


def migrate_database():
    """Add missing columns to the jobs table"""
    
    # Path to the database file
    db_path = Path("data_quality_platform.db")
    
    if not db_path.exists():
        print("❌ Database file not found!")
        return False
        
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check current schema
        cursor.execute("PRAGMA table_info(jobs)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Existing columns: {existing_columns}")
        
        # Define missing columns to add
        missing_columns = {
            'use_case': 'VARCHAR',
            'inputs_folder': 'VARCHAR', 
            'outputs_folder': 'VARCHAR',
            'temp_folder': 'VARCHAR'
        }
        
        # Add missing columns
        columns_added = []
        for column_name, column_type in missing_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE jobs ADD COLUMN {column_name} {column_type}")
                    columns_added.append(column_name)
                    print(f"✅ Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"⚠️  Column {column_name} already exists")
                    else:
                        print(f"❌ Error adding column {column_name}: {e}")
            else:
                print(f"⚠️  Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify the new schema
        cursor.execute("PRAGMA table_info(jobs)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Updated columns: {new_columns}")
        
        conn.close()
        
        if columns_added:
            print(f"✅ Migration completed! Added {len(columns_added)} columns: {columns_added}")
        else:
            print("✅ Migration completed! No columns needed to be added.")
            
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    migrate_database()
