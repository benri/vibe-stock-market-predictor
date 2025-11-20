"""
Tests for database models
"""

import pytest
from datetime import datetime
from models import Trader, Trade, Portfolio, TraderStatus, TradeAction


class TestTraderModel:
    """Test cases for the Trader model"""

    def test_create_trader(self, db):
        """Test creating a new trader"""
        trader = Trader(
            name='Risk Taker',
            initial_balance=5000.00,
            current_balance=5000.00,
            risk_tolerance='high',
            trading_ethos='Aggressive growth strategy',
            status=TraderStatus.ACTIVE
        )
        db.session.add(trader)
        db.session.commit()

        assert trader.id is not None
        assert trader.name == 'Risk Taker'
        assert float(trader.initial_balance) == 5000.00
        assert float(trader.current_balance) == 5000.00
        assert trader.risk_tolerance == 'high'
        assert trader.trading_ethos == 'Aggressive growth strategy'
        assert trader.status == TraderStatus.ACTIVE

    def test_trader_to_dict(self, sample_trader):
        """Test converting trader to dictionary"""
        trader_dict = sample_trader.to_dict()

        assert trader_dict['id'] == sample_trader.id
        assert trader_dict['name'] == 'Test Trader'
        assert trader_dict['initial_balance'] == 10000.00
        assert trader_dict['current_balance'] == 10000.00
        assert trader_dict['risk_tolerance'] == 'medium'
        assert trader_dict['status'] == 'active'
        assert trader_dict['profit_loss'] == 0.0
        assert trader_dict['profit_loss_percentage'] == 0.0
        assert trader_dict['total_trades'] == 0

    def test_trader_profit_loss_calculation(self, db):
        """Test profit/loss calculation"""
        trader = Trader(
            name='Profitable Trader',
            initial_balance=10000.00,
            current_balance=12000.00,
            risk_tolerance='medium',
            status=TraderStatus.ACTIVE
        )
        db.session.add(trader)
        db.session.commit()

        trader_dict = trader.to_dict()
        assert trader_dict['profit_loss'] == 2000.00
        assert trader_dict['profit_loss_percentage'] == 20.0

    def test_trader_unique_name_constraint(self, db, sample_trader):
        """Test that trader names must be unique"""
        duplicate_trader = Trader(
            name='Test Trader',  # Same name as sample_trader
            initial_balance=5000.00,
            current_balance=5000.00,
            risk_tolerance='low',
            status=TraderStatus.ACTIVE
        )
        db.session.add(duplicate_trader)

        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()


class TestTradeModel:
    """Test cases for the Trade model"""

    def test_create_trade(self, db, sample_trader):
        """Test creating a new trade"""
        trade = Trade(
            trader_id=sample_trader.id,
            ticker='MSFT',
            action=TradeAction.BUY,
            quantity=5,
            price=300.00,
            total_amount=1500.00,
            balance_after=8500.00,
            rsi=50.0,
            macd=1.5,
            sma_20=295.00,
            sma_50=290.00,
            recommendation='BUY',
            confidence=70,
            notes='Strong momentum indicators'
        )
        db.session.add(trade)
        db.session.commit()

        assert trade.id is not None
        assert trade.ticker == 'MSFT'
        assert trade.action == TradeAction.BUY
        assert trade.quantity == 5
        assert float(trade.price) == 300.00
        assert float(trade.total_amount) == 1500.00
        assert float(trade.balance_after) == 8500.00

    def test_trade_to_dict(self, sample_trade, sample_trader):
        """Test converting trade to dictionary"""
        trade_dict = sample_trade.to_dict()

        assert trade_dict['id'] == sample_trade.id
        assert trade_dict['trader_id'] == sample_trader.id
        assert trade_dict['trader_name'] == 'Test Trader'
        assert trade_dict['ticker'] == 'AAPL'
        assert trade_dict['action'] == 'buy'
        assert trade_dict['quantity'] == 10
        assert trade_dict['price'] == 150.00
        assert trade_dict['total_amount'] == 1500.00
        assert trade_dict['balance_after'] == 8500.00
        assert trade_dict['rsi'] == 45.0
        assert trade_dict['recommendation'] == 'BUY'
        assert trade_dict['confidence'] == 75

    def test_trade_relationship_with_trader(self, sample_trade, sample_trader):
        """Test that trades are properly related to traders"""
        assert sample_trade.trader == sample_trader
        assert sample_trade in sample_trader.trades.all()


