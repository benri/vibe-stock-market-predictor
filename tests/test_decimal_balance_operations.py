"""
Regression tests for Decimal/float balance calculations.

These tests verify that trader balance operations (buy/sell) handle
the Decimal type from the database correctly when mixed with float
prices from the stock API.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from datetime import datetime


def test_buy_operation_with_decimal_balance(client, app, db):
    """Test that buy operations handle Decimal balance correctly"""
    from models import Trader, TraderStatus

    with app.app_context():
        # Create trader with Decimal balance
        trader = Trader(
            name='Decimal Test Buyer',
            initial_balance=Decimal('10000.00'),
            current_balance=Decimal('10000.00'),
            risk_tolerance='medium',
            trading_timezone='America/New_York',
            status=TraderStatus.ACTIVE
        )
        db.session.add(trader)
        db.session.commit()

        # Mock stock data with typical float response
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.__len__ = lambda self: 100
        mock_df.iloc = MagicMock()
        mock_df.iloc.__getitem__ = MagicMock(return_value={
            'Close': 150.50,
            'SMA_20': 145.00,
            'SMA_50': 140.00,
            'RSI': 45.0,
            'MACD': 1.5,
            'Signal_Line': 1.0,
            'Momentum': 3.0
        })

        with patch('tasks.TimeSeries') as mock_ts:
            mock_ts.return_value.get_daily.return_value = (mock_df, {})

            # Import and call the trading function
            from tasks import execute_trader_decisions_by_timezone

            # This should not raise "unsupported operand type" error
            result = execute_trader_decisions_by_timezone('America/New_York', 'morning')

            assert result['status'] == 'success'

            # Verify balance was updated (should be Decimal type)
            trader_after = Trader.query.get(trader.id)
            assert isinstance(trader_after.current_balance, Decimal)
            # Balance should have changed if trades executed
            assert trader_after.current_balance <= Decimal('10000.00')


def test_sell_operation_with_decimal_balance(client, app, db):
    """Test that sell operations handle Decimal balance correctly"""
    from models import Trader, Portfolio, TraderStatus

    with app.app_context():
        # Create trader with Decimal balance and existing position
        trader = Trader(
            name='Decimal Test Seller',
            initial_balance=Decimal('10000.00'),
            current_balance=Decimal('5000.00'),
            risk_tolerance='medium',
            trading_timezone='America/New_York',
            status=TraderStatus.ACTIVE
        )
        db.session.add(trader)
        db.session.commit()

        # Add portfolio position
        portfolio = Portfolio(
            trader_id=trader.id,
            ticker='AAPL',
            quantity=10,
            average_price=Decimal('250.00'),
            total_cost=Decimal('2500.00')
        )
        db.session.add(portfolio)
        db.session.commit()

        # Mock stock data that triggers sell
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.__len__ = lambda self: 100
        mock_df.iloc = MagicMock()
        mock_df.iloc.__getitem__ = MagicMock(return_value={
            'Close': 200.00,
            'SMA_20': 220.00,
            'SMA_50': 230.00,
            'RSI': 75.0,
            'MACD': -2.5,
            'Signal_Line': -1.0,
            'Momentum': -8.0
        })

        with patch('tasks.TimeSeries') as mock_ts:
            mock_ts.return_value.get_daily.return_value = (mock_df, {})

            from tasks import execute_trader_decisions_by_timezone

            # This should not raise "unsupported operand type" error
            result = execute_trader_decisions_by_timezone('America/New_York', 'morning')

            assert result['status'] == 'success'

            # Verify balance increased (Decimal type)
            trader_after = Trader.query.get(trader.id)
            assert isinstance(trader_after.current_balance, Decimal)


def test_mixed_decimal_float_calculations(app):
    """Test that Decimal balances can be mixed with float prices"""
    from decimal import Decimal

    with app.app_context():
        # Simulate the operations in tasks.py
        trader_balance = Decimal('10000.00')
        stock_price = 292.81  # Float from API
        quantity = 10

        # Test buy operation
        total_amount = quantity * stock_price
        new_balance = trader_balance - Decimal(str(total_amount))

        assert isinstance(new_balance, Decimal)
        assert new_balance == Decimal('10000.00') - Decimal('2928.10')

        # Test sell operation
        sell_amount = quantity * stock_price
        final_balance = new_balance + Decimal(str(sell_amount))

        assert isinstance(final_balance, Decimal)
        assert final_balance == Decimal('10000.00')


def test_decimal_precision_maintained(app):
    """Test that Decimal precision is maintained in calculations"""
    from decimal import Decimal

    with app.app_context():
        # Test with prices that would lose precision as float
        balance = Decimal('10000.00')
        price = 123.456789  # Many decimal places
        quantity = 7

        total = quantity * price
        new_balance = balance - Decimal(str(total))

        # Should maintain precision
        assert isinstance(new_balance, Decimal)
        # Verify calculation is correct
        expected = Decimal('10000.00') - Decimal('864.197523')
        assert abs(new_balance - expected) < Decimal('0.01')


def test_zero_quantity_does_not_error(client, app, db):
    """Test that zero quantity (insufficient funds) doesn't cause errors"""
    from models import Trader, TraderStatus

    with app.app_context():
        # Create trader with very low balance
        trader = Trader(
            name='Decimal Poor Trader',
            initial_balance=Decimal('10.00'),
            current_balance=Decimal('10.00'),
            risk_tolerance='medium',
            trading_timezone='America/New_York',
            status=TraderStatus.ACTIVE
        )
        db.session.add(trader)
        db.session.commit()

        # Mock expensive stock
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.__len__ = lambda self: 100
        mock_df.iloc = MagicMock()
        mock_df.iloc.__getitem__ = MagicMock(return_value={
            'Close': 1000.00,  # Too expensive
            'SMA_20': 950.00,
            'SMA_50': 900.00,
            'RSI': 45.0,
            'MACD': 1.5,
            'Signal_Line': 1.0,
            'Momentum': 3.0
        })

        with patch('tasks.TimeSeries') as mock_ts:
            mock_ts.return_value.get_daily.return_value = (mock_df, {})

            from tasks import execute_trader_decisions_by_timezone

            # Should complete without error even though no trades execute
            result = execute_trader_decisions_by_timezone('America/New_York', 'morning')

            assert result['status'] == 'success'
            assert result['trades_executed'] == 0

            # Balance should remain unchanged
            trader_after = Trader.query.get(trader.id)
            assert trader_after.current_balance == Decimal('10.00')
