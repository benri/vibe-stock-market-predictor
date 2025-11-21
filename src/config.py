"""
Trading Configuration
Centralized configuration for trading parameters, risk management, and watchlists
"""
from typing import Dict, List


class TradingConfig:
    """Central configuration for trading system"""

    # ========== Risk Management Configuration ==========

    RISK_PROFILES = {
        'low': {
            'buy_threshold': 35,        # Score needed to trigger buy
            'sell_threshold': -35,      # Score needed to trigger sell
            'position_size': 0.05,      # 5% of balance per trade
            'description': 'Conservative trading with high confidence thresholds'
        },
        'medium': {
            'buy_threshold': 18,
            'sell_threshold': -18,
            'position_size': 0.10,      # 10% of balance per trade
            'description': 'Balanced risk/reward approach'
        },
        'high': {
            'buy_threshold': 15,
            'sell_threshold': -15,
            'position_size': 0.15,      # 15% of balance per trade
            'description': 'Aggressive trading with lower confidence thresholds'
        }
    }

    # ========== Watchlists by Timezone/Exchange ==========

    WATCHLISTS = {
        'America/New_York': {
            'tickers': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META'],
            'exchange': 'NYSE/NASDAQ',
            'timezone': 'America/New_York',
            'market_hours': '9:30 AM - 4:00 PM EST'
        },
        'Europe/London': {
            'tickers': ['BARC.L', 'HSBA.L', 'BP.L', 'SHEL.L', 'VOD.L', 'GSK.L', 'AZN.L'],
            'exchange': 'LSE',
            'timezone': 'Europe/London',
            'market_hours': '8:00 AM - 4:30 PM GMT'
        },
        'Asia/Tokyo': {
            'tickers': ['7203.T', '6758.T', '9984.T', '8306.T', '9432.T', '6861.T', '6501.T'],
            'exchange': 'TSE',
            'timezone': 'Asia/Tokyo',
            'market_hours': '9:00 AM - 3:00 PM JST'
        }
    }

    # Default watchlist for unknown timezones
    DEFAULT_WATCHLIST_TIMEZONE = 'America/New_York'

    # ========== Technical Indicator Parameters ==========

    INDICATOR_PARAMS = {
        'sma_short_window': 20,
        'sma_long_window': 50,
        'ema_short_span': 12,
        'ema_long_span': 26,
        'macd_signal_span': 9,
        'rsi_window': 14,
        'momentum_periods': 10,
        'min_data_points': 50  # Minimum data points for reliable indicators
    }

    # ========== Signal Scoring Weights ==========

    SIGNAL_SCORES = {
        'strong_trend': 20,         # Strong uptrend/downtrend (price vs both MAs)
        'weak_trend': 10,           # Weak trend (price vs short MA)
        'rsi_extreme': 15,          # Oversold (<30) or Overbought (>70)
        'macd_crossover': 15,       # MACD bullish/bearish crossover
        'strong_momentum': 10       # Strong positive/negative momentum (>5% or <-5%)
    }

    # RSI thresholds
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    RSI_NEUTRAL_LOWER = 40
    RSI_NEUTRAL_UPPER = 60

    # Momentum thresholds
    MOMENTUM_STRONG_POSITIVE = 5.0
    MOMENTUM_STRONG_NEGATIVE = -5.0

    # ========== Display Signal Thresholds ==========

    DISPLAY_THRESHOLDS = {
        'strong_buy': 30,
        'buy': 15,
        'strong_sell': -30,
        'sell': -15
    }

    # ========== Trading Schedule (for GitHub Actions) ==========

    TRADING_SCHEDULE = {
        'morning': '09:45',      # After market open
        'midday': '12:30',       # Midday session
        'afternoon': '15:00',    # Before market close
        'health_check': '16:30'  # After market close
    }

    # ========== Helper Methods ==========

    @classmethod
    def get_risk_profile(cls, risk_tolerance: str) -> Dict:
        """
        Get risk profile configuration

        Args:
            risk_tolerance: 'low', 'medium', or 'high'

        Returns:
            Dictionary with risk profile settings
        """
        return cls.RISK_PROFILES.get(risk_tolerance, cls.RISK_PROFILES['medium'])

    @classmethod
    def get_position_size(cls, risk_tolerance: str) -> float:
        """
        Get position size percentage for a given risk tolerance

        Args:
            risk_tolerance: 'low', 'medium', or 'high'

        Returns:
            Float representing percentage of balance (0.05 = 5%)
        """
        profile = cls.get_risk_profile(risk_tolerance)
        return profile['position_size']

    @classmethod
    def get_buy_threshold(cls, risk_tolerance: str) -> int:
        """
        Get buy threshold score for a given risk tolerance

        Args:
            risk_tolerance: 'low', 'medium', or 'high'

        Returns:
            Integer threshold score
        """
        profile = cls.get_risk_profile(risk_tolerance)
        return profile['buy_threshold']

    @classmethod
    def get_sell_threshold(cls, risk_tolerance: str) -> int:
        """
        Get sell threshold score for a given risk tolerance

        Args:
            risk_tolerance: 'low', 'medium', or 'high'

        Returns:
            Integer threshold score
        """
        profile = cls.get_risk_profile(risk_tolerance)
        return profile['sell_threshold']

    @classmethod
    def get_watchlist(cls, timezone: str) -> List[str]:
        """
        Get watchlist for a given timezone

        Args:
            timezone: Timezone identifier (e.g., 'America/New_York')

        Returns:
            List of ticker symbols
        """
        watchlist_config = cls.WATCHLISTS.get(
            timezone,
            cls.WATCHLISTS[cls.DEFAULT_WATCHLIST_TIMEZONE]
        )
        return watchlist_config['tickers']

    @classmethod
    def get_all_tickers(cls) -> List[str]:
        """
        Get all unique tickers across all watchlists

        Returns:
            List of all unique ticker symbols
        """
        all_tickers = set()
        for watchlist_config in cls.WATCHLISTS.values():
            all_tickers.update(watchlist_config['tickers'])
        return sorted(list(all_tickers))

    @classmethod
    def get_supported_timezones(cls) -> List[str]:
        """
        Get list of supported timezone identifiers

        Returns:
            List of timezone strings
        """
        return list(cls.WATCHLISTS.keys())
