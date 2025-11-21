#!/usr/bin/env python
"""
Seed database with dummy trading data for testing and visualization

This script creates realistic trading history for existing traders
to demonstrate charts and performance metrics.
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def seed_data():
    """Seed the database with dummy trading data"""
    print("🌱 Seeding database with dummy data...")

    # Import app and models
    try:
        from app import app, db
        from models import Trader, Trade, Portfolio, TickerPrice, TraderStatus, TradeAction
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        sys.exit(1)

    with app.app_context():
        try:
            # Get existing traders
            traders = Trader.query.filter_by(status=TraderStatus.ACTIVE).all()

            if not traders:
                print("📝 No active traders found. Creating sample traders...")

                # Create sample traders
                sample_traders = [
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
                    ),
                    Trader(
                        name='balanced beth',
                        initial_balance=10000.00,
                        current_balance=10000.00,
                        risk_tolerance='medium',
                        trading_timezone='America/New_York',
                        trading_ethos='Balanced approach mixing growth and value strategies',
                        status=TraderStatus.ACTIVE
                    )
                ]

                for trader in sample_traders:
                    db.session.add(trader)
                    print(f"  ✓ Created trader: {trader.name}")

                db.session.commit()
                traders = Trader.query.filter_by(status=TraderStatus.ACTIVE).all()

            print(f"📊 Found {len(traders)} active traders")

            # Define tickers and their price trajectories
            tickers_data = {
                'AAPL': {'start_price': 170.00, 'volatility': 0.02},
                'MSFT': {'start_price': 370.00, 'volatility': 0.015},
                'GOOGL': {'start_price': 140.00, 'volatility': 0.025},
                'AMZN': {'start_price': 155.00, 'volatility': 0.03},
                'TSLA': {'start_price': 240.00, 'volatility': 0.05},
                'NVDA': {'start_price': 480.00, 'volatility': 0.04},
                'META': {'start_price': 350.00, 'volatility': 0.028}
            }

            # Generate trades for each trader over the past 30 days
            days_back = 30
            trades_per_trader = 15

            for trader in traders:
                print(f"\n👤 Seeding trades for {trader.name}...")

                # Reset trader to initial state
                trader.current_balance = trader.initial_balance
                trader.last_trade_at = None

                # Clear existing trades and portfolio
                Trade.query.filter_by(trader_id=trader.id).delete()
                Portfolio.query.filter_by(trader_id=trader.id).delete()

                # Generate random trade dates
                base_date = datetime.utcnow() - timedelta(days=days_back)
                trade_dates = sorted([
                    base_date + timedelta(
                        days=random.randint(0, days_back),
                        hours=random.randint(9, 16),
                        minutes=random.randint(0, 59)
                    )
                    for _ in range(trades_per_trader)
                ])

                # Track holdings for sell decisions
                holdings = {}  # {ticker: {'quantity': X, 'avg_price': Y}}

                for trade_idx, trade_date in enumerate(trade_dates):
                    # Pick a random ticker
                    ticker = random.choice(list(tickers_data.keys()))
                    ticker_info = tickers_data[ticker]

                    # Calculate price at this point in time (simulate market movement)
                    days_elapsed = (trade_date - base_date).days
                    price_change = 1 + random.gauss(0.01, ticker_info['volatility']) * days_elapsed / days_back
                    current_price = ticker_info['start_price'] * price_change

                    # Decide action: buy or sell (prefer buy if no holdings)
                    can_sell = ticker in holdings and holdings[ticker]['quantity'] > 0

                    if not can_sell or (random.random() < 0.65 and float(trader.current_balance) > current_price * 10):
                        # BUY
                        action = TradeAction.BUY

                        # Calculate quantity based on risk tolerance
                        if trader.risk_tolerance == 'high':
                            max_invest = float(trader.current_balance) * 0.15
                        elif trader.risk_tolerance == 'medium':
                            max_invest = float(trader.current_balance) * 0.10
                        else:  # low
                            max_invest = float(trader.current_balance) * 0.05

                        quantity = int(max_invest / current_price)

                        if quantity == 0:
                            continue  # Skip if can't afford

                        total_amount = quantity * current_price

                        if float(trader.current_balance) < total_amount:
                            continue  # Skip if insufficient funds

                        trader.current_balance -= Decimal(str(total_amount))

                        # Update holdings
                        if ticker in holdings:
                            old_qty = holdings[ticker]['quantity']
                            old_cost = old_qty * holdings[ticker]['avg_price']
                            new_cost = old_cost + total_amount
                            new_qty = old_qty + quantity
                            holdings[ticker] = {
                                'quantity': new_qty,
                                'avg_price': new_cost / new_qty
                            }
                        else:
                            holdings[ticker] = {
                                'quantity': quantity,
                                'avg_price': current_price
                            }

                    else:
                        # SELL
                        action = TradeAction.SELL

                        # Sell 30-70% of holdings
                        sell_pct = random.uniform(0.3, 0.7)
                        quantity = max(1, int(holdings[ticker]['quantity'] * sell_pct))
                        total_amount = quantity * current_price

                        trader.current_balance += Decimal(str(total_amount))

                        # Update holdings
                        holdings[ticker]['quantity'] -= quantity
                        if holdings[ticker]['quantity'] == 0:
                            del holdings[ticker]

                    # Generate technical indicators (random but reasonable)
                    rsi = random.uniform(30, 70)
                    macd = random.gauss(0, 2)
                    sma_20 = current_price * random.uniform(0.98, 1.02)
                    sma_50 = current_price * random.uniform(0.95, 1.05)

                    recommendation = 'BUY' if action == TradeAction.BUY else 'SELL'
                    confidence = random.uniform(60, 90)

                    # Create trade
                    trade = Trade(
                        trader_id=trader.id,
                        ticker=ticker,
                        action=action,
                        quantity=quantity,
                        price=round(current_price, 2),
                        total_amount=round(total_amount, 2),
                        balance_after=trader.current_balance,
                        rsi=round(rsi, 2),
                        macd=round(macd, 2),
                        sma_20=round(sma_20, 2),
                        sma_50=round(sma_50, 2),
                        recommendation=recommendation,
                        confidence=round(confidence, 2),
                        notes=f"Seeded {action.value} trade",
                        executed_at=trade_date
                    )

                    db.session.add(trade)
                    trader.last_trade_at = trade_date

                    print(f"  ✓ {action.value} {quantity} {ticker} @ ${current_price:.2f} on {trade_date.strftime('%Y-%m-%d %H:%M')}")

                # Create portfolio entries for remaining holdings
                for ticker, holding in holdings.items():
                    if holding['quantity'] > 0:
                        portfolio = Portfolio(
                            trader_id=trader.id,
                            ticker=ticker,
                            quantity=holding['quantity'],
                            average_price=round(holding['avg_price'], 2),
                            total_cost=round(holding['quantity'] * holding['avg_price'], 2)
                        )
                        db.session.add(portfolio)
                        print(f"  📦 Portfolio: {holding['quantity']} shares of {ticker}")

            # Populate ticker_prices table with current prices
            print("\n💰 Populating ticker prices...")
            for ticker, info in tickers_data.items():
                # Calculate final price (30 days later)
                final_price = info['start_price'] * (1 + random.gauss(0.05, info['volatility'] * 2))

                ticker_price = TickerPrice.query.filter_by(ticker=ticker).first()
                if ticker_price:
                    ticker_price.current_price = round(final_price, 2)
                    ticker_price.last_updated = datetime.utcnow()
                else:
                    ticker_price = TickerPrice(
                        ticker=ticker,
                        current_price=round(final_price, 2),
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(ticker_price)

                print(f"  💵 {ticker}: ${round(final_price, 2)}")

            # Commit all changes
            db.session.commit()

            print("\n✅ Database seeding complete!")
            print("\n📊 Final Summary:")
            for trader in traders:
                portfolio = Portfolio.query.filter_by(trader_id=trader.id).all()
                trades = Trade.query.filter_by(trader_id=trader.id).count()
                print(f"  {trader.name}:")
                print(f"    - Balance: ${trader.current_balance:.2f}")
                print(f"    - Trades: {trades}")
                print(f"    - Portfolio items: {len(portfolio)}")

        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            sys.exit(1)


if __name__ == '__main__':
    seed_data()
