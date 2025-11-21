"""
Trading Analysis Service
Generates buy/sell signals and trading decisions based on technical indicators
"""
import pandas as pd
from typing import Optional, Dict, Any
from .indicator_service import IndicatorService


class TradingAnalysisService:
    """Service for analyzing stock data and generating trading signals/decisions"""

    # Score thresholds for display signals
    DISPLAY_STRONG_BUY_THRESHOLD = 30
    DISPLAY_BUY_THRESHOLD = 15
    DISPLAY_STRONG_SELL_THRESHOLD = -30
    DISPLAY_SELL_THRESHOLD = -15

    # Signal scoring weights
    SCORE_STRONG_TREND = 20
    SCORE_WEAK_TREND = 10
    SCORE_RSI_EXTREME = 15
    SCORE_MACD_CROSSOVER = 15
    SCORE_STRONG_MOMENTUM = 10

    def __init__(self, indicator_service: IndicatorService = None):
        """
        Initialize the Trading Analysis Service

        Args:
            indicator_service: Optional IndicatorService instance (default: uses class)
        """
        self.indicator_service = indicator_service or IndicatorService

    def generate_display_signals(self, df: pd.DataFrame, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Generate user-friendly buy/sell signals for display (used in /analyze endpoint)

        Args:
            df: DataFrame with OHLCV data and calculated indicators
            ticker: Stock ticker symbol

        Returns:
            Dictionary with signals, recommendation, and confidence, or None if insufficient data
        """
        if not self.indicator_service.has_sufficient_data(df):
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        signals = {
            'ticker': ticker,
            'current_price': round(latest['Close'], 2),
            'sma_20': round(latest['SMA_20'], 2) if pd.notna(latest['SMA_20']) else None,
            'sma_50': round(latest['SMA_50'], 2) if pd.notna(latest['SMA_50']) else None,
            'rsi': round(latest['RSI'], 2) if pd.notna(latest['RSI']) else None,
            'macd': round(latest['MACD'], 2) if pd.notna(latest['MACD']) else None,
            'momentum': round(latest['Momentum'], 2) if pd.notna(latest['Momentum']) else None,
            'recommendation': 'HOLD',
            'confidence': 50,
            'signals': []
        }

        score = self._calculate_signal_score(latest, prev, signals['signals'], display_mode=True)

        # Determine recommendation based on score
        if score >= self.DISPLAY_STRONG_BUY_THRESHOLD:
            signals['recommendation'] = 'STRONG BUY'
            signals['confidence'] = min(80 + (score - self.DISPLAY_STRONG_BUY_THRESHOLD), 95)
        elif score >= self.DISPLAY_BUY_THRESHOLD:
            signals['recommendation'] = 'BUY'
            signals['confidence'] = 65 + (score - self.DISPLAY_BUY_THRESHOLD)
        elif score <= self.DISPLAY_STRONG_SELL_THRESHOLD:
            signals['recommendation'] = 'STRONG SELL'
            signals['confidence'] = min(80 + abs(score + self.DISPLAY_STRONG_SELL_THRESHOLD), 95)
        elif score <= self.DISPLAY_SELL_THRESHOLD:
            signals['recommendation'] = 'SELL'
            signals['confidence'] = 65 + abs(score + self.DISPLAY_SELL_THRESHOLD)
        else:
            signals['recommendation'] = 'HOLD'
            signals['confidence'] = 50 + abs(score)

        return signals

    def generate_trading_decision(self, df: pd.DataFrame, ticker: str, trader) -> Optional[Dict[str, Any]]:
        """
        Generate trading decision (buy/sell/hold) for automated trading

        Args:
            df: DataFrame with OHLCV data and calculated indicators
            ticker: Stock ticker symbol
            trader: Trader model instance with risk_tolerance

        Returns:
            Dictionary with action, confidence, and signals, or None if insufficient data
        """
        if not self.indicator_service.has_sufficient_data(df):
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        decision = {
            'ticker': ticker,
            'current_price': float(latest['Close']),
            'sma_20': float(latest['SMA_20']) if pd.notna(latest['SMA_20']) else None,
            'sma_50': float(latest['SMA_50']) if pd.notna(latest['SMA_50']) else None,
            'rsi': float(latest['RSI']) if pd.notna(latest['RSI']) else None,
            'macd': float(latest['MACD']) if pd.notna(latest['MACD']) else None,
            'action': None,
            'confidence': 50,
            'signals': []
        }

        score = self._calculate_signal_score(latest, prev, decision['signals'], display_mode=False)

        # Get risk-adjusted thresholds
        thresholds = self._get_risk_thresholds(trader.risk_tolerance)

        # Determine action based on risk tolerance
        if score >= thresholds['buy']:
            decision['action'] = 'buy'
            decision['confidence'] = min(70 + (score - thresholds['buy']), 95)
        elif score <= thresholds['sell']:
            decision['action'] = 'sell'
            decision['confidence'] = min(70 + abs(score - thresholds['sell']), 95)
        else:
            decision['action'] = 'hold'
            decision['confidence'] = 50 + abs(score)

        return decision

    def _calculate_signal_score(self, latest: pd.Series, prev: pd.Series,
                                 signals_list: list, display_mode: bool = True) -> int:
        """
        Calculate trading score based on technical indicators

        Args:
            latest: Latest row from DataFrame with indicators
            prev: Previous row from DataFrame with indicators
            signals_list: List to append signal messages to
            display_mode: If True, use emoji-rich messages; if False, use plain messages

        Returns:
            Integer score (positive = bullish, negative = bearish)
        """
        score = 0

        # Trend signals
        if pd.notna(latest['SMA_20']) and pd.notna(latest['SMA_50']):
            if latest['Close'] > latest['SMA_20'] > latest['SMA_50']:
                msg = '✅ Strong uptrend: Price above both moving averages' if display_mode else 'Strong uptrend'
                signals_list.append(msg)
                score += self.SCORE_STRONG_TREND
            elif latest['Close'] > latest['SMA_20']:
                msg = '↗️ Uptrend: Price above 20-day MA' if display_mode else 'Uptrend'
                signals_list.append(msg)
                score += self.SCORE_WEAK_TREND
            elif latest['Close'] < latest['SMA_20'] < latest['SMA_50']:
                msg = '❌ Strong downtrend: Price below both moving averages' if display_mode else 'Strong downtrend'
                signals_list.append(msg)
                score -= self.SCORE_STRONG_TREND
            elif latest['Close'] < latest['SMA_20']:
                msg = '↘️ Downtrend: Price below 20-day MA' if display_mode else 'Downtrend'
                signals_list.append(msg)
                score -= self.SCORE_WEAK_TREND

        # RSI signals
        if pd.notna(latest['RSI']):
            if latest['RSI'] < 30:
                msg = f'🔥 Oversold (RSI: {latest["RSI"]:.1f}) - potential buy opportunity' if display_mode else f'Oversold (RSI: {latest["RSI"]:.1f})'
                signals_list.append(msg)
                score += self.SCORE_RSI_EXTREME
            elif latest['RSI'] > 70:
                msg = f'⚠️ Overbought (RSI: {latest["RSI"]:.1f}) - potential sell signal' if display_mode else f'Overbought (RSI: {latest["RSI"]:.1f})'
                signals_list.append(msg)
                score -= self.SCORE_RSI_EXTREME
            elif 40 <= latest['RSI'] <= 60 and display_mode:
                signals_list.append(f'⚖️ Neutral momentum (RSI: {latest["RSI"]:.1f})')

        # MACD signals
        if pd.notna(latest['MACD']) and pd.notna(latest['Signal_Line']) and \
           pd.notna(prev['MACD']) and pd.notna(prev['Signal_Line']):
            if latest['MACD'] > latest['Signal_Line'] and prev['MACD'] <= prev['Signal_Line']:
                msg = '📈 MACD bullish crossover - buy signal' if display_mode else 'MACD bullish crossover'
                signals_list.append(msg)
                score += self.SCORE_MACD_CROSSOVER
            elif latest['MACD'] < latest['Signal_Line'] and prev['MACD'] >= prev['Signal_Line']:
                msg = '📉 MACD bearish crossover - sell signal' if display_mode else 'MACD bearish crossover'
                signals_list.append(msg)
                score -= self.SCORE_MACD_CROSSOVER

        # Momentum signals
        if pd.notna(latest['Momentum']):
            if latest['Momentum'] > 5:
                msg = f'🚀 Strong positive momentum ({latest["Momentum"]:.1f}%)' if display_mode else f'Strong positive momentum ({latest["Momentum"]:.1f}%)'
                signals_list.append(msg)
                score += self.SCORE_STRONG_MOMENTUM
            elif latest['Momentum'] < -5:
                msg = f'⬇️ Strong negative momentum ({latest["Momentum"]:.1f}%)' if display_mode else f'Strong negative momentum ({latest["Momentum"]:.1f}%)'
                signals_list.append(msg)
                score -= self.SCORE_STRONG_MOMENTUM

        return score

    @staticmethod
    def _get_risk_thresholds(risk_tolerance: str) -> Dict[str, int]:
        """
        Get buy/sell thresholds based on trader's risk tolerance

        Args:
            risk_tolerance: 'low', 'medium', or 'high'

        Returns:
            Dictionary with 'buy' and 'sell' thresholds
        """
        thresholds = {
            'low': {'buy': 35, 'sell': -35},
            'medium': {'buy': 18, 'sell': -18},
            'high': {'buy': 15, 'sell': -15}
        }
        return thresholds.get(risk_tolerance, thresholds['medium'])
