"""
Technical Indicator Service
Calculates various technical indicators for stock analysis
"""
import pandas as pd
from typing import Optional


class IndicatorService:
    """Service for calculating technical indicators used in trading decisions"""

    # Configuration for indicator parameters
    SMA_SHORT_WINDOW = 20
    SMA_LONG_WINDOW = 50
    EMA_SHORT_SPAN = 12
    EMA_LONG_SPAN = 26
    MACD_SIGNAL_SPAN = 9
    RSI_WINDOW = 14
    MOMENTUM_PERIODS = 10
    MIN_DATA_POINTS = 50  # Minimum data points needed for reliable indicators

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators for trend analysis

        Args:
            df: DataFrame with OHLCV data (must have 'Close' column)

        Returns:
            DataFrame with added indicator columns:
            - SMA_20, SMA_50: Simple Moving Averages
            - EMA_12, EMA_26: Exponential Moving Averages
            - MACD, Signal_Line: MACD and Signal
            - RSI: Relative Strength Index
            - Momentum: Price momentum percentage
        """
        # Simple Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=IndicatorService.SMA_SHORT_WINDOW).mean()
        df['SMA_50'] = df['Close'].rolling(window=IndicatorService.SMA_LONG_WINDOW).mean()

        # Exponential Moving Averages
        df['EMA_12'] = df['Close'].ewm(span=IndicatorService.EMA_SHORT_SPAN, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=IndicatorService.EMA_LONG_SPAN, adjust=False).mean()

        # MACD (Moving Average Convergence Divergence)
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['Signal_Line'] = df['MACD'].ewm(span=IndicatorService.MACD_SIGNAL_SPAN, adjust=False).mean()

        # RSI (Relative Strength Index)
        df = IndicatorService._calculate_rsi(df)

        # Price momentum
        df['Momentum'] = df['Close'].pct_change(periods=IndicatorService.MOMENTUM_PERIODS) * 100

        return df

    @staticmethod
    def _calculate_rsi(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Relative Strength Index (RSI)

        Args:
            df: DataFrame with 'Close' column

        Returns:
            DataFrame with added 'RSI' column
        """
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=IndicatorService.RSI_WINDOW).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=IndicatorService.RSI_WINDOW).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

    @staticmethod
    def has_sufficient_data(df: pd.DataFrame) -> bool:
        """
        Check if DataFrame has sufficient data points for reliable indicators

        Args:
            df: DataFrame to check

        Returns:
            True if sufficient data points, False otherwise
        """
        return len(df) >= IndicatorService.MIN_DATA_POINTS

    @staticmethod
    def get_latest_indicators(df: pd.DataFrame) -> Optional[dict]:
        """
        Get the latest indicator values from a DataFrame

        Args:
            df: DataFrame with calculated indicators

        Returns:
            Dictionary with latest indicator values, or None if insufficient data
        """
        if not IndicatorService.has_sufficient_data(df):
            return None

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        return {
            'close': float(latest['Close']),
            'sma_20': float(latest['SMA_20']),
            'sma_50': float(latest['SMA_50']),
            'ema_12': float(latest['EMA_12']),
            'ema_26': float(latest['EMA_26']),
            'macd': float(latest['MACD']),
            'signal_line': float(latest['Signal_Line']),
            'rsi': float(latest['RSI']),
            'momentum': float(latest['Momentum']),
            'previous_close': float(previous['Close'])
        }
