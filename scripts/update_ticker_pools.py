#!/usr/bin/env python
"""
Ticker Pool Update Script

Manually updates the ticker pool from external sources (Wikipedia).
Can be run periodically via cron job or GitHub Actions.

Usage:
    python scripts/update_ticker_pools.py
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()


def main():
    """Update ticker pools from external sources"""
    print("🔄 Ticker Pool Update Script")
    print("=" * 50)

    # Import app and services
    try:
        from app import app
        from models import db
        from src.services.ticker_source_service import TickerSourceService
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        sys.exit(1)

    # Check if DATABASE_URL is set
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable is not set!")
        sys.exit(1)

    print(f"📊 Using database: {database_url.split('@')[-1] if '@' in database_url else database_url}\n")

    with app.app_context():
        # Get current stats before update
        print("📈 Current Ticker Pool Stats:")
        stats_before = TickerSourceService.get_ticker_pool_stats(db)
        print(f"   Total tickers: {stats_before.get('total_tickers', 0)}")
        print(f"   Active tickers: {stats_before.get('active_tickers', 0)}")
        print(f"   By exchange: {stats_before.get('by_exchange', {})}")
        print()

        # Refresh ticker pools
        print("🔄 Refreshing ticker pools from external sources...")
        results = TickerSourceService.refresh_ticker_pools(db)

        print("\n📊 Refresh Results:")
        print(f"   S&P 500 (US): {results.get('sp500', 0)} new tickers")
        print(f"   FTSE 100 (UK): {results.get('ftse100', 0)} new tickers")
        print(f"   Nikkei 225 (Japan): {results.get('nikkei225', 0)} new tickers")

        if results.get('errors'):
            print("\n⚠️  Errors encountered:")
            for error in results['errors']:
                print(f"   - {error}")

        # Get updated stats
        print("\n📈 Updated Ticker Pool Stats:")
        stats_after = TickerSourceService.get_ticker_pool_stats(db)
        print(f"   Total tickers: {stats_after.get('total_tickers', 0)}")
        print(f"   Active tickers: {stats_after.get('active_tickers', 0)}")
        print(f"   By exchange: {stats_after.get('by_exchange', {})}")

        total_new = sum([results.get('sp500', 0), results.get('ftse100', 0), results.get('nikkei225', 0)])
        print(f"\n✅ Update complete! Added {total_new} new tickers to the pool.")


if __name__ == '__main__':
    main()
