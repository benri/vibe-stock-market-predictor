"""
Tests for API endpoints
"""

import json
import pytest
from models import Trader, Trade, Portfolio, TraderStatus, TradeAction


class TestTraderEndpoints:
    """Test cases for trader API endpoints"""

    def test_get_traders_empty(self, client, db):
        """Test getting traders when none exist"""
        response = client.get('/api/traders')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'traders' in data
        assert len(data['traders']) == 0

    def test_get_traders(self, client, sample_trader):
        """Test getting all traders"""
        response = client.get('/api/traders')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'traders' in data
        assert len(data['traders']) == 1
        assert data['traders'][0]['name'] == 'Test Trader'

    def test_create_trader(self, client, db):
        """Test creating a new trader"""
        trader_data = {
            'name': 'New Trader',
            'initial_balance': 15000.00,
            'risk_tolerance': 'high',
            'trading_ethos': 'Growth focused strategy'
        }

        response = client.post(
            '/api/traders',
            data=json.dumps(trader_data),
            content_type='application/json'
        )
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['name'] == 'New Trader'
        assert data['initial_balance'] == 15000.00
        assert data['risk_tolerance'] == 'high'
        assert data['trading_ethos'] == 'Growth focused strategy'
        assert data['status'] == 'active'

    def test_create_trader_missing_name(self, client, db):
        """Test creating a trader without a name"""
        trader_data = {
            'initial_balance': 10000.00,
            'risk_tolerance': 'medium'
        }

        response = client.post(
            '/api/traders',
            data=json.dumps(trader_data),
            content_type='application/json'
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data

    def test_create_trader_duplicate_name(self, client, sample_trader):
        """Test creating a trader with a duplicate name"""
        trader_data = {
            'name': 'Test Trader',  # Same as sample_trader
            'initial_balance': 10000.00,
            'risk_tolerance': 'medium'
        }

        response = client.post(
            '/api/traders',
            data=json.dumps(trader_data),
            content_type='application/json'
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data
        assert 'already exists' in data['error']

    def test_get_trader_by_id(self, client, sample_trader):
        """Test getting a specific trader by ID"""
        response = client.get(f'/api/traders/{sample_trader.id}')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['id'] == sample_trader.id
        assert data['name'] == 'Test Trader'

    def test_get_trader_not_found(self, client, db):
        """Test getting a non-existent trader"""
        response = client.get('/api/traders/99999')
        assert response.status_code == 404

    def test_update_trader(self, client, sample_trader):
        """Test updating a trader"""
        update_data = {
            'name': 'Updated Trader',
            'risk_tolerance': 'low',
            'status': 'paused',
            'trading_ethos': 'Conservative approach'
        }

        response = client.put(
            f'/api/traders/{sample_trader.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['name'] == 'Updated Trader'
        assert data['risk_tolerance'] == 'low'
        assert data['status'] == 'paused'
        assert data['trading_ethos'] == 'Conservative approach'

    def test_delete_trader(self, client, db, sample_trader):
        """Test deleting a trader"""
        trader_id = sample_trader.id

        response = client.delete(f'/api/traders/{trader_id}')
        assert response.status_code == 200

        # Verify trader is deleted
        assert Trader.query.get(trader_id) is None


class TestTradeEndpoints:
    """Test cases for trade API endpoints"""

    def test_get_trader_trades_empty(self, client, sample_trader):
        """Test getting trades when none exist"""
        response = client.get(f'/api/traders/{sample_trader.id}/trades')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'trades' in data
        assert len(data['trades']) == 0

    def test_get_trader_trades(self, client, sample_trader, sample_trade):
        """Test getting all trades for a trader"""
        response = client.get(f'/api/traders/{sample_trader.id}/trades')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'trades' in data
        assert len(data['trades']) == 1
        assert data['trades'][0]['ticker'] == 'AAPL'
        assert data['trades'][0]['action'] == 'buy'

    def test_execute_buy_trade(self, client, db, sample_trader):
        """Test executing a buy trade"""
        trade_data = {
            'ticker': 'MSFT',
            'action': 'buy',
            'quantity': 5,
            'price': 300.00,
            'rsi': 50.0,
            'macd': 1.5,
            'sma_20': 295.00,
            'sma_50': 290.00,
            'recommendation': 'BUY',
            'confidence': 70,
            'notes': 'Strong momentum'
        }

        response = client.post(
            f'/api/traders/{sample_trader.id}/trades',
            data=json.dumps(trade_data),
            content_type='application/json'
        )
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['ticker'] == 'MSFT'
        assert data['action'] == 'buy'
        assert data['quantity'] == 5
        assert data['price'] == 300.00
        assert data['total_amount'] == 1500.00
        assert data['balance_after'] == 8500.00

        # Verify trader balance updated
        trader = Trader.query.get(sample_trader.id)
        assert float(trader.current_balance) == 8500.00

        # Verify portfolio created
        portfolio = Portfolio.query.filter_by(
            trader_id=sample_trader.id,
            ticker='MSFT'
        ).first()
        assert portfolio is not None
        assert portfolio.quantity == 5
        assert float(portfolio.average_price) == 300.00

    def test_execute_sell_trade(self, client, db, sample_trader, sample_portfolio):
        """Test executing a sell trade"""
        # First, adjust trader balance to reflect the portfolio
        sample_trader.current_balance = 8500.00
        db.session.commit()

        trade_data = {
            'ticker': 'AAPL',
            'action': 'sell',
            'quantity': 5,
            'price': 155.00,
            'recommendation': 'SELL',
            'confidence': 65
        }

        response = client.post(
            f'/api/traders/{sample_trader.id}/trades',
            data=json.dumps(trade_data),
            content_type='application/json'
        )
        assert response.status_code == 201

        data = json.loads(response.data)
        assert data['action'] == 'sell'
        assert data['quantity'] == 5
        assert data['balance_after'] == 9275.00  # 8500 + (5 * 155)

        # Verify trader balance updated
        trader = Trader.query.get(sample_trader.id)
        assert float(trader.current_balance) == 9275.00

        # Verify portfolio updated
        portfolio = Portfolio.query.filter_by(
            trader_id=sample_trader.id,
            ticker='AAPL'
        ).first()
        assert portfolio is not None
        assert portfolio.quantity == 5  # 10 - 5

    def test_execute_trade_insufficient_balance(self, client, sample_trader):
        """Test executing a trade with insufficient balance"""
        trade_data = {
            'ticker': 'TSLA',
            'action': 'buy',
            'quantity': 100,
            'price': 200.00  # Total: $20,000 but balance is only $10,000
        }

        response = client.post(
            f'/api/traders/{sample_trader.id}/trades',
            data=json.dumps(trade_data),
            content_type='application/json'
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data
        assert 'Insufficient balance' in data['error']

    def test_execute_trade_insufficient_shares(self, client, sample_trader, sample_portfolio):
        """Test selling more shares than owned"""
        trade_data = {
            'ticker': 'AAPL',
            'action': 'sell',
            'quantity': 20,  # Portfolio only has 10
            'price': 155.00
        }

        response = client.post(
            f'/api/traders/{sample_trader.id}/trades',
            data=json.dumps(trade_data),
            content_type='application/json'
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data
        assert 'Insufficient shares' in data['error']

    def test_execute_trade_inactive_trader(self, client, db, sample_trader):
        """Test executing a trade with an inactive trader"""
        sample_trader.status = TraderStatus.PAUSED
        db.session.commit()

        trade_data = {
            'ticker': 'AAPL',
            'action': 'buy',
            'quantity': 5,
            'price': 150.00
        }

        response = client.post(
            f'/api/traders/{sample_trader.id}/trades',
            data=json.dumps(trade_data),
            content_type='application/json'
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'error' in data
        assert 'not active' in data['error']


class TestPortfolioEndpoints:
    """Test cases for portfolio API endpoints"""

    def test_get_portfolio_empty(self, client, sample_trader):
        """Test getting portfolio when empty"""
        response = client.get(f'/api/traders/{sample_trader.id}/portfolio')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['trader_id'] == sample_trader.id
        assert data['trader_name'] == 'Test Trader'
        assert data['current_balance'] == 10000.00
        assert len(data['portfolio']) == 0

    def test_get_portfolio(self, client, sample_trader, sample_portfolio):
        """Test getting portfolio with holdings"""
        response = client.get(f'/api/traders/{sample_trader.id}/portfolio')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['trader_id'] == sample_trader.id
        assert len(data['portfolio']) == 1
        assert data['portfolio'][0]['ticker'] == 'AAPL'
        assert data['portfolio'][0]['quantity'] == 10
        assert data['portfolio'][0]['average_price'] == 150.00


class TestAllTradesEndpoint:
    """Test cases for the all trades endpoint"""

    def test_get_all_trades(self, client, sample_trade):
        """Test getting all trades across all traders"""
        response = client.get('/api/trades')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'trades' in data
        assert len(data['trades']) == 1
        assert data['trades'][0]['ticker'] == 'AAPL'

    def test_get_all_trades_filtered_by_ticker(self, client, db, sample_trader):
        """Test filtering trades by ticker"""
        # Create multiple trades
        trade1 = Trade(
            trader_id=sample_trader.id,
            ticker='AAPL',
            action=TradeAction.BUY,
            quantity=5,
            price=150.00,
            total_amount=750.00,
            balance_after=9250.00
        )
        trade2 = Trade(
            trader_id=sample_trader.id,
            ticker='MSFT',
            action=TradeAction.BUY,
            quantity=3,
            price=300.00,
            total_amount=900.00,
            balance_after=8350.00
        )
        db.session.add_all([trade1, trade2])
        db.session.commit()

        # Filter by AAPL
        response = client.get('/api/trades?ticker=AAPL')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert len(data['trades']) == 1
        assert data['trades'][0]['ticker'] == 'AAPL'
