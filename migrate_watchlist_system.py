#!/usr/bin/env python
"""
Database migration script for Hybrid Dynamic Watchlist System

This script:
1. Adds new columns to traders table (custom_watchlist, watchlist_size, use_custom_watchlist)
2. Creates new tables: api_usage_log, ticker_pool, ticker_rotation
3. Seeds initial ticker pool data from S&P 500, FTSE 100, and Nikkei 225

Usage:
    python migrate_watchlist_system.py
"""

import os
import sys
from datetime import date
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()


def migrate_database():
    """Run database migrations for watchlist system"""
    print("🚀 Starting Hybrid Watchlist System migration...")

    # Import app and database
    try:
        from app import app, db
        from models import ApiUsageLog, TickerPool, TickerRotation, Trader
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
            print("\n=== Phase 1: Updating Traders Table ===")

            # Check if custom_watchlist column exists
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='traders' AND column_name='custom_watchlist'
            """))

            if result.fetchone() is None:
                print("➕ Adding custom_watchlist column to traders table...")
                db.session.execute(text("""
                    ALTER TABLE traders
                    ADD COLUMN custom_watchlist JSON
                """))
                db.session.commit()
                print("✅ Added custom_watchlist column successfully!")
            else:
                print("✓ custom_watchlist column already exists")

            # Check if watchlist_size column exists
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='traders' AND column_name='watchlist_size'
            """))

            if result.fetchone() is None:
                print("➕ Adding watchlist_size column to traders table...")
                db.session.execute(text("""
                    ALTER TABLE traders
                    ADD COLUMN watchlist_size INTEGER NOT NULL DEFAULT 6
                """))
                db.session.commit()
                print("✅ Added watchlist_size column successfully!")
            else:
                print("✓ watchlist_size column already exists")

            # Check if use_custom_watchlist column exists
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='traders' AND column_name='use_custom_watchlist'
            """))

            if result.fetchone() is None:
                print("➕ Adding use_custom_watchlist column to traders table...")
                db.session.execute(text("""
                    ALTER TABLE traders
                    ADD COLUMN use_custom_watchlist BOOLEAN NOT NULL DEFAULT FALSE
                """))
                db.session.commit()
                print("✅ Added use_custom_watchlist column successfully!")
            else:
                print("✓ use_custom_watchlist column already exists")

            print("\n=== Phase 2: Creating New Tables ===")

            # Create all new tables (will skip if they already exist)
            db.create_all()
            print("✅ Created new tables (api_usage_log, ticker_pool, ticker_rotation)")

            print("\n=== Phase 3: Seeding Initial Ticker Pool Data ===")

            # Check if ticker_pool already has data
            existing_count = TickerPool.query.count()
            if existing_count > 0:
                print(f"✓ Ticker pool already has {existing_count} entries, skipping seed")
            else:
                print("📦 Seeding ticker pool with initial data...")
                seed_ticker_pools(db)

            # Initialize API usage log for today
            print("\n=== Phase 4: Initializing API Usage Tracking ===")
            today = date.today()
            existing_log = ApiUsageLog.query.filter_by(date=today).first()
            if not existing_log:
                api_log = ApiUsageLog(date=today, call_count=0)
                db.session.add(api_log)
                db.session.commit()
                print(f"✅ Initialized API usage log for {today}")
            else:
                print(f"✓ API usage log already exists for {today} ({existing_log.call_count} calls)")

            print("\n🎉 Migration complete!")
            print("\n📊 Database Summary:")
            print(f"   - Traders: {Trader.query.count()}")
            print(f"   - Ticker Pool: {TickerPool.query.count()}")
            print(f"   - Ticker Rotation Records: {TickerRotation.query.count()}")
            print(f"   - API Usage Logs: {ApiUsageLog.query.count()}")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def seed_ticker_pools(db):
    """Seed ticker pool with initial data from major indices"""
    from models import TickerPool

    # S&P 500 - Top tech stocks (sample)
    sp500_tickers = [
        ('AAPL', 'Apple Inc.', 'Technology'),
        ('MSFT', 'Microsoft Corporation', 'Technology'),
        ('GOOGL', 'Alphabet Inc. Class A', 'Technology'),
        ('AMZN', 'Amazon.com Inc.', 'Consumer Cyclical'),
        ('NVDA', 'NVIDIA Corporation', 'Technology'),
        ('META', 'Meta Platforms Inc.', 'Technology'),
        ('TSLA', 'Tesla Inc.', 'Automotive'),
        ('BRK.B', 'Berkshire Hathaway Inc.', 'Financial Services'),
        ('JPM', 'JPMorgan Chase & Co.', 'Financial Services'),
        ('V', 'Visa Inc.', 'Financial Services'),
        ('JNJ', 'Johnson & Johnson', 'Healthcare'),
        ('WMT', 'Walmart Inc.', 'Consumer Defensive'),
        ('PG', 'Procter & Gamble Co.', 'Consumer Defensive'),
        ('MA', 'Mastercard Incorporated', 'Financial Services'),
        ('HD', 'Home Depot Inc.', 'Consumer Cyclical'),
        ('DIS', 'The Walt Disney Company', 'Communication Services'),
        ('NFLX', 'Netflix Inc.', 'Communication Services'),
        ('BAC', 'Bank of America Corporation', 'Financial Services'),
        ('ADBE', 'Adobe Inc.', 'Technology'),
        ('CRM', 'Salesforce Inc.', 'Technology'),
    ]

    # FTSE 100 - Top UK stocks (sample)
    ftse100_tickers = [
        ('BARC.L', 'Barclays PLC', 'Financial Services'),
        ('HSBA.L', 'HSBC Holdings plc', 'Financial Services'),
        ('BP.L', 'BP plc', 'Energy'),
        ('SHEL.L', 'Shell plc', 'Energy'),
        ('VOD.L', 'Vodafone Group Plc', 'Communication Services'),
        ('GSK.L', 'GSK plc', 'Healthcare'),
        ('AZN.L', 'AstraZeneca PLC', 'Healthcare'),
        ('ULVR.L', 'Unilever PLC', 'Consumer Defensive'),
        ('DGE.L', 'Diageo plc', 'Consumer Defensive'),
        ('LLOY.L', 'Lloyds Banking Group plc', 'Financial Services'),
    ]

    # Nikkei 225 - Top Japanese stocks (sample)
    nikkei225_tickers = [
        ('7203.T', 'Toyota Motor Corporation', 'Automotive'),
        ('6758.T', 'Sony Group Corporation', 'Technology'),
        ('9984.T', 'SoftBank Group Corp.', 'Technology'),
        ('8306.T', 'Mitsubishi UFJ Financial Group', 'Financial Services'),
        ('9432.T', 'Nippon Telegraph and Telephone', 'Communication Services'),
        ('6861.T', 'Keyence Corporation', 'Technology'),
        ('6501.T', 'Hitachi Ltd.', 'Technology'),
        ('8035.T', 'Tokyo Electron Limited', 'Technology'),
        ('4502.T', 'Takeda Pharmaceutical Company', 'Healthcare'),
        ('4503.T', 'Astellas Pharma Inc.', 'Healthcare'),
    ]

    # Add S&P 500 tickers
    for ticker, name, sector in sp500_tickers:
        entry = TickerPool(
            ticker=ticker,
            name=name,
            exchange='NYSE/NASDAQ',
            timezone='America/New_York',
            sector=sector,
            source='sp500',
            is_active=True
        )
        db.session.add(entry)

    # Add FTSE 100 tickers
    for ticker, name, sector in ftse100_tickers:
        entry = TickerPool(
            ticker=ticker,
            name=name,
            exchange='LSE',
            timezone='Europe/London',
            sector=sector,
            source='ftse100',
            is_active=True
        )
        db.session.add(entry)

    # Add Nikkei 225 tickers
    for ticker, name, sector in nikkei225_tickers:
        entry = TickerPool(
            ticker=ticker,
            name=name,
            exchange='TSE',
            timezone='Asia/Tokyo',
            sector=sector,
            source='nikkei225',
            is_active=True
        )
        db.session.add(entry)

    db.session.commit()
    print(f"✅ Seeded {len(sp500_tickers) + len(ftse100_tickers) + len(nikkei225_tickers)} tickers into ticker_pool")


if __name__ == '__main__':
    migrate_database()
