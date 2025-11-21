"""
Tests for stock analysis and technical indicators
"""

import pytest
import pandas as pd
import numpy as np
from src.services import IndicatorService, TradingAnalysisService

# Initialize services for testing
indicator_service = IndicatorService()
analysis_service = TradingAnalysisService(indicator_service)


class TestTechnicalIndicators:
    """Test cases for technical indicator calculations"""

    @pytest.fixture
    def sample_stock_data(self):
        """Create sample stock price data for testing"""
        # Create 100 days of sample data
        dates = pd.date_range('2024-01-01', periods=100, freq='D')

        # Generate price data with an uptrend
        np.random.seed(42)
        base_price = 100
        prices = base_price + np.cumsum(np.random.randn(100) * 2)
        prices = np.maximum(prices, 50)  # Keep prices above 50

        df = pd.DataFrame({
            'Close': prices,
            'Open': prices * 0.99,
            'High': prices * 1.01,
            'Low': prices * 0.98,
            'Volume': np.random.randint(1000000, 5000000, 100)
        }, index=dates)

        return df

    def test_calculate_sma(self, sample_stock_data):
        """Test Simple Moving Average calculation"""
        df = indicator_service.calculate_all_indicators(sample_stock_data)

        assert 'SMA_20' in df.columns
        assert 'SMA_50' in df.columns

        # Check that SMA values are not null where expected
        assert not df['SMA_20'].iloc[-1:].isna().any()
        assert not df['SMA_50'].iloc[-1:].isna().any()

        # Check that SMA is actually an average
        last_20_prices = df['Close'].iloc[-20:].mean()
        assert abs(df['SMA_20'].iloc[-1] - last_20_prices) < 0.01

    def test_calculate_ema(self, sample_stock_data):
        """Test Exponential Moving Average calculation"""
        df = indicator_service.calculate_all_indicators(sample_stock_data)

        assert 'EMA_12' in df.columns
        assert 'EMA_26' in df.columns

        # Check that EMA values exist
        assert not df['EMA_12'].iloc[-1:].isna().any()
        assert not df['EMA_26'].iloc[-1:].isna().any()

    def test_calculate_macd(self, sample_stock_data):
        """Test MACD calculation"""
        df = indicator_service.calculate_all_indicators(sample_stock_data)

        assert 'MACD' in df.columns
        assert 'Signal_Line' in df.columns

        # MACD should be EMA_12 - EMA_26
        expected_macd = df['EMA_12'].iloc[-1] - df['EMA_26'].iloc[-1]
        assert abs(df['MACD'].iloc[-1] - expected_macd) < 0.01

    def test_calculate_rsi(self, sample_stock_data):
        """Test RSI calculation"""
        df = indicator_service.calculate_all_indicators(sample_stock_data)

        assert 'RSI' in df.columns

        # RSI should be between 0 and 100
        assert 0 <= df['RSI'].iloc[-1] <= 100

        # Check that RSI is not null
        assert not pd.isna(df['RSI'].iloc[-1])

    def test_calculate_momentum(self, sample_stock_data):
        """Test momentum calculation"""
        df = indicator_service.calculate_all_indicators(sample_stock_data)

        assert 'Momentum' in df.columns

        # Momentum should be percentage change over 10 periods
        manual_momentum = ((df['Close'].iloc[-1] / df['Close'].iloc[-11]) - 1) * 100
        assert abs(df['Momentum'].iloc[-1] - manual_momentum) < 0.01


