"""
Database models for Vibe Stock Market Predictor
"""

from datetime import datetime
from enum import Enum
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class TraderStatus(Enum):
    """Status of a trader"""
    ACTIVE = 'active'
    PAUSED = 'paused'
    ARCHIVED = 'archived'


class TradeAction(Enum):
    """Type of trade action"""
    BUY = 'buy'
    SELL = 'sell'


class Trader(db.Model):
    """Trader (bot) that executes trades"""
    __tablename__ = 'traders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.Enum(TraderStatus), default=TraderStatus.ACTIVE, nullable=False)

    # Balance tracking
    initial_balance = db.Column(db.Numeric(12, 2), nullable=False, default=10000.00)
    current_balance = db.Column(db.Numeric(12, 2), nullable=False, default=10000.00)

    # Strategy
    strategy_name = db.Column(db.String(50), nullable=False, default='default')
    risk_tolerance = db.Column(db.String(20), nullable=False, default='medium')
    trading_ethos = db.Column(db.Text, nullable=True)
    trading_timezone = db.Column(db.String(50), nullable=False, default='America/New_York')

    # Custom watchlist configuration
    custom_watchlist = db.Column(db.JSON, nullable=True)  # Array of ticker symbols
    watchlist_size = db.Column(db.Integer, nullable=False, default=6)  # Discovery tickers per session
    use_custom_watchlist = db.Column(db.Boolean, nullable=False, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_trade_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    trades = db.relationship('Trade', back_populates='trader', lazy='dynamic', cascade='all, delete-orphan')
    portfolio = db.relationship('Portfolio', back_populates='trader', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Trader {self.name} - ${self.current_balance}>'

    def to_dict(self):
        """Convert trader to dictionary with market-value based P/L and detailed performance metrics"""
        portfolio_items = self.portfolio.all()

        # Calculate portfolio value using current market prices from ticker_prices table
        portfolio_market_value = 0
        portfolio_cost_basis = 0
        for item in portfolio_items:
            cost_basis = float(item.total_cost)
            portfolio_cost_basis += cost_basis

            # Get current price from ticker_prices table
            ticker_price = TickerPrice.query.filter_by(ticker=item.ticker).first()
            if ticker_price and ticker_price.current_price and item.quantity > 0:
                # Use latest market price
                market_value = float(ticker_price.current_price) * item.quantity
                portfolio_market_value += market_value
            else:
                # Fallback to cost basis if no current price
                portfolio_market_value += cost_basis

        total_value = float(self.current_balance) + portfolio_market_value
        unrealized_pl = portfolio_market_value - portfolio_cost_basis

        # Calculate detailed performance metrics from trade history
        all_trades = self.trades.all()
        buy_trades = [t for t in all_trades if t.action == TradeAction.BUY]
        sell_trades = [t for t in all_trades if t.action == TradeAction.SELL]

        # Calculate realized P/L by comparing sell prices to average buy prices per ticker
        realized_pl = 0
        ticker_buy_history = {}  # Track buy prices per ticker for realized P/L calculation

        for trade in all_trades:
            if trade.action == TradeAction.BUY:
                if trade.ticker not in ticker_buy_history:
                    ticker_buy_history[trade.ticker] = []
                ticker_buy_history[trade.ticker].append({
                    'price': float(trade.price),
                    'quantity': trade.quantity
                })
            elif trade.action == TradeAction.SELL:
                # Calculate realized gain/loss for this sell
                if trade.ticker in ticker_buy_history and ticker_buy_history[trade.ticker]:
                    # Calculate average buy price for this ticker
                    total_cost = sum(h['price'] * h['quantity'] for h in ticker_buy_history[trade.ticker])
                    total_qty = sum(h['quantity'] for h in ticker_buy_history[trade.ticker])
                    avg_buy_price = total_cost / total_qty if total_qty > 0 else 0

                    # Realized gain/loss = (sell_price - avg_buy_price) * quantity_sold
                    trade_pl = (float(trade.price) - avg_buy_price) * trade.quantity
                    realized_pl += trade_pl

        # Calculate win rate (profitable trades vs total trades)
        winning_trades = 0
        losing_trades = 0

        for trade in sell_trades:
            if trade.ticker in ticker_buy_history and ticker_buy_history[trade.ticker]:
                total_cost = sum(h['price'] * h['quantity'] for h in ticker_buy_history[trade.ticker])
                total_qty = sum(h['quantity'] for h in ticker_buy_history[trade.ticker])
                avg_buy_price = total_cost / total_qty if total_qty > 0 else 0

                if float(trade.price) > avg_buy_price:
                    winning_trades += 1
                else:
                    losing_trades += 1

        win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0

        # Calculate average trade sizes
        avg_buy_amount = sum(float(t.total_amount) for t in buy_trades) / len(buy_trades) if buy_trades else 0
        avg_sell_amount = sum(float(t.total_amount) for t in sell_trades) / len(sell_trades) if sell_trades else 0

        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'initial_balance': float(self.initial_balance),
            'current_balance': float(self.current_balance),
            'portfolio_value': portfolio_market_value,
            'portfolio_cost_basis': portfolio_cost_basis,
            'unrealized_pl': unrealized_pl,
            'unrealized_pl_percentage': (unrealized_pl / portfolio_cost_basis * 100) if portfolio_cost_basis > 0 else 0,
            'realized_pl': realized_pl,
            'total_value': total_value,
            'strategy_name': self.strategy_name,
            'risk_tolerance': self.risk_tolerance,
            'trading_ethos': self.trading_ethos,
            'trading_timezone': self.trading_timezone,
            'custom_watchlist': self.custom_watchlist,
            'watchlist_size': self.watchlist_size,
            'use_custom_watchlist': self.use_custom_watchlist,
            'created_at': self.created_at.isoformat(),
            'last_trade_at': self.last_trade_at.isoformat() if self.last_trade_at else None,
            'total_trades': len(all_trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_buy_amount': avg_buy_amount,
            'avg_sell_amount': avg_sell_amount,
            'profit_loss': total_value - float(self.initial_balance),
            'profit_loss_percentage': float((total_value - float(self.initial_balance)) / float(self.initial_balance) * 100) if self.initial_balance > 0 else 0
        }


class Trade(db.Model):
    """Record of a trade executed by a trader"""
    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True)
    trader_id = db.Column(db.Integer, db.ForeignKey('traders.id'), nullable=False)

    # Trade details
    ticker = db.Column(db.String(10), nullable=False, index=True)
    action = db.Column(db.Enum(TradeAction), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)

    # Balance after trade
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)

    # Technical indicators at time of trade
    rsi = db.Column(db.Numeric(10, 2), nullable=True)
    macd = db.Column(db.Numeric(10, 2), nullable=True)
    sma_20 = db.Column(db.Numeric(10, 2), nullable=True)
    sma_50 = db.Column(db.Numeric(10, 2), nullable=True)

    # Decision metadata
    recommendation = db.Column(db.String(10), nullable=True)
    confidence = db.Column(db.Numeric(5, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Timestamp
    executed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    trader = db.relationship('Trader', back_populates='trades')

    def __repr__(self):
        return f'<Trade {self.action.value} {self.quantity} {self.ticker} @ ${self.price}>'

    def to_dict(self):
        """Convert trade to dictionary"""
        return {
            'id': self.id,
            'trader_id': self.trader_id,
            'trader_name': self.trader.name,
            'ticker': self.ticker,
            'action': self.action.value,
            'quantity': self.quantity,
            'price': float(self.price),
            'total_amount': float(self.total_amount),
            'balance_after': float(self.balance_after),
            'rsi': float(self.rsi) if self.rsi else None,
            'macd': float(self.macd) if self.macd else None,
            'sma_20': float(self.sma_20) if self.sma_20 else None,
            'sma_50': float(self.sma_50) if self.sma_50 else None,
            'recommendation': self.recommendation,
            'confidence': float(self.confidence) if self.confidence else None,
            'notes': self.notes,
            'executed_at': self.executed_at.isoformat()
        }


class Portfolio(db.Model):
    """Current holdings of a trader"""
    __tablename__ = 'portfolio'

    id = db.Column(db.Integer, primary_key=True)
    trader_id = db.Column(db.Integer, db.ForeignKey('traders.id'), nullable=False)

    # Holding details
    ticker = db.Column(db.String(10), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    average_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_cost = db.Column(db.Numeric(12, 2), nullable=False)

    # Timestamps
    first_purchased_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    trader = db.relationship('Trader', back_populates='portfolio')

    # Unique constraint: one row per trader per ticker
    __table_args__ = (
        db.UniqueConstraint('trader_id', 'ticker', name='unique_trader_ticker'),
    )

    def __repr__(self):
        return f'<Portfolio {self.ticker}: {self.quantity} @ avg ${self.average_price}>'

    def to_dict(self, current_price=None):
        """Convert portfolio holding to dictionary"""
        result = {
            'id': self.id,
            'trader_id': self.trader_id,
            'ticker': self.ticker,
            'quantity': self.quantity,
            'average_price': float(self.average_price),
            'total_cost': float(self.total_cost),
            'first_purchased_at': self.first_purchased_at.isoformat(),
            'last_updated_at': self.last_updated_at.isoformat()
        }

        if current_price:
            current_value = current_price * self.quantity
            total_cost_float = float(self.total_cost)
            result['current_price'] = current_price
            result['current_value'] = float(current_value)
            result['profit_loss'] = float(current_value - total_cost_float)
            result['profit_loss_percentage'] = float((current_value - total_cost_float) / total_cost_float * 100) if total_cost_float > 0 else 0

        return result


class TickerPrice(db.Model):
    """Latest market prices for ticker symbols (single source of truth)"""
    __tablename__ = 'ticker_prices'

    ticker = db.Column(db.String(10), primary_key=True)
    current_price = db.Column(db.Numeric(10, 2), nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<TickerPrice {self.ticker}: ${self.current_price}>'

    def to_dict(self):
        """Convert ticker price to dictionary"""
        return {
            'ticker': self.ticker,
            'current_price': float(self.current_price),
            'last_updated': self.last_updated.isoformat()
        }


class ApiUsageLog(db.Model):
    """Track daily API usage to manage rate limits"""
    __tablename__ = 'api_usage_log'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True, index=True)
    call_count = db.Column(db.Integer, nullable=False, default=0)
    last_reset = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<ApiUsageLog {self.date}: {self.call_count} calls>'

    def to_dict(self):
        """Convert API usage log to dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'call_count': self.call_count,
            'last_reset': self.last_reset.isoformat(),
            'created_at': self.created_at.isoformat()
        }


class TickerPool(db.Model):
    """Pool of available tickers for trading analysis"""
    __tablename__ = 'ticker_pool'

    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=True)
    exchange = db.Column(db.String(50), nullable=False, index=True)  # NYSE, NASDAQ, LSE, TSE
    timezone = db.Column(db.String(50), nullable=False, index=True)  # America/New_York, Europe/London, Asia/Tokyo
    market_cap = db.Column(db.Numeric(20, 2), nullable=True)  # Market capitalization
    sector = db.Column(db.String(100), nullable=True, index=True)  # Technology, Finance, Healthcare, etc.
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    # Metadata
    source = db.Column(db.String(50), nullable=True)  # sp500, ftse100, nikkei225, custom
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('ticker', 'exchange', name='unique_ticker_exchange'),
    )

    def __repr__(self):
        return f'<TickerPool {self.ticker} ({self.exchange})>'

    def to_dict(self):
        """Convert ticker pool entry to dictionary"""
        return {
            'id': self.id,
            'ticker': self.ticker,
            'name': self.name,
            'exchange': self.exchange,
            'timezone': self.timezone,
            'market_cap': float(self.market_cap) if self.market_cap else None,
            'sector': self.sector,
            'is_active': self.is_active,
            'source': self.source,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }


class TickerRotation(db.Model):
    """Track which tickers have been analyzed to ensure rotation"""
    __tablename__ = 'ticker_rotation'

    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    timezone = db.Column(db.String(50), nullable=False, index=True)
    trader_id = db.Column(db.Integer, db.ForeignKey('traders.id'), nullable=True, index=True)  # NULL = all traders

    # Tracking
    last_analyzed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    analysis_count = db.Column(db.Integer, nullable=False, default=0)

    # Unique constraint per ticker-timezone-trader combination
    __table_args__ = (
        db.UniqueConstraint('ticker', 'timezone', 'trader_id', name='unique_ticker_timezone_trader'),
    )

    def __repr__(self):
        return f'<TickerRotation {self.ticker} ({self.timezone}): analyzed {self.analysis_count} times>'

    def to_dict(self):
        """Convert ticker rotation entry to dictionary"""
        return {
            'id': self.id,
            'ticker': self.ticker,
            'timezone': self.timezone,
            'trader_id': self.trader_id,
            'last_analyzed_at': self.last_analyzed_at.isoformat(),
            'analysis_count': self.analysis_count
        }
