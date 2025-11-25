"""
Watchlist Service

Manages dynamic watchlists with portfolio-first prioritization,
random rotation, and custom watchlist support.
"""

import logging
import random
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class WatchlistService:
    """Service for managing trader watchlists with priority queue logic"""

    @staticmethod
    def get_priority_tickers(trader_id: int, timezone: str, db, limit: int = 6) -> List[str]:
        """
        Get priority tickers for a trader with portfolio-first approach

        Priority:
        1. Tickers currently in portfolio (always included)
        2. Custom watchlist (if trader has use_custom_watchlist=True)
        3. Random selection from timezone-based ticker pool

        Args:
            trader_id: ID of the trader
            timezone: Trading timezone (America/New_York, Europe/London, Asia/Tokyo)
            db: SQLAlchemy database session
            limit: Maximum number of discovery tickers (excluding portfolio)

        Returns:
            List of ticker symbols to analyze
        """
        from models import Trader, Portfolio, TickerPool
        from src.services.trading_service import TradingService

        try:
            trader = Trader.query.get(trader_id)
            if not trader:
                logger.error(f"Trader {trader_id} not found")
                return []

            # Priority 1: Get portfolio tickers (always included)
            portfolio_tickers = TradingService.get_trader_portfolio_tickers(trader_id)
            logger.info(f"Trader {trader.name}: {len(portfolio_tickers)} portfolio holdings")

            # Use trader's custom watchlist size if set, otherwise use limit
            discovery_limit = trader.watchlist_size if trader.watchlist_size else limit

            # Priority 2: Check if trader has custom watchlist
            if trader.use_custom_watchlist and trader.custom_watchlist:
                logger.info(f"Trader {trader.name}: Using custom watchlist ({len(trader.custom_watchlist)} tickers)")
                # Get random sample from custom watchlist (excluding portfolio tickers)
                available_custom = [t for t in trader.custom_watchlist if t not in portfolio_tickers]
                discovery_tickers = random.sample(
                    available_custom,
                    min(discovery_limit, len(available_custom))
                )
            else:
                # Priority 3: Get discovery tickers from ticker pool (random selection)
                logger.info(f"Trader {trader.name}: Using timezone-based ticker pool ({timezone})")
                discovery_tickers = WatchlistService._get_random_discovery_tickers(
                    trader_id=trader_id,
                    timezone=timezone,
                    db=db,
                    limit=discovery_limit,
                    exclude_tickers=portfolio_tickers
                )

            # Combine portfolio + discovery tickers
            final_tickers = list(set(portfolio_tickers + discovery_tickers))

            logger.info(f"Trader {trader.name}: Analyzing {len(final_tickers)} tickers "
                       f"({len(portfolio_tickers)} portfolio + {len(discovery_tickers)} discovery)")

            return final_tickers

        except Exception as e:
            logger.error(f"Error getting priority tickers for trader {trader_id}: {e}")
            return []

    @staticmethod
    def _get_random_discovery_tickers(
        trader_id: int,
        timezone: str,
        db,
        limit: int,
        exclude_tickers: List[str] = None
    ) -> List[str]:
        """
        Get random discovery tickers from the ticker pool

        Args:
            trader_id: ID of the trader
            timezone: Trading timezone
            db: SQLAlchemy database session
            limit: Maximum number of tickers to return
            exclude_tickers: List of tickers to exclude (e.g., portfolio holdings)

        Returns:
            List of ticker symbols
        """
        from models import TickerPool

        try:
            exclude_tickers = exclude_tickers or []

            # Get all active tickers for the timezone
            query = TickerPool.query.filter_by(
                timezone=timezone,
                is_active=True
            )

            # Exclude portfolio tickers
            if exclude_tickers:
                query = query.filter(TickerPool.ticker.notin_(exclude_tickers))

            available_tickers = query.all()

            if not available_tickers:
                logger.warning(f"No tickers available for timezone {timezone}")
                return []

            # Random selection
            sample_size = min(limit, len(available_tickers))
            selected = random.sample(available_tickers, sample_size)
            ticker_symbols = [t.ticker for t in selected]

            # Track rotation
            WatchlistService._track_ticker_rotation(trader_id, timezone, ticker_symbols, db)

            logger.info(f"Selected {len(ticker_symbols)} random tickers from pool of {len(available_tickers)}")
            return ticker_symbols

        except Exception as e:
            logger.error(f"Error getting random discovery tickers: {e}")
            return []

    @staticmethod
    def _track_ticker_rotation(trader_id: int, timezone: str, tickers: List[str], db):
        """
        Track which tickers were analyzed for rotation tracking

        Args:
            trader_id: ID of the trader
            timezone: Trading timezone
            tickers: List of ticker symbols that were analyzed
            db: SQLAlchemy database session
        """
        from models import TickerRotation

        try:
            for ticker in tickers:
                # Check if rotation record exists
                rotation = TickerRotation.query.filter_by(
                    ticker=ticker,
                    timezone=timezone,
                    trader_id=trader_id
                ).first()

                if rotation:
                    # Update existing record
                    rotation.last_analyzed_at = datetime.utcnow()
                    rotation.analysis_count += 1
                else:
                    # Create new record
                    rotation = TickerRotation(
                        ticker=ticker,
                        timezone=timezone,
                        trader_id=trader_id,
                        last_analyzed_at=datetime.utcnow(),
                        analysis_count=1
                    )
                    db.session.add(rotation)

            db.session.commit()
            logger.debug(f"Tracked rotation for {len(tickers)} tickers")

        except Exception as e:
            logger.error(f"Error tracking ticker rotation: {e}")
            db.session.rollback()

    @staticmethod
    def get_trader_watchlist_pool(trader_id: int, timezone: str) -> List[Dict[str, any]]:
        """
        Get the available ticker pool for a trader

        Args:
            trader_id: ID of the trader
            timezone: Trading timezone

        Returns:
            List of ticker dictionaries with info
        """
        from models import Trader, TickerPool

        try:
            trader = Trader.query.get(trader_id)
            if not trader:
                return []

            # If trader has custom watchlist and it's enabled, return that
            if trader.use_custom_watchlist and trader.custom_watchlist:
                # Get ticker info for custom watchlist
                tickers = TickerPool.query.filter(
                    TickerPool.ticker.in_(trader.custom_watchlist)
                ).all()
                return [t.to_dict() for t in tickers]
            else:
                # Return timezone-based pool
                tickers = TickerPool.query.filter_by(
                    timezone=timezone,
                    is_active=True
                ).all()
                return [t.to_dict() for t in tickers]

        except Exception as e:
            logger.error(f"Error getting watchlist pool for trader {trader_id}: {e}")
            return []

    @staticmethod
    def get_analysis_history(trader_id: int, timezone: str, limit: int = 50) -> List[Dict[str, any]]:
        """
        Get recent analysis history for a trader

        Args:
            trader_id: ID of the trader
            timezone: Trading timezone
            limit: Maximum number of records to return

        Returns:
            List of rotation records
        """
        from models import TickerRotation

        try:
            records = TickerRotation.query.filter_by(
                trader_id=trader_id,
                timezone=timezone
            ).order_by(TickerRotation.last_analyzed_at.desc()).limit(limit).all()

            return [r.to_dict() for r in records]

        except Exception as e:
            logger.error(f"Error getting analysis history for trader {trader_id}: {e}")
            return []

    @staticmethod
    def set_custom_watchlist(trader_id: int, tickers: List[str], db) -> bool:
        """
        Set custom watchlist for a trader

        Args:
            trader_id: ID of the trader
            tickers: List of ticker symbols
            db: SQLAlchemy database session

        Returns:
            True if successful, False otherwise
        """
        from models import Trader

        try:
            trader = Trader.query.get(trader_id)
            if not trader:
                logger.error(f"Trader {trader_id} not found")
                return False

            # Validate tickers (basic validation)
            if not isinstance(tickers, list):
                logger.error("Tickers must be a list")
                return False

            # Remove duplicates and empty strings
            unique_tickers = list(set([t.strip().upper() for t in tickers if t.strip()]))

            trader.custom_watchlist = unique_tickers
            trader.use_custom_watchlist = True  # Enable custom watchlist
            db.session.commit()

            logger.info(f"Set custom watchlist for trader {trader.name}: {len(unique_tickers)} tickers")
            return True

        except Exception as e:
            logger.error(f"Error setting custom watchlist for trader {trader_id}: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def clear_custom_watchlist(trader_id: int, db) -> bool:
        """
        Clear custom watchlist and revert to timezone-based pool

        Args:
            trader_id: ID of the trader
            db: SQLAlchemy database session

        Returns:
            True if successful, False otherwise
        """
        from models import Trader

        try:
            trader = Trader.query.get(trader_id)
            if not trader:
                logger.error(f"Trader {trader_id} not found")
                return False

            trader.custom_watchlist = None
            trader.use_custom_watchlist = False
            db.session.commit()

            logger.info(f"Cleared custom watchlist for trader {trader.name}")
            return True

        except Exception as e:
            logger.error(f"Error clearing custom watchlist for trader {trader_id}: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def get_watchlist_stats(db) -> Dict[str, any]:
        """
        Get statistics about watchlist usage

        Args:
            db: SQLAlchemy database session

        Returns:
            Dictionary with statistics
        """
        from models import Trader, TickerRotation, TickerPool
        from sqlalchemy import func

        try:
            total_traders = Trader.query.count()
            custom_watchlist_traders = Trader.query.filter_by(use_custom_watchlist=True).count()

            # Most analyzed tickers
            most_analyzed = db.session.query(
                TickerRotation.ticker,
                func.sum(TickerRotation.analysis_count).label('total_analyses')
            ).group_by(TickerRotation.ticker).order_by(func.sum(TickerRotation.analysis_count).desc()).limit(10).all()

            # Rotation coverage (tickers that have been analyzed at least once)
            total_pool_tickers = TickerPool.query.filter_by(is_active=True).count()
            analyzed_tickers = db.session.query(func.count(func.distinct(TickerRotation.ticker))).scalar()

            return {
                'total_traders': total_traders,
                'custom_watchlist_traders': custom_watchlist_traders,
                'timezone_based_traders': total_traders - custom_watchlist_traders,
                'total_pool_tickers': total_pool_tickers,
                'analyzed_tickers': analyzed_tickers,
                'coverage_percentage': (analyzed_tickers / total_pool_tickers * 100) if total_pool_tickers > 0 else 0,
                'most_analyzed': [{'ticker': t, 'count': c} for t, c in most_analyzed]
            }

        except Exception as e:
            logger.error(f"Error getting watchlist stats: {e}")
            return {}
