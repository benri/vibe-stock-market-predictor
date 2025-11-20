#!/usr/bin/env python
"""
Reset database to clean state with fresh traders

This script:
1. Deletes all trades, portfolio items, and ticker prices
2. Resets trader balances to initial amounts
3. Can also recreate traders from scratch
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def reset_database(recreate_traders=False):
    """Reset database to clean state"""
    print("🔄 Resetting database...")

    # Import app and models
    try:
        from app import app, db
        from models import Trader, Trade, Portfolio, TickerPrice, TraderStatus
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        sys.exit(1)

    with app.app_context():
        try:
            # Delete all trades, portfolio items, and ticker prices
            print("\n📊 Current state:")
            print(f"   - Trades: {Trade.query.count()}")
            print(f"   - Portfolio items: {Portfolio.query.count()}")
            print(f"   - Ticker prices: {TickerPrice.query.count()}")
            print(f"   - Traders: {Trader.query.count()}")

            print("\n🗑️  Deleting all trades, portfolio items, and ticker prices...")
            Trade.query.delete()
            Portfolio.query.delete()
            TickerPrice.query.delete()

            if recreate_traders:
                print("🗑️  Deleting all traders...")
                Trader.query.delete()
                db.session.commit()

                print("➕ Creating fresh traders...")
                traders = [
                    Trader(
                        name='bullish betty',
                        initial_balance=10000.00,
                        current_balance=10000.00,
                        risk_tolerance='high',
                        trading_timezone='America/New_York',
                        trading_ethos='Aggressive trader who loves momentum and high-conviction plays',
                        status=TraderStatus.ACTIVE
                    ),
                    Trader(
                        name='cautious carl',
                        initial_balance=10000.00,
                        current_balance=10000.00,
                        risk_tolerance='low',
                        trading_timezone='America/New_York',
                        trading_ethos='Conservative value investor who prefers steady gains over quick wins',
                        status=TraderStatus.ACTIVE
                    )
                ]

                for trader in traders:
                    db.session.add(trader)

            else:
                print("🔄 Resetting trader balances to initial amounts...")
                traders = Trader.query.all()
                for trader in traders:
                    trader.current_balance = trader.initial_balance
                    trader.last_trade_at = None

            db.session.commit()

            print("\n✅ Database reset complete!")
            print("\n📊 Final state:")
            print(f"   - Trades: {Trade.query.count()}")
            print(f"   - Portfolio items: {Portfolio.query.count()}")
            print(f"   - Ticker prices: {TickerPrice.query.count()}")
            print(f"   - Traders: {Trader.query.count()}")

            print("\n👥 Traders:")
            for trader in Trader.query.all():
                print(f"   - {trader.name}: ${trader.current_balance:.2f} (initial: ${trader.initial_balance:.2f})")

        except Exception as e:
            print(f"❌ Error during reset: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            sys.exit(1)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Reset database to clean state')
    parser.add_argument(
        '--recreate-traders',
        action='store_true',
        help='Delete and recreate traders from scratch (default: just reset balances)'
    )

    args = parser.parse_args()

    if args.recreate_traders:
        confirm = input("⚠️  This will DELETE all traders and create new ones. Are you sure? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Aborted")
            sys.exit(0)

    reset_database(recreate_traders=args.recreate_traders)
