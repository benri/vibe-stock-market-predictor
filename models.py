from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Enum
import enum

db = SQLAlchemy()


class TraderStatus(enum.Enum):
    """Status of a trader"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class TradeAction(enum.Enum):
    """Type of trade action"""
    BUY = "buy"
    SELL = "sell"


class Trader(db.Model):
    """Machine trader with virtual account balance"""
    __tablename__ = 'traders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    status = db.Column(Enum(TraderStatus), default=TraderStatus.ACTIVE, nullable=False)

    # Virtual account balance
    initial_balance = db.Column(db.Numeric(12, 2), nullable=False, default=10000.00)
    current_balance = db.Column(db.Numeric(12, 2), nullable=False, default=10000.00)

    # Trading strategy parameters
    strategy_name = db.Column(db.String(50), nullable=False, default='default')
    risk_tolerance = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high
    trading_ethos = db.Column(db.Text, nullable=True)  # Free-form text for trading philosophy (bullish, bearish, etc.)
    trading_timezone = db.Column(db.String(50), nullable=False, default='America/New_York')  # Trading timezone (NYSE, LSE, TSE, etc.)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_trade_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    trades = db.relationship('Trade', back_populates='trader', lazy='dynamic', cascade='all, delete-orphan')
    portfolio = db.relationship('Portfolio', back_populates='trader', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Trader {self.name} - ${self.current_balance}>'

    def to_dict(self):
        """Convert trader to dictionary with market-value based P/L"""
        portfolio_items = self.portfolio.all()

        # Calculate portfolio value using cached current_price if available, else cost basis
        portfolio_market_value = 0
        portfolio_cost_basis = 0
        for item in portfolio_items:
            cost_basis = float(item.total_cost)
            portfolio_cost_basis += cost_basis

            if item.current_price and item.quantity > 0:
                # Use cached market price
                market_value = float(item.current_price) * item.quantity
                portfolio_market_value += market_value
            else:
                # Fallback to cost basis if no current price
                portfolio_market_value += cost_basis

        total_value = float(self.current_balance) + portfolio_market_value
        unrealized_pl = portfolio_market_value - portfolio_cost_basis

        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'initial_balance': float(self.initial_balance),
            'current_balance': float(self.current_balance),
            'portfolio_value': portfolio_market_value,
            'portfolio_cost_basis': portfolio_cost_basis,
            'unrealized_pl': unrealized_pl,
            'total_value': total_value,
            'strategy_name': self.strategy_name,
            'risk_tolerance': self.risk_tolerance,
            'trading_ethos': self.trading_ethos,
            'trading_timezone': self.trading_timezone,
            'created_at': self.created_at.isoformat(),
            'last_trade_at': self.last_trade_at.isoformat() if self.last_trade_at else None,
            'total_trades': self.trades.count(),
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
    action = db.Column(Enum(TradeAction), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)

    # Account balance after trade
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)

    # Trading signals that led to this trade
    rsi = db.Column(db.Numeric(5, 2), nullable=True)
    macd = db.Column(db.Numeric(10, 2), nullable=True)
    sma_20 = db.Column(db.Numeric(10, 2), nullable=True)
    sma_50 = db.Column(db.Numeric(10, 2), nullable=True)
    recommendation = db.Column(db.String(20), nullable=True)
    confidence = db.Column(db.Integer, nullable=True)

    # Notes
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
            'confidence': self.confidence,
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

    # Market value (updated periodically)
    current_price = db.Column(db.Numeric(10, 2), nullable=True)  # Latest market price
    last_price_update = db.Column(db.DateTime, nullable=True)    # When price was last updated

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
