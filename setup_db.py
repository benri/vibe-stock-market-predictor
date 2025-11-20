#!/usr/bin/env python
"""
Database setup script for Vibe Stock Market Predictor

This script initializes the database and creates all necessary tables.
Run this script after setting up your DATABASE_URL environment variable.

Usage:
    python setup_db.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Initialize database and create all tables"""
    print("🔧 Setting up database...")

    # Import app and database
    try:
        from app import app, db
        from models import Trader, Trade, Portfolio, TraderStatus, TradeAction
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)

    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable is not set!")
        print("Please set DATABASE_URL in your .env file or environment")
        print("Example: DATABASE_URL=postgresql://localhost/vibe_stock_predictor")
        sys.exit(1)

    print(f"📊 Using database: {database_url.split('@')[-1] if '@' in database_url else database_url}")

    # Create all tables
    try:
        with app.app_context():
            print("🏗️  Creating database tables...")
            db.create_all()
            print("✅ Database tables created successfully!")

            # Check if any traders exist
            trader_count = Trader.query.count()
            print(f"📈 Current traders in database: {trader_count}")

            if trader_count == 0:
                print("\n💡 Tip: Create your first trader using the web interface!")
                print("   Or use the API: POST /api/traders")

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Verify the database exists (createdb vibe_stock_predictor)")
        print("3. Check your DATABASE_URL is correct")
        sys.exit(1)

    print("\n🎉 Database setup complete!")
    print("\nNext steps:")
    print("1. Start the web server: python app.py")
    print("2. Start the Celery worker: celery -A celery_app worker --loglevel=info")
    print("3. Start the Celery beat: celery -A celery_app beat --loglevel=info")
    print("4. Visit http://localhost:5000 in your browser")

if __name__ == '__main__':
    setup_database()
