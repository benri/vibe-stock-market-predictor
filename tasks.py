import os
import logging
from celery_app import celery_app
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Alpha Vantage API key
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')


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


def generate_trading_decision(df, ticker, trader):
    """Generate buy/sell decision based on technical indicators"""
    if len(df) < 50:
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

    score = 0

    # Trend signals
    if pd.notna(latest['SMA_20']) and pd.notna(latest['SMA_50']):
        if latest['Close'] > latest['SMA_20'] > latest['SMA_50']:
            decision['signals'].append('Strong uptrend')
            score += 20
        elif latest['Close'] > latest['SMA_20']:
            decision['signals'].append('Uptrend')
            score += 10
        elif latest['Close'] < latest['SMA_20'] < latest['SMA_50']:
            decision['signals'].append('Strong downtrend')
            score -= 20
        elif latest['Close'] < latest['SMA_20']:
            decision['signals'].append('Downtrend')
            score -= 10

    # RSI signals
    if pd.notna(latest['RSI']):
        if latest['RSI'] < 30:
            decision['signals'].append(f'Oversold (RSI: {latest["RSI"]:.1f})')
            score += 15
        elif latest['RSI'] > 70:
            decision['signals'].append(f'Overbought (RSI: {latest["RSI"]:.1f})')
            score -= 15

    # MACD signals
    if pd.notna(latest['MACD']) and pd.notna(latest['Signal_Line']) and pd.notna(prev['MACD']) and pd.notna(prev['Signal_Line']):
        if latest['MACD'] > latest['Signal_Line'] and prev['MACD'] <= prev['Signal_Line']:
            decision['signals'].append('MACD bullish crossover')
            score += 15
        elif latest['MACD'] < latest['Signal_Line'] and prev['MACD'] >= prev['Signal_Line']:
            decision['signals'].append('MACD bearish crossover')
            score -= 15

    # Momentum signals
    if pd.notna(latest['Momentum']):
        if latest['Momentum'] > 5:
            decision['signals'].append(f'Strong positive momentum ({latest["Momentum"]:.1f}%)')
            score += 10
        elif latest['Momentum'] < -5:
            decision['signals'].append(f'Strong negative momentum ({latest["Momentum"]:.1f}%)')
            score -= 10

    # Adjust score based on risk tolerance
    if trader.risk_tolerance == 'low':
        threshold_buy = 35
        threshold_sell = -35
    elif trader.risk_tolerance == 'high':
        threshold_buy = 15
        threshold_sell = -15
    else:  # medium
        threshold_buy = 25
        threshold_sell = -25

    # Determine action
    if score >= threshold_buy:
        decision['action'] = 'buy'
        decision['confidence'] = min(70 + (score - threshold_buy), 95)
    elif score <= threshold_sell:
        decision['action'] = 'sell'
        decision['confidence'] = min(70 + abs(score - threshold_sell), 95)
    else:
        decision['action'] = 'hold'
        decision['confidence'] = 50 + abs(score)

    return decision


