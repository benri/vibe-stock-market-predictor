"""
Ticker Source Service

Fetches ticker lists from external non-rate-limited sources like Wikipedia
and updates the ticker pool database.
"""

import logging
import pandas as pd
import requests
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class TickerSourceService:
    """Service for fetching ticker lists from external sources"""

    @staticmethod
    def fetch_sp500_tickers() -> List[Dict[str, any]]:
        """
        Fetch S&P 500 constituent list from Wikipedia

        Returns:
            List of dictionaries with ticker info (ticker, name, sector)
        """
        try:
            logger.info("Fetching S&P 500 tickers from Wikipedia...")
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

            # Read HTML tables from Wikipedia
            tables = pd.read_html(url)
            df = tables[0]  # First table contains the S&P 500 list

            tickers = []
            for _, row in df.iterrows():
                ticker_info = {
                    'ticker': row['Symbol'].replace('.', '-'),  # Fix ticker format for Yahoo Finance
                    'name': row['Security'],
                    'sector': row['GICS Sector'] if 'GICS Sector' in df.columns else None,
                    'exchange': 'NYSE/NASDAQ',
                    'timezone': 'America/New_York',
                    'source': 'sp500'
                }
                tickers.append(ticker_info)

            logger.info(f"✅ Fetched {len(tickers)} S&P 500 tickers")
            return tickers

        except Exception as e:
            logger.error(f"❌ Error fetching S&P 500 tickers: {e}")
            return []

    @staticmethod
    def fetch_ftse100_tickers() -> List[Dict[str, any]]:
        """
        Fetch FTSE 100 constituent list from Wikipedia

        Returns:
            List of dictionaries with ticker info (ticker, name, sector)
        """
        try:
            logger.info("Fetching FTSE 100 tickers from Wikipedia...")
            url = 'https://en.wikipedia.org/wiki/FTSE_100_Index'

            # Read HTML tables from Wikipedia
            tables = pd.read_html(url)

            # Find the table with "Company" and "Ticker" columns
            df = None
            for table in tables:
                if 'Company' in table.columns and 'Ticker' in table.columns:
                    df = table
                    break

            if df is None:
                logger.warning("Could not find FTSE 100 constituents table")
                return []

            tickers = []
            for _, row in df.iterrows():
                ticker_symbol = row['Ticker']
                # Add .L suffix for London Stock Exchange if not present
                if not ticker_symbol.endswith('.L'):
                    ticker_symbol = f"{ticker_symbol}.L"

                ticker_info = {
                    'ticker': ticker_symbol,
                    'name': row['Company'],
                    'sector': row['FTSE Industry Classification Benchmark sector'] if 'FTSE Industry Classification Benchmark sector' in df.columns else None,
                    'exchange': 'LSE',
                    'timezone': 'Europe/London',
                    'source': 'ftse100'
                }
                tickers.append(ticker_info)

            logger.info(f"✅ Fetched {len(tickers)} FTSE 100 tickers")
            return tickers

        except Exception as e:
            logger.error(f"❌ Error fetching FTSE 100 tickers: {e}")
            return []

    @staticmethod
    def fetch_nikkei225_tickers() -> List[Dict[str, any]]:
        """
        Fetch Nikkei 225 constituent list from Wikipedia

        Returns:
            List of dictionaries with ticker info (ticker, name, sector)
        """
        try:
            logger.info("Fetching Nikkei 225 tickers from Wikipedia...")
            url = 'https://en.wikipedia.org/wiki/Nikkei_225'

            # Read HTML tables from Wikipedia
            tables = pd.read_html(url)

            # Find the table with company listings
            df = None
            for table in tables:
                if 'Code' in table.columns and 'Company' in table.columns:
                    df = table
                    break

            if df is None:
                logger.warning("Could not find Nikkei 225 constituents table")
                return []

            tickers = []
            for _, row in df.iterrows():
                ticker_code = str(row['Code'])
                # Add .T suffix for Tokyo Stock Exchange if not present
                if not ticker_code.endswith('.T'):
                    ticker_code = f"{ticker_code}.T"

                ticker_info = {
                    'ticker': ticker_code,
                    'name': row['Company'],
                    'sector': row['Sector'] if 'Sector' in df.columns else None,
                    'exchange': 'TSE',
                    'timezone': 'Asia/Tokyo',
                    'source': 'nikkei225'
                }
                tickers.append(ticker_info)

            logger.info(f"✅ Fetched {len(tickers)} Nikkei 225 tickers")
            return tickers

        except Exception as e:
            logger.error(f"❌ Error fetching Nikkei 225 tickers: {e}")
            return []

    @staticmethod
    def refresh_ticker_pools(db) -> Dict[str, int]:
        """
        Refresh all ticker pools from external sources

        Args:
            db: SQLAlchemy database session

        Returns:
            Dictionary with counts of tickers added/updated per source
        """
        from models import TickerPool

        results = {
            'sp500': 0,
            'ftse100': 0,
            'nikkei225': 0,
            'errors': []
        }

        try:
            # Fetch from all sources
            sources = [
                ('sp500', TickerSourceService.fetch_sp500_tickers),
                ('ftse100', TickerSourceService.fetch_ftse100_tickers),
                ('nikkei225', TickerSourceService.fetch_nikkei225_tickers),
            ]

            for source_name, fetch_func in sources:
                try:
                    logger.info(f"Refreshing {source_name} ticker pool...")
                    tickers = fetch_func()

                    for ticker_info in tickers:
                        # Check if ticker already exists
                        existing = TickerPool.query.filter_by(
                            ticker=ticker_info['ticker'],
                            exchange=ticker_info['exchange']
                        ).first()

                        if existing:
                            # Update existing entry
                            existing.name = ticker_info['name']
                            existing.sector = ticker_info['sector']
                            existing.source = ticker_info['source']
                            existing.is_active = True
                            existing.last_updated = datetime.utcnow()
                        else:
                            # Create new entry
                            new_ticker = TickerPool(
                                ticker=ticker_info['ticker'],
                                name=ticker_info['name'],
                                exchange=ticker_info['exchange'],
                                timezone=ticker_info['timezone'],
                                sector=ticker_info['sector'],
                                source=ticker_info['source'],
                                is_active=True
                            )
                            db.session.add(new_ticker)
                            results[source_name] += 1

                    db.session.commit()
                    logger.info(f"✅ Refreshed {source_name}: {results[source_name]} new tickers")

                except Exception as e:
                    error_msg = f"Error refreshing {source_name}: {e}"
                    logger.error(f"❌ {error_msg}")
                    results['errors'].append(error_msg)
                    db.session.rollback()

            return results

        except Exception as e:
            logger.error(f"❌ Error during ticker pool refresh: {e}")
            db.session.rollback()
            results['errors'].append(str(e))
            return results

    @staticmethod
    def validate_ticker_format(ticker: str, exchange: str) -> bool:
        """
        Validate ticker format for a given exchange

        Args:
            ticker: Ticker symbol
            exchange: Exchange name (NYSE/NASDAQ, LSE, TSE)

        Returns:
            True if valid, False otherwise
        """
        if not ticker or len(ticker) < 1:
            return False

        if exchange == 'LSE':
            # London stocks should end with .L
            return ticker.endswith('.L')
        elif exchange == 'TSE':
            # Tokyo stocks should end with .T
            return ticker.endswith('.T')
        elif exchange in ['NYSE', 'NASDAQ', 'NYSE/NASDAQ']:
            # US stocks should not have exchange suffix
            return '.' not in ticker or ticker.endswith(('.A', '.B'))
        else:
            return True

    @staticmethod
    def get_ticker_pool_stats(db) -> Dict[str, any]:
        """
        Get statistics about the ticker pool

        Args:
            db: SQLAlchemy database session

        Returns:
            Dictionary with statistics
        """
        from models import TickerPool
        from sqlalchemy import func

        try:
            total_tickers = TickerPool.query.count()
            active_tickers = TickerPool.query.filter_by(is_active=True).count()

            # Count by exchange
            exchange_counts = db.session.query(
                TickerPool.exchange,
                func.count(TickerPool.id)
            ).filter_by(is_active=True).group_by(TickerPool.exchange).all()

            # Count by timezone
            timezone_counts = db.session.query(
                TickerPool.timezone,
                func.count(TickerPool.id)
            ).filter_by(is_active=True).group_by(TickerPool.timezone).all()

            # Count by source
            source_counts = db.session.query(
                TickerPool.source,
                func.count(TickerPool.id)
            ).filter_by(is_active=True).group_by(TickerPool.source).all()

            return {
                'total_tickers': total_tickers,
                'active_tickers': active_tickers,
                'inactive_tickers': total_tickers - active_tickers,
                'by_exchange': {ex: count for ex, count in exchange_counts},
                'by_timezone': {tz: count for tz, count in timezone_counts},
                'by_source': {src: count for src, count in source_counts}
            }

        except Exception as e:
            logger.error(f"Error getting ticker pool stats: {e}")
            return {}
