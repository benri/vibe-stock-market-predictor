"""
Trading Service
Handles trade execution, position management, and portfolio updates
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, List, Any
from models import db, Trade, Portfolio, TradeAction
from app.config import TradingConfig

logger = logging.getLogger(__name__)


class TradingService:
    """Service for executing trades and managing positions"""

    def __init__(self, db_session=None):
        """
        Initialize Trading Service

        Args:
            db_session: Optional database session (defaults to global db.session)
        """
        self.db = db_session or db.session
        self.config = TradingConfig

    def execute_buy_trade(self, trader, ticker: str, decision: Dict[str, Any],
                         time_of_day: str = 'automated') -> Optional[Dict[str, Any]]:
        """
        Execute a buy trade for a trader

        Args:
            trader: Trader model instance
            ticker: Stock ticker symbol
            decision: Dictionary with 'current_price', 'rsi', 'macd', 'sma_20', 'sma_50',
                     'confidence', 'signals'
            time_of_day: Description of when trade is being executed (e.g., 'morning', 'midday')

        Returns:
            Dictionary with trade details, or None if trade not executed
        """
        try:
            # Calculate position size
            position_size = self.config.get_position_size(trader.risk_tolerance)
            max_investment = float(trader.current_balance) * position_size
            quantity = int(max_investment / decision['current_price'])

            # Validate sufficient funds and quantity
            if quantity <= 0:
                logger.info(f"{trader.name}: Insufficient funds for {ticker} buy")
                return None

            total_cost = quantity * decision['current_price']
            if float(trader.current_balance) < total_cost:
                logger.info(f"{trader.name}: Insufficient balance for {ticker} buy")
                return None

            # Deduct from balance
            trader.current_balance -= Decimal(str(total_cost))

            # Update or create portfolio item
            portfolio_item = Portfolio.query.filter_by(
                trader_id=trader.id,
                ticker=ticker
            ).first()

            if portfolio_item:
                # Add to existing position
                new_total_cost = portfolio_item.total_cost + total_cost
                new_quantity = portfolio_item.quantity + quantity
                portfolio_item.average_price = new_total_cost / new_quantity
                portfolio_item.total_cost = new_total_cost
                portfolio_item.quantity = new_quantity
                portfolio_item.last_updated_at = datetime.utcnow()
            else:
                # Create new position
                portfolio_item = Portfolio(
                    trader_id=trader.id,
                    ticker=ticker,
                    quantity=quantity,
                    average_price=decision['current_price'],
                    total_cost=total_cost,
                    first_purchased_at=datetime.utcnow()
                )
                self.db.add(portfolio_item)

            # Create trade record
            trade = Trade(
                trader_id=trader.id,
                ticker=ticker,
                action=TradeAction.BUY,
                quantity=quantity,
                price=decision['current_price'],
                total_amount=total_cost,
                balance_after=trader.current_balance,
                rsi=decision.get('rsi'),
                macd=decision.get('macd'),
                sma_20=decision.get('sma_20'),
                sma_50=decision.get('sma_50'),
                recommendation='BUY',
                confidence=decision.get('confidence', 50),
                notes=f"Automated {time_of_day} trade: {', '.join(decision.get('signals', []))}"
            )

            trader.last_trade_at = datetime.utcnow()
            self.db.add(trade)

            logger.info(f"{trader.name} bought {quantity} shares of {ticker} at ${decision['current_price']}")

            return {
                'trader': trader.name,
                'action': 'BUY',
                'ticker': ticker,
                'quantity': quantity,
                'price': decision['current_price'],
                'total_amount': total_cost
            }

        except Exception as e:
            logger.error(f"Error executing buy trade for {trader.name}/{ticker}: {str(e)}")
            return None

    def execute_sell_trade(self, trader, ticker: str, decision: Dict[str, Any],
                          time_of_day: str = 'automated') -> Optional[Dict[str, Any]]:
        """
        Execute a sell trade for a trader

        Args:
            trader: Trader model instance
            ticker: Stock ticker symbol
            decision: Dictionary with 'current_price', 'rsi', 'macd', 'sma_20', 'sma_50',
                     'confidence', 'signals'
            time_of_day: Description of when trade is being executed

        Returns:
            Dictionary with trade details, or None if trade not executed
        """
        try:
            # Find portfolio item
            portfolio_item = Portfolio.query.filter_by(
                trader_id=trader.id,
                ticker=ticker
            ).first()

            if not portfolio_item or portfolio_item.quantity <= 0:
                logger.info(f"{trader.name}: No position in {ticker} to sell")
                return None

            # Determine sell quantity (half position or all if small)
            quantity = portfolio_item.quantity // 2 if portfolio_item.quantity > 2 else portfolio_item.quantity
            price = decision['current_price']
            total_proceeds = quantity * price

            # Add proceeds to balance
            trader.current_balance += Decimal(str(total_proceeds))

            # Update portfolio
            portfolio_item.quantity -= quantity
            portfolio_item.total_cost -= (portfolio_item.average_price * quantity)
            portfolio_item.last_updated_at = datetime.utcnow()

            # Delete portfolio item if position fully closed
            if portfolio_item.quantity == 0:
                self.db.delete(portfolio_item)

            # Create trade record
            trade = Trade(
                trader_id=trader.id,
                ticker=ticker,
                action=TradeAction.SELL,
                quantity=quantity,
                price=price,
                total_amount=total_proceeds,
                balance_after=trader.current_balance,
                rsi=decision.get('rsi'),
                macd=decision.get('macd'),
                sma_20=decision.get('sma_20'),
                sma_50=decision.get('sma_50'),
                recommendation='SELL',
                confidence=decision.get('confidence', 50),
                notes=f"Automated {time_of_day} trade: {', '.join(decision.get('signals', []))}"
            )

            trader.last_trade_at = datetime.utcnow()
            self.db.add(trade)

            logger.info(f"{trader.name} sold {quantity} shares of {ticker} at ${price}")

            return {
                'trader': trader.name,
                'action': 'SELL',
                'ticker': ticker,
                'quantity': quantity,
                'price': price,
                'total_amount': total_proceeds
            }

        except Exception as e:
            logger.error(f"Error executing sell trade for {trader.name}/{ticker}: {str(e)}")
            return None

    def get_trader_portfolio_tickers(self, trader_id: int) -> List[str]:
        """
        Get list of tickers in trader's portfolio

        Args:
            trader_id: Trader ID

        Returns:
            List of ticker symbols
        """
        portfolio_items = Portfolio.query.filter_by(trader_id=trader_id).all()
        return [item.ticker for item in portfolio_items if item.quantity > 0]

    def has_position(self, trader_id: int, ticker: str) -> bool:
        """
        Check if trader has a position in a ticker

        Args:
            trader_id: Trader ID
            ticker: Stock ticker symbol

        Returns:
            True if position exists, False otherwise
        """
        portfolio_item = Portfolio.query.filter_by(
            trader_id=trader_id,
            ticker=ticker
        ).first()
        return portfolio_item is not None and portfolio_item.quantity > 0

    def get_position_quantity(self, trader_id: int, ticker: str) -> int:
        """
        Get quantity of shares held in a position

        Args:
            trader_id: Trader ID
            ticker: Stock ticker symbol

        Returns:
            Number of shares, or 0 if no position
        """
        portfolio_item = Portfolio.query.filter_by(
            trader_id=trader_id,
            ticker=ticker
        ).first()
        return portfolio_item.quantity if portfolio_item else 0

    def calculate_position_value(self, trader_id: int, ticker: str, current_price: float) -> float:
        """
        Calculate current value of a position

        Args:
            trader_id: Trader ID
            ticker: Stock ticker symbol
            current_price: Current market price

        Returns:
            Current value of position in dollars
        """
        quantity = self.get_position_quantity(trader_id, ticker)
        return quantity * current_price

    def calculate_position_pl(self, trader_id: int, ticker: str, current_price: float) -> Dict[str, float]:
        """
        Calculate profit/loss for a position

        Args:
            trader_id: Trader ID
            ticker: Stock ticker symbol
            current_price: Current market price

        Returns:
            Dictionary with 'cost_basis', 'current_value', 'profit_loss', 'profit_loss_pct'
        """
        portfolio_item = Portfolio.query.filter_by(
            trader_id=trader_id,
            ticker=ticker
        ).first()

        if not portfolio_item or portfolio_item.quantity == 0:
            return {
                'cost_basis': 0.0,
                'current_value': 0.0,
                'profit_loss': 0.0,
                'profit_loss_pct': 0.0
            }

        cost_basis = portfolio_item.average_price * portfolio_item.quantity
        current_value = current_price * portfolio_item.quantity
        profit_loss = current_value - cost_basis
        profit_loss_pct = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0.0

        return {
            'cost_basis': cost_basis,
            'current_value': current_value,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct
        }