class TestSignalGeneration:
    """Test cases for trading signal generation"""

    @pytest.fixture
    def uptrend_data(self):
        """Create data showing strong uptrend"""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')

        # Create steady uptrend
        prices = np.linspace(100, 150, 100)

        df = pd.DataFrame({
            'Close': prices,
            'Open': prices * 0.99,
            'High': prices * 1.01,
            'Low': prices * 0.98,
            'Volume': np.ones(100) * 1000000
        }, index=dates)

        return indicator_service.calculate_all_indicators(df)

    @pytest.fixture
    def downtrend_data(self):
        """Create data showing strong downtrend"""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')

        # Create steady downtrend
        prices = np.linspace(150, 100, 100)

        df = pd.DataFrame({
            'Close': prices,
            'Open': prices * 0.99,
            'High': prices * 1.01,
            'Low': prices * 0.98,
            'Volume': np.ones(100) * 1000000
        }, index=dates)

        return indicator_service.calculate_all_indicators(df)

    @pytest.fixture
    def neutral_data(self):
        """Create data showing neutral/sideways movement"""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')

        # Create sideways movement
        np.random.seed(42)
        prices = 125 + np.random.randn(100) * 2

        df = pd.DataFrame({
            'Close': prices,
            'Open': prices * 0.99,
            'High': prices * 1.01,
            'Low': prices * 0.98,
            'Volume': np.ones(100) * 1000000
        }, index=dates)

        return indicator_service.calculate_all_indicators(df)

    def test_generate_signals_structure(self, uptrend_data):
        """Test that signals have correct structure"""
        signals = analysis_service.generate_display_signals(uptrend_data, 'TEST')

        assert signals is not None
        assert 'ticker' in signals
        assert 'current_price' in signals
        assert 'recommendation' in signals
        assert 'confidence' in signals
        assert 'signals' in signals
        assert isinstance(signals['signals'], list)

    def test_insufficient_data(self):
        """Test signal generation with insufficient data"""
        # Create data with less than 50 rows
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        df = pd.DataFrame({
            'Close': np.ones(30) * 100
        }, index=dates)

        df = indicator_service.calculate_all_indicators(df)
        signals = analysis_service.generate_display_signals(df, 'TEST')

        assert signals is None

    def test_uptrend_generates_buy_signal(self, uptrend_data):
        """Test that strong uptrend generates positive signal"""
        signals = analysis_service.generate_display_signals(uptrend_data, 'TEST')

        assert signals is not None
        # Uptrend should generate BUY, STRONG BUY, or at minimum HOLD (not SELL)
        assert signals['recommendation'] in ['BUY', 'STRONG BUY', 'HOLD']
        assert signals['recommendation'] not in ['SELL', 'STRONG SELL']

    def test_downtrend_generates_sell_signal(self, downtrend_data):
        """Test that strong downtrend generates sell signal"""
        signals = analysis_service.generate_display_signals(downtrend_data, 'TEST')

        assert signals is not None
        assert signals['recommendation'] in ['SELL', 'STRONG SELL', 'HOLD']
        # Note: might be HOLD if indicators are mixed

    def test_technical_indicators_in_signals(self, uptrend_data):
        """Test that signals include technical indicator values"""
        signals = analysis_service.generate_display_signals(uptrend_data, 'TEST')

        assert 'sma_20' in signals
        assert 'sma_50' in signals
        assert 'rsi' in signals
        assert 'macd' in signals
        assert 'momentum' in signals

        # Check that values are numeric
        assert isinstance(signals['sma_20'], (int, float))
        assert isinstance(signals['sma_50'], (int, float))
        assert isinstance(signals['rsi'], (int, float))

    def test_signal_messages(self, uptrend_data):
        """Test that signal messages are generated"""
        signals = analysis_service.generate_display_signals(uptrend_data, 'TEST')

        assert len(signals['signals']) > 0

        # Check that signals are strings
        for signal in signals['signals']:
            assert isinstance(signal, str)
            assert len(signal) > 0

    def test_confidence_range(self, uptrend_data):
        """Test that confidence is within valid range"""
        signals = analysis_service.generate_display_signals(uptrend_data, 'TEST')

        assert 0 <= signals['confidence'] <= 100

    def test_recommendation_values(self, uptrend_data):
        """Test that recommendation is one of valid values"""
        signals = analysis_service.generate_display_signals(uptrend_data, 'TEST')

        valid_recommendations = ['STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL']
        assert signals['recommendation'] in valid_recommendations


class TestAnalysisEndpoint:
    """Test cases for the analyze endpoint"""

    def test_analyze_endpoint_structure(self, client, mocker):
        """Test that analyze endpoint returns correct structure"""
        # Mock Alpha Vantage API
        mock_ts = mocker.MagicMock()

        # Create mock data
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        mock_data = pd.DataFrame({
            'Open': np.ones(100) * 100,
            'High': np.ones(100) * 101,
            'Low': np.ones(100) * 99,
            'Close': np.linspace(100, 110, 100),
            'Volume': np.ones(100) * 1000000
        }, index=dates)

        mock_ts.return_value.get_daily.return_value = (mock_data, {})
        mocker.patch('app.TimeSeries', return_value=mock_ts.return_value)

        response = client.post(
            '/analyze',
            data='{"tickers": ["AAPL"]}',
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()

        assert 'results' in data
        assert len(data['results']) == 1

    def test_analyze_no_tickers(self, client):
        """Test analyze endpoint with no tickers"""
        response = client.post(
            '/analyze',
            data='{"tickers": []}',
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
