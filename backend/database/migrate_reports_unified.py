#!/usr/bin/env python3
"""
Migration script to update the reports table structure:
- Remove report_type column
- Add sections column to store all report sections in one field
- Migrate existing data to new structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
import uuid
from datetime import datetime

# Import the database and models
# Note: Migration script - no longer needed with Repository pattern
import os

def migrate_reports_to_unified_structure():
    """
    Migrate existing reports from individual report_type records 
    to unified reports with sections field.
    """
    
    # Migration no longer needed with Repository pattern
    print("Migration script is deprecated - using Repository pattern now")
    return
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/tradingagents.db")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("🔄 Starting reports table migration...")
        
        # 1. First, let's check the current table structure
        result = session.execute(text("PRAGMA table_info(reports)"))
        columns = [row[1] for row in result.fetchall()]
        print(f"📋 Current columns: {columns}")
        
        # 2. Check if we already have the new structure
        if 'sections' in columns and 'report_type' not in columns:
            print("✅ Migration already completed!")
            return
        
        # 3. Get all existing reports grouped by analysis_id
        print("📊 Fetching existing reports...")
        result = session.execute(text("""
            SELECT analysis_id, ticker, user_id, report_type, title, content, status, created_at, updated_at
            FROM reports 
            ORDER BY analysis_id, report_type
        """))
        
        all_reports = result.fetchall()
        print(f"📄 Found {len(all_reports)} existing report records")
        
        # 4. Group reports by analysis_id
        analysis_groups = {}
        for report in all_reports:
            analysis_id = report[0]
            if analysis_id not in analysis_groups:
                analysis_groups[analysis_id] = {
                    'ticker': report[1],
                    'user_id': report[2],
                    'title': report[4] or f"{report[1]} Analysis Report",
                    'status': report[6],
                    'created_at': report[7],
                    'updated_at': report[8],
                    'sections': {}
                }
            
            # Add this report section
            report_type = report[3]
            content = report[5] if isinstance(report[5], str) else json.dumps(report[5])
            analysis_groups[analysis_id]['sections'][report_type] = content
        
        print(f"🔗 Grouped into {len(analysis_groups)} analysis reports")
        
        # 5. Create backup table
        print("💾 Creating backup table...")
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS reports_backup AS 
            SELECT * FROM reports
        """))
        
        # 6. Drop the old table and create new structure
        print("🗑️ Dropping old table...")
        session.execute(text("DROP TABLE reports"))
        
        print("🏗️ Creating new table structure...")
        session.execute(text("""
            CREATE TABLE reports (
                id TEXT PRIMARY KEY,
                report_id TEXT UNIQUE NOT NULL,
                analysis_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                ticker TEXT NOT NULL,
                title TEXT,
                sections JSON NOT NULL,
                status TEXT DEFAULT 'generated',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # 7. Create indexes (with IF NOT EXISTS for safety)
        print("📇 Creating indexes...")
        try:
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_analysis_id ON reports(analysis_id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_ticker ON reports(user_id, ticker)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_analysis_created ON reports(analysis_id, created_at)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_ticker_created ON reports(ticker, created_at)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_status ON reports(user_id, status)"))
        except Exception as index_error:
            print(f"⚠️ Index creation warning: {index_error}")
        
        # 8. Insert migrated data
        print("📥 Inserting migrated data...")
        for analysis_id, group_data in analysis_groups.items():
            report_id = f"report_{group_data['ticker']}_{analysis_id.split('_')[-1]}_{int(datetime.now().timestamp())}"
            
            # Only create unified report if we have at least one section
            if group_data['sections']:
                session.execute(text("""
                    INSERT INTO reports (
                        id, report_id, analysis_id, user_id, ticker, 
                        title, sections, status, created_at, updated_at
                    ) VALUES (
                        :id, :report_id, :analysis_id, :user_id, :ticker,
                        :title, :sections, :status, :created_at, :updated_at
                    )
                """), {
                    'id': str(uuid.uuid4()),
                    'report_id': report_id,
                    'analysis_id': analysis_id,
                    'user_id': group_data['user_id'],
                    'ticker': group_data['ticker'],
                    'title': group_data['title'],
                    'sections': json.dumps(group_data['sections']),
                    'status': group_data['status'],
                    'created_at': group_data['created_at'],
                    'updated_at': group_data['updated_at']
                })
        
        session.commit()
        print(f"✅ Migration completed! Created {len(analysis_groups)} unified reports")
        
        # 9. Verify the migration
        result = session.execute(text("SELECT COUNT(*) FROM reports"))
        new_count = result.fetchone()[0]
        print(f"📊 New table has {new_count} records")
        
        # Show sample of new structure
        result = session.execute(text("""
            SELECT report_id, ticker, JSON_KEYS(sections) as section_keys 
            FROM reports 
            LIMIT 3
        """))
        print("🔍 Sample of new structure:")
        for row in result.fetchall():
            print(f"   - {row[0]} ({row[1]}): sections = {row[2]}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate_reports_to_unified_structure()