class TestPortfolioModel:
    """Test cases for the Portfolio model"""

    def test_create_portfolio(self, db, sample_trader):
        """Test creating a new portfolio holding"""
        portfolio = Portfolio(
            trader_id=sample_trader.id,
            ticker='GOOGL',
            quantity=3,
            average_price=140.00,
            total_cost=420.00
        )
        db.session.add(portfolio)
        db.session.commit()

        assert portfolio.id is not None
        assert portfolio.ticker == 'GOOGL'
        assert portfolio.quantity == 3
        assert float(portfolio.average_price) == 140.00
        assert float(portfolio.total_cost) == 420.00

    def test_portfolio_to_dict(self, sample_portfolio, sample_trader):
        """Test converting portfolio to dictionary"""
        portfolio_dict = sample_portfolio.to_dict()

        assert portfolio_dict['id'] == sample_portfolio.id
        assert portfolio_dict['trader_id'] == sample_trader.id
        assert portfolio_dict['ticker'] == 'AAPL'
        assert portfolio_dict['quantity'] == 10
        assert portfolio_dict['average_price'] == 150.00
        assert portfolio_dict['total_cost'] == 1500.00

    def test_portfolio_to_dict_with_current_price(self, sample_portfolio):
        """Test portfolio dictionary with current price calculations"""
        current_price = 160.00
        portfolio_dict = sample_portfolio.to_dict(current_price=current_price)

        assert portfolio_dict['current_price'] == 160.00
        assert portfolio_dict['current_value'] == 1600.00  # 10 * 160
        assert portfolio_dict['profit_loss'] == 100.00  # 1600 - 1500
        assert portfolio_dict['profit_loss_percentage'] == pytest.approx(6.67, rel=0.1)

    def test_portfolio_unique_constraint(self, db, sample_trader, sample_portfolio):
        """Test that each trader can only have one position per ticker"""
        duplicate_portfolio = Portfolio(
            trader_id=sample_trader.id,
            ticker='AAPL',  # Same ticker as sample_portfolio
            quantity=5,
            average_price=155.00,
            total_cost=775.00
        )
        db.session.add(duplicate_portfolio)

        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()

    def test_portfolio_relationship_with_trader(self, sample_portfolio, sample_trader):
        """Test that portfolio items are properly related to traders"""
        assert sample_portfolio.trader == sample_trader
        assert sample_portfolio in sample_trader.portfolio.all()


class TestCascadeDeletes:
    """Test cascade delete behavior"""

    def test_deleting_trader_deletes_trades(self, db, sample_trader, sample_trade):
        """Test that deleting a trader also deletes their trades"""
        trader_id = sample_trader.id
        trade_id = sample_trade.id

        db.session.delete(sample_trader)
        db.session.commit()

        # Check that trader and trade are both gone
        assert Trader.query.get(trader_id) is None
        assert Trade.query.get(trade_id) is None

    def test_deleting_trader_deletes_portfolio(self, db, sample_trader, sample_portfolio):
        """Test that deleting a trader also deletes their portfolio"""
        trader_id = sample_trader.id
        portfolio_id = sample_portfolio.id

        db.session.delete(sample_trader)
        db.session.commit()

        # Check that trader and portfolio are both gone
        assert Trader.query.get(trader_id) is None
        assert Portfolio.query.get(portfolio_id) is None
