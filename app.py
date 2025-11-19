import os
from flask import Flask, render_template, request, jsonify
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
from datetime import datetime, timedelta
import json
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Get Alpha Vantage API key
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
if not ALPHA_VANTAGE_API_KEY:
    logger.error("ALPHA_VANTAGE_API_KEY not found in environment variables!")
    raise ValueError("Please set ALPHA_VANTAGE_API_KEY in your .env file")

def calculate_technical_indicators(df):
    """Calculate technical indicators for trend analysis"""
    # Simple Moving Averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()

    # Exponential Moving Average
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()

    # MACD (Moving Average Convergence Divergence)
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # RSI (Relative Strength Index)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Price momentum
    df['Momentum'] = df['Close'].pct_change(periods=10) * 100

    return df

def generate_signals(df, ticker):
    """Generate buy/sell signals based on technical indicators"""
    if len(df) < 50:
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

    score = 0

    # Trend signals
    if pd.notna(latest['SMA_20']) and pd.notna(latest['SMA_50']):
        if latest['Close'] > latest['SMA_20'] > latest['SMA_50']:
            signals['signals'].append('✅ Strong uptrend: Price above both moving averages')
            score += 20
        elif latest['Close'] > latest['SMA_20']:
            signals['signals'].append('↗️ Uptrend: Price above 20-day MA')
            score += 10
        elif latest['Close'] < latest['SMA_20'] < latest['SMA_50']:
            signals['signals'].append('❌ Strong downtrend: Price below both moving averages')
            score -= 20
        elif latest['Close'] < latest['SMA_20']:
            signals['signals'].append('↘️ Downtrend: Price below 20-day MA')
            score -= 10

    # RSI signals
    if pd.notna(latest['RSI']):
        if latest['RSI'] < 30:
            signals['signals'].append(f'🔥 Oversold (RSI: {latest["RSI"]:.1f}) - potential buy opportunity')
            score += 15
        elif latest['RSI'] > 70:
            signals['signals'].append(f'⚠️ Overbought (RSI: {latest["RSI"]:.1f}) - potential sell signal')
            score -= 15
        elif 40 <= latest['RSI'] <= 60:
            signals['signals'].append(f'⚖️ Neutral momentum (RSI: {latest["RSI"]:.1f})')

    # MACD signals
    if pd.notna(latest['MACD']) and pd.notna(latest['Signal_Line']) and pd.notna(prev['MACD']) and pd.notna(prev['Signal_Line']):
        if latest['MACD'] > latest['Signal_Line'] and prev['MACD'] <= prev['Signal_Line']:
            signals['signals'].append('📈 MACD bullish crossover - buy signal')
            score += 15
        elif latest['MACD'] < latest['Signal_Line'] and prev['MACD'] >= prev['Signal_Line']:
            signals['signals'].append('📉 MACD bearish crossover - sell signal')
            score -= 15

    # Momentum signals
    if pd.notna(latest['Momentum']):
        if latest['Momentum'] > 5:
            signals['signals'].append(f'🚀 Strong positive momentum ({latest["Momentum"]:.1f}%)')
            score += 10
        elif latest['Momentum'] < -5:
            signals['signals'].append(f'⬇️ Strong negative momentum ({latest["Momentum"]:.1f}%)')
            score -= 10

    # Determine recommendation
    if score >= 30:
        signals['recommendation'] = 'STRONG BUY'
        signals['confidence'] = min(80 + (score - 30), 95)
    elif score >= 15:
        signals['recommendation'] = 'BUY'
        signals['confidence'] = 65 + (score - 15)
    elif score <= -30:
        signals['recommendation'] = 'STRONG SELL'
        signals['confidence'] = min(80 + abs(score + 30), 95)
    elif score <= -15:
        signals['recommendation'] = 'SELL'
        signals['confidence'] = 65 + abs(score + 15)
    else:
        signals['recommendation'] = 'HOLD'
        signals['confidence'] = 50 + abs(score)

    return signals

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        tickers = data.get('tickers', [])

        if not tickers:
            return jsonify({'error': 'No tickers provided'}), 400

        results = []

        # Initialize Alpha Vantage TimeSeries
        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

        for ticker in tickers:
            try:
                logger.info(f"Fetching data for {ticker.upper()}")

                # Fetch stock data from Alpha Vantage (6 months = ~180 days)
                df, meta_data = ts.get_daily(symbol=ticker.upper(), outputsize='full')

                # Rename columns to match expected format (Alpha Vantage uses '4. close' format)
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

                # Sort by date ascending (Alpha Vantage returns newest first)
                df = df.sort_index(ascending=True)

                # Get last 6 months of data
                six_months_ago = datetime.now() - timedelta(days=180)
                df = df[df.index >= six_months_ago]

                logger.info(f"Retrieved {len(df)} rows for {ticker.upper()}")

                if df.empty or len(df) < 10:
                    logger.warning(f"Insufficient data for {ticker.upper()}: {len(df) if not df.empty else 0} rows")
                    results.append({
                        'ticker': ticker.upper(),
                        'error': 'Invalid ticker or insufficient data available'
                    })
                    continue

                # Calculate indicators
                df = calculate_technical_indicators(df)

                # Generate signals
                signals = generate_signals(df, ticker.upper())

                if signals:
                    # Alpha Vantage doesn't provide company names in daily endpoint
                    # Just use the ticker symbol
                    signals['company_name'] = ticker.upper()

                    # Calculate price change over the period
                    price_change = ((df.iloc[-1]['Close'] - df.iloc[0]['Close']) / df.iloc[0]['Close']) * 100
                    signals['price_change_6mo'] = round(price_change, 2)

                    results.append(signals)
                else:
                    results.append({
                        'ticker': ticker.upper(),
                        'error': 'Insufficient data for analysis'
                    })

            except Exception as e:
                logger.error(f"Error analyzing {ticker.upper()}: {str(e)}", exc_info=True)
                error_msg = str(e)

                # Provide helpful error messages
                if 'Invalid API call' in error_msg or 'Invalid API Key' in error_msg:
                    error_msg = 'Invalid ticker symbol or API error'
                elif 'rate limit' in error_msg.lower():
                    error_msg = 'API rate limit reached. Please try again later.'

                results.append({
                    'ticker': ticker.upper(),
                    'error': f'Error analyzing ticker: {error_msg}'
                })

        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
