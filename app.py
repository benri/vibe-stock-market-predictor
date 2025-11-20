import os
from flask import Flask, render_template, request, jsonify
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
import json
import requests
import logging
from dotenv import load_dotenv
from flask_migrate import Migrate
from models import db, Trader, Trade, Portfolio, TraderStatus, TradeAction
from functools import wraps

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key for scheduled tasks
SCHEDULER_API_KEY = os.getenv('SCHEDULER_API_KEY', 'change-me-in-production')

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Heroku uses postgres:// but SQLAlchemy requires postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Local development database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/vibe-stock-market-predictor-development'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

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

def require_api_key(f):
    """Decorator to require API key authentication for scheduled task endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if not api_key or api_key != SCHEDULER_API_KEY:
            logger.warning(f"Unauthorized API access attempt from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized - Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function


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

@app.route('/api/traders', methods=['GET', 'POST'])
def traders():
    """Get all traders or create a new trader"""
    if request.method == 'GET':
        traders = Trader.query.all()
        return jsonify({'traders': [trader.to_dict() for trader in traders]})

    elif request.method == 'POST':
        data = request.get_json()

        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Trader name is required'}), 400

        # Check if trader name already exists
        if Trader.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Trader with this name already exists'}), 400

        # Create new trader
        trader = Trader(
            name=data['name'],
            initial_balance=data.get('initial_balance', 10000.00),
            current_balance=data.get('initial_balance', 10000.00),
            strategy_name=data.get('strategy_name', 'default'),
            risk_tolerance=data.get('risk_tolerance', 'medium'),
            trading_ethos=data.get('trading_ethos'),
            trading_timezone=data.get('trading_timezone', 'America/New_York'),
            status=TraderStatus.ACTIVE
        )

        db.session.add(trader)
        db.session.commit()

        logger.info(f"Created new trader: {trader.name} with ${trader.initial_balance}")
        return jsonify(trader.to_dict()), 201


@app.route('/api/traders/<int:trader_id>', methods=['GET', 'PUT', 'DELETE'])
def trader_detail(trader_id):
    """Get, update, or delete a specific trader"""
    trader = Trader.query.get_or_404(trader_id)

    if request.method == 'GET':
        return jsonify(trader.to_dict())

    elif request.method == 'PUT':
        data = request.get_json()

        # Update trader fields
        if 'name' in data:
            trader.name = data['name']
        if 'status' in data:
            trader.status = TraderStatus(data['status'])
        if 'strategy_name' in data:
            trader.strategy_name = data['strategy_name']
        if 'risk_tolerance' in data:
            trader.risk_tolerance = data['risk_tolerance']
        if 'trading_ethos' in data:
            trader.trading_ethos = data['trading_ethos']
        if 'trading_timezone' in data:
            trader.trading_timezone = data['trading_timezone']

        db.session.commit()
        logger.info(f"Updated trader: {trader.name}")
        return jsonify(trader.to_dict())

    elif request.method == 'DELETE':
        db.session.delete(trader)
        db.session.commit()
        logger.info(f"Deleted trader: {trader.name}")
        return jsonify({'message': 'Trader deleted successfully'}), 200


@app.route('/api/traders/<int:trader_id>/trades', methods=['GET', 'POST'])
def trader_trades(trader_id):
    """Get all trades for a trader or execute a new trade"""
    trader = Trader.query.get_or_404(trader_id)

    if request.method == 'GET':
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        # Get trades with pagination
        trades_pagination = Trade.query.filter_by(trader_id=trader_id)\
            .order_by(Trade.executed_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'trades': [trade.to_dict() for trade in trades_pagination.items],
            'total': trades_pagination.total,
            'pages': trades_pagination.pages,
            'current_page': page
        })

    elif request.method == 'POST':
        data = request.get_json()

        # Validate required fields
        required_fields = ['ticker', 'action', 'quantity', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400

        # Check trader status
        if trader.status != TraderStatus.ACTIVE:
            return jsonify({'error': 'Trader is not active'}), 400

        action = TradeAction(data['action'])
        quantity = int(data['quantity'])
        price = float(data['price'])
        total_amount = quantity * price

        # Validate trade
        if action == TradeAction.BUY:
            if trader.current_balance < total_amount:
                return jsonify({'error': 'Insufficient balance for this trade'}), 400
        elif action == TradeAction.SELL:
            # Check if trader owns enough shares
            portfolio_item = Portfolio.query.filter_by(
                trader_id=trader_id,
                ticker=data['ticker']
            ).first()

            if not portfolio_item or portfolio_item.quantity < quantity:
                return jsonify({'error': 'Insufficient shares to sell'}), 400

        # Execute trade
        if action == TradeAction.BUY:
            trader.current_balance -= Decimal(str(total_amount))

            # Update portfolio
            portfolio_item = Portfolio.query.filter_by(
                trader_id=trader_id,
                ticker=data['ticker']
            ).first()

            if portfolio_item:
                # Update existing position
                new_total_cost = portfolio_item.total_cost + total_amount
                new_quantity = portfolio_item.quantity + quantity
                portfolio_item.average_price = new_total_cost / new_quantity
                portfolio_item.total_cost = new_total_cost
                portfolio_item.quantity = new_quantity
            else:
                # Create new position
                portfolio_item = Portfolio(
                    trader_id=trader_id,
                    ticker=data['ticker'],
                    quantity=quantity,
                    average_price=price,
                    total_cost=total_amount
                )
                db.session.add(portfolio_item)

        elif action == TradeAction.SELL:
            trader.current_balance += Decimal(str(total_amount))

            # Update portfolio
            portfolio_item = Portfolio.query.filter_by(
                trader_id=trader_id,
                ticker=data['ticker']
            ).first()

            portfolio_item.quantity -= quantity
            portfolio_item.total_cost -= (portfolio_item.average_price * quantity)

            # Remove position if quantity is 0
            if portfolio_item.quantity == 0:
                db.session.delete(portfolio_item)

        # Create trade record
        trade = Trade(
            trader_id=trader_id,
            ticker=data['ticker'],
            action=action,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            balance_after=trader.current_balance,
            rsi=data.get('rsi'),
            macd=data.get('macd'),
            sma_20=data.get('sma_20'),
            sma_50=data.get('sma_50'),
            recommendation=data.get('recommendation'),
            confidence=data.get('confidence'),
            notes=data.get('notes')
        )

        trader.last_trade_at = datetime.utcnow()

        db.session.add(trade)
        db.session.commit()

        logger.info(f"Executed trade: {trade}")
        return jsonify(trade.to_dict()), 201


@app.route('/api/traders/<int:trader_id>/portfolio', methods=['GET'])
def trader_portfolio(trader_id):
    """Get current portfolio for a trader"""
    trader = Trader.query.get_or_404(trader_id)
    portfolio_items = Portfolio.query.filter_by(trader_id=trader_id).all()

    return jsonify({
        'trader_id': trader_id,
        'trader_name': trader.name,
        'current_balance': float(trader.current_balance),
        'portfolio': [item.to_dict() for item in portfolio_items]
    })


@app.route('/api/trades', methods=['GET'])
def all_trades():
    """Get all trades across all traders"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    ticker = request.args.get('ticker', type=str)

    query = Trade.query

    if ticker:
        query = query.filter_by(ticker=ticker.upper())

    trades_pagination = query.order_by(Trade.executed_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'trades': [trade.to_dict() for trade in trades_pagination.items],
        'total': trades_pagination.total,
        'pages': trades_pagination.pages,
        'current_page': page
    })