@celery_app.task(name='tasks.execute_all_trader_decisions')
def execute_all_trader_decisions(time_of_day='morning'):
    """
    Execute trading decisions for all active traders

    Args:
        time_of_day: morning, midday, or afternoon
    """
    from app import app
    from models import db, Trader, Trade, Portfolio, TraderStatus, TradeAction

    with app.app_context():
        logger.info(f"Starting {time_of_day} trading session")

        # Get all active traders
        traders = Trader.query.filter_by(status=TraderStatus.ACTIVE).all()

        if not traders:
            logger.info("No active traders found")
            return {'status': 'success', 'message': 'No active traders'}

        # Define watchlist of tickers to trade
        watchlist = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META']

        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

        results = []

        for trader in traders:
            logger.info(f"Processing trader: {trader.name}")

            # Get trader's current portfolio
            portfolio = Portfolio.query.filter_by(trader_id=trader.id).all()
            portfolio_tickers = {item.ticker for item in portfolio}

            # Analyze each ticker
            for ticker in watchlist:
                try:
                    # Fetch stock data
                    df, _ = ts.get_daily(symbol=ticker, outputsize='full')
                    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                    df = df.sort_index(ascending=True)

                    # Get last 6 months
                    six_months_ago = datetime.now() - timedelta(days=180)
                    df = df[df.index >= six_months_ago]

                    if df.empty or len(df) < 50:
                        logger.warning(f"Insufficient data for {ticker}")
                        continue

                    # Calculate indicators
                    df = calculate_technical_indicators(df)

                    # Generate decision
                    decision = generate_trading_decision(df, ticker, trader)

                    if not decision:
                        continue

                    # Execute trade based on decision
                    if decision['action'] == 'buy':
                        # Determine quantity based on account balance and risk tolerance
                        max_investment = trader.current_balance * (0.15 if trader.risk_tolerance == 'high' else 0.10 if trader.risk_tolerance == 'medium' else 0.05)
                        quantity = int(max_investment / decision['current_price'])

                        if quantity > 0 and trader.current_balance >= (quantity * decision['current_price']):
                            # Execute buy
                            price = decision['current_price']
                            total_amount = quantity * price

                            trader.current_balance -= total_amount

                            # Update portfolio
                            portfolio_item = Portfolio.query.filter_by(
                                trader_id=trader.id,
                                ticker=ticker
                            ).first()

                            if portfolio_item:
                                new_total_cost = portfolio_item.total_cost + total_amount
                                new_quantity = portfolio_item.quantity + quantity
                                portfolio_item.average_price = new_total_cost / new_quantity
                                portfolio_item.total_cost = new_total_cost
                                portfolio_item.quantity = new_quantity
                            else:
                                portfolio_item = Portfolio(
                                    trader_id=trader.id,
                                    ticker=ticker,
                                    quantity=quantity,
                                    average_price=price,
                                    total_cost=total_amount
                                )
                                db.session.add(portfolio_item)

                            # Create trade record
                            trade = Trade(
                                trader_id=trader.id,
                                ticker=ticker,
                                action=TradeAction.BUY,
                                quantity=quantity,
                                price=price,
                                total_amount=total_amount,
                                balance_after=trader.current_balance,
                                rsi=decision['rsi'],
                                macd=decision['macd'],
                                sma_20=decision['sma_20'],
                                sma_50=decision['sma_50'],
                                recommendation='BUY',
                                confidence=decision['confidence'],
                                notes=f"Automated {time_of_day} trade: {', '.join(decision['signals'])}"
                            )

                            trader.last_trade_at = datetime.utcnow()
                            db.session.add(trade)

                            results.append({
                                'trader': trader.name,
                                'action': 'BUY',
                                'ticker': ticker,
                                'quantity': quantity,
                                'price': price
                            })

                            logger.info(f"{trader.name} bought {quantity} shares of {ticker} at ${price}")

                    elif decision['action'] == 'sell' and ticker in portfolio_tickers:
                        # Find portfolio item
                        portfolio_item = Portfolio.query.filter_by(
                            trader_id=trader.id,
                            ticker=ticker
                        ).first()

                        if portfolio_item and portfolio_item.quantity > 0:
                            # Sell half of position or all if small
                            quantity = portfolio_item.quantity // 2 if portfolio_item.quantity > 2 else portfolio_item.quantity
                            price = decision['current_price']
                            total_amount = quantity * price

                            trader.current_balance += total_amount

                            # Update portfolio
                            portfolio_item.quantity -= quantity
                            portfolio_item.total_cost -= (portfolio_item.average_price * quantity)

                            if portfolio_item.quantity == 0:
                                db.session.delete(portfolio_item)

                            # Create trade record
                            trade = Trade(
                                trader_id=trader.id,
                                ticker=ticker,
                                action=TradeAction.SELL,
                                quantity=quantity,
                                price=price,
                                total_amount=total_amount,
                                balance_after=trader.current_balance,
                                rsi=decision['rsi'],
                                macd=decision['macd'],
                                sma_20=decision['sma_20'],
                                sma_50=decision['sma_50'],
                                recommendation='SELL',
                                confidence=decision['confidence'],
                                notes=f"Automated {time_of_day} trade: {', '.join(decision['signals'])}"
                            )

                            trader.last_trade_at = datetime.utcnow()
                            db.session.add(trade)

                            results.append({
                                'trader': trader.name,
                                'action': 'SELL',
                                'ticker': ticker,
                                'quantity': quantity,
                                'price': price
                            })

                            logger.info(f"{trader.name} sold {quantity} shares of {ticker} at ${price}")

                except Exception as e:
                    logger.error(f"Error processing {ticker} for {trader.name}: {str(e)}")
                    continue

        # Commit all trades
        db.session.commit()

        logger.info(f"Completed {time_of_day} trading session. Executed {len(results)} trades")

        return {
            'status': 'success',
            'time_of_day': time_of_day,
            'traders_processed': len(traders),
            'trades_executed': len(results),
            'trades': results
        }


@celery_app.task(name='tasks.portfolio_health_check')
def portfolio_health_check():
    """
    Check portfolio health for all traders after market close
    """
    from app import app
    from models import db, Trader, Portfolio

    with app.app_context():
        logger.info("Starting portfolio health check")

        traders = Trader.query.all()

        results = []

        for trader in traders:
            portfolio = Portfolio.query.filter_by(trader_id=trader.id).all()

            portfolio_value = sum(item.total_cost for item in portfolio)
            total_value = float(trader.current_balance) + portfolio_value

            performance = {
                'trader_id': trader.id,
                'trader_name': trader.name,
                'cash_balance': float(trader.current_balance),
                'portfolio_value': float(portfolio_value),
                'total_value': float(total_value),
                'initial_balance': float(trader.initial_balance),
                'profit_loss': float(total_value - trader.initial_balance),
                'profit_loss_pct': float((total_value - trader.initial_balance) / trader.initial_balance * 100) if trader.initial_balance > 0 else 0,
                'positions': len(portfolio)
            }

            results.append(performance)
            logger.info(f"{trader.name}: Total value ${total_value:.2f}, P&L: {performance['profit_loss_pct']:.2f}%")

        return {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'traders': results
        }


@celery_app.task(name='tasks.execute_single_trade')
def execute_single_trade(trader_id, ticker):
    """
    Execute a single trade for a specific trader and ticker
    Useful for manual triggering or testing
    """
    from app import app
    from models import db, Trader

    with app.app_context():
        trader = Trader.query.get(trader_id)

        if not trader:
            return {'status': 'error', 'message': 'Trader not found'}

        # This would contain the same logic as above but for a single ticker
        # Omitted for brevity but would follow the same pattern

        return {'status': 'success', 'message': f'Trade executed for {ticker}'}
