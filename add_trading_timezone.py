#!/usr/bin/env python
"""
Migration script to add trading_timezone column to traders table

Usage:
    python add_trading_timezone.py
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

def add_trading_timezone_column():
    """Add trading_timezone column to traders table"""
    print("🔄 Adding trading_timezone column to traders table...")

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
            # Check if trading_timezone column exists
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='traders' AND column_name='trading_timezone'
            """))

            if result.fetchone() is None:
                print("➕ Adding trading_timezone column...")
                db.session.execute(text("""
                    ALTER TABLE traders
                    ADD COLUMN trading_timezone VARCHAR(50) DEFAULT 'America/New_York' NOT NULL
                """))
                db.session.commit()
                print("✅ Added trading_timezone column successfully!")
            else:
                print("✓ trading_timezone column already exists")

            print("\n🎉 Migration complete!")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    add_trading_timezone_column()