@app.route('/api/scheduled/execute-trades', methods=['POST'])
@require_api_key
def execute_scheduled_trades():
    """
    API endpoint to trigger trading execution for a specific timezone

    Body params:
        timezone: Trading timezone (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo')
        time_of_day: Trading session (e.g., 'morning', 'midday', 'afternoon', 'closing')

    Example:
        curl -X POST https://your-app.herokuapp.com/api/scheduled/execute-trades \
             -H "X-API-Key: your-api-key" \
             -H "Content-Type: application/json" \
             -d '{"timezone": "America/New_York", "time_of_day": "morning"}'
    """
    try:
        data = request.get_json() or {}
        timezone = data.get('timezone', 'America/New_York')
        time_of_day = data.get('time_of_day', 'morning')

        logger.info(f"📊 Scheduled trade execution triggered: {timezone} - {time_of_day}")

        # Import the task function directly
        from tasks import execute_trader_decisions_by_timezone

        # Execute the trading task synchronously
        result = execute_trader_decisions_by_timezone(timezone, time_of_day)

        logger.info(f"✅ Trade execution completed: {result.get('trades_executed', 0)} trades")

        return jsonify({
            'status': 'success',
            'message': f'Executed {time_of_day} trades for {timezone}',
            'result': result
        }), 200

    except Exception as e:
        logger.error(f"❌ Error executing scheduled trades: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/scheduled/portfolio-health-check', methods=['POST'])
@require_api_key
def scheduled_portfolio_health_check():
    """
    API endpoint to trigger portfolio health check

    Example:
        curl -X POST https://your-app.herokuapp.com/api/scheduled/portfolio-health-check \
             -H "X-API-Key: your-api-key"
    """
    try:
        logger.info("📊 Portfolio health check triggered")

        # Import the task function directly
        from tasks import portfolio_health_check

        # Execute the health check synchronously
        result = portfolio_health_check()

        logger.info(f"✅ Portfolio health check completed for {len(result.get('traders', []))} traders")

        return jsonify({
            'status': 'success',
            'message': 'Portfolio health check completed',
            'result': result
        }), 200

    except Exception as e:
        logger.error(f"❌ Error executing portfolio health check: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/scheduled/update-prices', methods=['POST'])
@require_api_key
def scheduled_update_prices():
    """
    Update ticker prices in ticker_prices table
    Triggered by GitHub Actions daily after market close

    Example:
        curl -X POST https://your-app.herokuapp.com/api/scheduled/update-prices \
             -H "X-API-Key: your-api-key"
    """
    logger.info("📊 Scheduled price update triggered")

    try:
        from tasks import update_portfolio_prices
        result = update_portfolio_prices()

        logger.info(f"✅ Price update completed: {result}")

        return jsonify({
            'status': 'success',
            'message': f"Updated prices for {result['updated']} tickers",
            'result': result
        }), 200

    except Exception as e:
        logger.error(f"❌ Error during price update: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/scheduled/health', methods=['GET'])
def scheduler_health():
    """
    Health check endpoint for scheduler to verify app is running
    No authentication required for health checks
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Scheduled task endpoint is operational'
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
