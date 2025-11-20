#!/usr/bin/env python
"""
Database migration script for Vibe Stock Market Predictor

This script handles adding new columns to existing tables without
dropping and recreating them.

Usage:
    python migrate_db.py
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

def migrate_database():
    """Run database migrations to add missing columns"""
    print("🔄 Running database migrations...")

    # Import app and database
    try:
        from app import app, db
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        sys.exit(1)

    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable is not set!")
        sys.exit(1)

    print(f"📊 Using database: {database_url.split('@')[-1] if '@' in database_url else database_url}")

    try:
        with app.app_context():
            # Check if trading_ethos column exists
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='traders' AND column_name='trading_ethos'
            """))

            if result.fetchone() is None:
                print("➕ Adding trading_ethos column to traders table...")
                db.session.execute(text("""
                    ALTER TABLE traders
                    ADD COLUMN trading_ethos TEXT
                """))
                db.session.commit()
                print("✅ Added trading_ethos column successfully!")
            else:
                print("✓ trading_ethos column already exists")

            print("\n🎉 Database migration complete!")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    migrate_database()
