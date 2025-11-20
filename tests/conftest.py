"""
Test configuration and fixtures for pytest
"""

import os
import pytest
from dotenv import load_dotenv

# Load test environment variables from .env.test before importing app
load_dotenv('.env.test')

from app import app as flask_app, db as _db
from models import Trader, Trade, Portfolio, TraderStatus, TradeAction


@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask app"""
    # Configure test settings
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/vibe-stock-market-predictor-test'
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Create test database tables
    with flask_app.app_context():
        _db.create_all()

    yield flask_app

    # Clean up
    with flask_app.app_context():
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    """Create a clean database for each test"""
    with app.app_context():
        # Clean up any existing data
        _db.session.remove()
        _db.drop_all()
        _db.create_all()

        yield _db

        # Rollback any uncommitted changes
        _db.session.remove()


@pytest.fixture
def client(app):
    """Create a test client for the Flask app"""
    return app.test_client()


@pytest.fixture
def sample_trader(db):
    """Create a sample trader for testing"""
    trader = Trader(
        name='Test Trader',
        initial_balance=10000.00,
        current_balance=10000.00,
        risk_tolerance='medium',
        trading_ethos='Balanced approach with focus on technical indicators',
        status=TraderStatus.ACTIVE
    )
    db.session.add(trader)
    db.session.commit()
    return trader


@pytest.fixture
def sample_trade(db, sample_trader):
    """Create a sample trade for testing"""
    trade = Trade(
        trader_id=sample_trader.id,
        ticker='AAPL',
        action=TradeAction.BUY,
        quantity=10,
        price=150.00,
        total_amount=1500.00,
        balance_after=8500.00,
        rsi=45.0,
        macd=2.5,
        sma_20=148.00,
        sma_50=145.00,
        recommendation='BUY',
        confidence=75
    )
    db.session.add(trade)
    db.session.commit()
    return trade


@pytest.fixture
def sample_portfolio(db, sample_trader):
    """Create a sample portfolio holding for testing"""
    portfolio = Portfolio(
        trader_id=sample_trader.id,
        ticker='AAPL',
        quantity=10,
        average_price=150.00,
        total_cost=1500.00
    )
    db.session.add(portfolio)
    db.session.commit()
    return portfolio
