"""
Pydantic Schemas for Type Safety and JSON Serialization

These models provide:
- Automatic Decimal to float conversion for JSON responses
- Type validation and safety
- Clear API response contracts
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_serializer


class TraderPerformance(BaseModel):
    """Portfolio health check performance data"""
    trader_id: int
    trader_name: str
    cash_balance: Decimal
    portfolio_value: Decimal
    total_value: Decimal
    initial_balance: Decimal
    profit_loss: Decimal
    profit_loss_pct: Decimal
    positions: int

    @field_serializer('cash_balance', 'portfolio_value', 'total_value',
                      'initial_balance', 'profit_loss', 'profit_loss_pct')
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization"""
        return float(value)


class PortfolioHealthCheckResult(BaseModel):
    """Portfolio health check response"""
    status: str = "success"
    timestamp: str
    traders: List[TraderPerformance]


class TradingDecision(BaseModel):
    """Trading analysis decision"""
    action: str  # buy | sell | hold
    confidence: int
    current_price: Decimal
    signals: List[str]
    score: int
    threshold: int
    ticker: str

    @field_serializer('current_price')
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization"""
        return float(value)


class TradeExecution(BaseModel):
    """Trade execution result"""
    trader_id: int
    trader_name: str
    ticker: str
    action: str
    quantity: int
    price: Decimal
    total_amount: Decimal
    balance_after: Decimal
    executed_at: str
    notes: Optional[str] = None

    @field_serializer('price', 'total_amount', 'balance_after')
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization"""
        return float(value)


class TradingSessionResult(BaseModel):
    """Result of a trading session"""
    status: str
    timezone: str
    time_of_day: str
    traders_processed: int
    trades_executed: int
    api_calls_made: Optional[int] = None
    api_usage: Optional[dict] = None
    trades: List[TradeExecution]


class PortfolioItem(BaseModel):
    """Individual portfolio holding"""
    ticker: str
    quantity: int
    average_price: Decimal
    total_cost: Decimal
    current_price: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    unrealized_pl: Optional[Decimal] = None
    unrealized_pl_pct: Optional[Decimal] = None

    @field_serializer('average_price', 'total_cost', 'current_price',
                      'current_value', 'unrealized_pl', 'unrealized_pl_pct')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[float]:
        """Convert Decimal to float for JSON serialization"""
        return float(value) if value is not None else None


class TraderStats(BaseModel):
    """Trader statistics and performance metrics"""
    id: int
    name: str
    status: str
    current_balance: Decimal
    portfolio_value: Decimal
    total_value: Decimal
    initial_balance: Decimal
    profit_loss: Decimal
    profit_loss_percentage: Decimal
    unrealized_pl: Decimal
    buy_trades: int
    sell_trades: int
    win_rate: Decimal
    risk_tolerance: str
    trading_timezone: Optional[str] = None
    trading_ethos: Optional[str] = None

    @field_serializer('current_balance', 'portfolio_value', 'total_value',
                      'initial_balance', 'profit_loss', 'profit_loss_percentage',
                      'unrealized_pl', 'win_rate')
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization"""
        return float(value)


class ApiUsageStats(BaseModel):
    """API usage statistics"""
    calls: int
    limit: int
    remaining: int
    percentage_used: Decimal
    reset_time: Optional[str] = None

    @field_serializer('percentage_used')
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization"""
        return float(value)
