"""
Trading Tasks
Automated trading tasks for executing trades and managing portfolios
Uses service layer for all business logic
"""
import os
import logging
from alpha_vantage.timeseries import TimeSeries
from datetime import datetime, timedelta
from dotenv import load_dotenv
from decimal import Decimal

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Alpha Vantage API key
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')


def fetch_and_analyze_ticker(ticker, ts, indicator_service, analysis_service, trader):
    """
    Fetch stock data, calculate indicators, and generate trading decision

    Args:
        ticker: Stock ticker symbol
        ts: Alpha Vantage TimeSeries instance
        indicator_service: IndicatorService instance
        analysis_service: TradingAnalysisService instance
        trader: Trader model instance

    Returns:
        Trading decision dictionary or None if error/insufficient data
    """
    try:
        logger.info(f"Analyzing {ticker}...")

        # Fetch stock data (compact = last ~100 data points, suitable for technical analysis)
        df, _ = ts.get_daily(symbol=ticker, outputsize='compact')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df.sort_index(ascending=True)

        # Compact gives us ~100 days, which is sufficient for technical indicators
        # (we need at least 50 days for SMA-50)

        if df.empty or not indicator_service.has_sufficient_data(df):
            logger.warning(f"Insufficient data for {ticker}: {len(df) if not df.empty else 0} rows")
            return None

        logger.info(f"Fetched {len(df)} rows for {ticker}, calculating indicators...")

        # Calculate indicators using service
        df = indicator_service.calculate_all_indicators(df)

        # Generate decision using service
        decision = analysis_service.generate_trading_decision(df, ticker, trader)

        if not decision:
            logger.warning(f"No decision generated for {ticker}")
            return None

        logger.info(
            f"{ticker}: action={decision['action']}, confidence={decision['confidence']}%, "
            f"price=${decision['current_price']}, signals={decision['signals'][:2] if decision['signals'] else 'none'}"
        )

        return decision

    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {str(e)}")
        return None


def execute_all_trader_decisions(time_of_day='morning'):
    """
    Execute trading decisions for all active traders

    Args:
        time_of_day: morning, midday, or afternoon
    """
    from app import app
    from models import db, Trader, TraderStatus
    from src.services import IndicatorService, TradingAnalysisService, TradingService
    from src.config import TradingConfig

    with app.app_context():
        logger.info(f"Starting {time_of_day} trading session")

        # Get all active traders
        traders = Trader.query.filter_by(status=TraderStatus.ACTIVE).all()

        if not traders:
            logger.info("No active traders found")
            return {'status': 'success', 'message': 'No active traders'}

        # Initialize services
        indicator_service = IndicatorService()
        analysis_service = TradingAnalysisService(indicator_service)
        trading_service = TradingService()

        # Get watchlist (default to New York if no timezone specified)
        watchlist = TradingConfig.get_watchlist('America/New_York')

        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
        results = []

        for trader in traders:
            logger.info(f"Processing trader: {trader.name}")

            # Get trader's current portfolio tickers
            portfolio_tickers = trading_service.get_trader_portfolio_tickers(trader.id)

            # Analyze each ticker in watchlist
            for ticker in watchlist:
                decision = fetch_and_analyze_ticker(
                    ticker, ts, indicator_service, analysis_service, trader
                )

                if not decision:
                    continue

                # Execute trade based on decision using service
                trade_result = None

                if decision['action'] == 'buy':
                    trade_result = trading_service.execute_buy_trade(
                        trader, ticker, decision, time_of_day
                    )
                elif decision['action'] == 'sell' and ticker in portfolio_tickers:
                    trade_result = trading_service.execute_sell_trade(
                        trader, ticker, decision, time_of_day
                    )

                if trade_result:
                    results.append(trade_result)

        # Commit all trades
        db.session.commit()

        logger.info(f"Completed {time_of_day} trading session. Executed {len(results)} trades")

        # Update portfolio prices after trading
        try:
            price_update_result = update_portfolio_prices()
            logger.info(f"Updated {price_update_result['updated']} portfolio prices")
        except Exception as e:
            logger.error(f"Error updating portfolio prices: {str(e)}")

        return {
            'status': 'success',
            'time_of_day': time_of_day,
            'traders_processed': len(traders),
            'trades_executed': len(results),
            'trades': results
        }


def execute_trader_decisions_by_timezone(timezone, time_of_day='morning'):
    """
    Execute trading decisions for traders in a specific timezone
    Uses hybrid dynamic watchlist system with portfolio-first prioritization

    Args:
        timezone: Trading timezone (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo')
        time_of_day: morning, midday, afternoon, or closing
    """
    from app import app
    from models import db, Trader, TraderStatus
    from src.services import IndicatorService, TradingAnalysisService, TradingService
    from src.services.watchlist_service import WatchlistService
    from src.services.api_limit_service import ApiLimitService
    from src.config import TradingConfig

    with app.app_context():
        logger.info(f"🚀 Starting {time_of_day} trading session for {timezone} timezone")

        # Initialize API cache
        ApiLimitService.initialize_cache()

        # Get all active traders for the specific timezone
        traders = Trader.query.filter_by(
            status=TraderStatus.ACTIVE,
            trading_timezone=timezone
        ).all()

        if not traders:
            logger.info(f"No active traders found for timezone {timezone}")
            return {
                'status': 'success',
                'message': f'No active traders in timezone {timezone}',
                'timezone': timezone,
                'time_of_day': time_of_day
            }

        logger.info(f"Found {len(traders)} active traders in {timezone}")

        # Initialize services
        indicator_service = IndicatorService()
        analysis_service = TradingAnalysisService(indicator_service)
        trading_service = TradingService()

        # Check API capacity before starting
        avg_tickers_per_trader = 8  # Estimate: 2-3 portfolio + 5-8 discovery
        capacity = ApiLimitService.estimate_remaining_capacity(db, len(traders), avg_tickers_per_trader)
        logger.info(capacity['message'])

        if not capacity['can_proceed']:
            logger.warning("⚠️ Insufficient API capacity - aborting trading session")
            return {
                'status': 'aborted',
                'message': 'Insufficient API quota remaining',
                'timezone': timezone,
                'time_of_day': time_of_day,
                'capacity_info': capacity
            }

        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
        results = []
        api_calls_made = 0

        for trader in traders:
            logger.info(f"📊 Processing trader: {trader.name} (Timezone: {timezone})")

            # Get dynamic watchlist using hybrid system
            watchlist = WatchlistService.get_priority_tickers(
                trader_id=trader.id,
                timezone=timezone,
                db=db,
                limit=trader.watchlist_size if trader.watchlist_size else 6
            )

            if not watchlist:
                logger.warning(f"No tickers in watchlist for trader {trader.name}")
                continue

            # Get trader's current portfolio tickers
            portfolio_tickers = trading_service.get_trader_portfolio_tickers(trader.id)

            # Analyze each ticker in dynamic watchlist
            for ticker in watchlist:
                # Check API limits before making request
                can_request, reason = ApiLimitService.can_make_request(db)
                if not can_request:
                    logger.warning(f"⚠️ API limit reached: {reason}. Stopping analysis.")
                    break

                # Throttle request to respect rate limits
                ApiLimitService.throttle_request()

                # Fetch and analyze ticker
                decision = fetch_and_analyze_ticker(
                    ticker, ts, indicator_service, analysis_service, trader
                )

                # Record API call
                ApiLimitService.record_api_call(db)
                api_calls_made += 1

                if not decision:
                    continue

                # Execute trade based on decision using service
                trade_result = None

                if decision['action'] == 'buy':
                    trade_result = trading_service.execute_buy_trade(
                        trader, ticker, decision, f"{timezone} {time_of_day}"
                    )
                elif decision['action'] == 'sell' and ticker in portfolio_tickers:
                    trade_result = trading_service.execute_sell_trade(
                        trader, ticker, decision, f"{timezone} {time_of_day}"
                    )

                if trade_result:
                    results.append(trade_result)

        # Commit all trades
        db.session.commit()

        logger.info(f"✅ Completed {time_of_day} trading session for {timezone}")
        logger.info(f"   📊 Traders processed: {len(traders)}")
        logger.info(f"   📈 Trades executed: {len(results)}")
        logger.info(f"   🔌 API calls made: {api_calls_made}")

        # Update portfolio prices after trading
        try:
            price_update_result = update_portfolio_prices()
            logger.info(f"Updated {price_update_result['updated']} portfolio prices")
        except Exception as e:
            logger.error(f"Error updating portfolio prices: {str(e)}")

        # Get final API usage stats
        usage_stats = ApiLimitService.get_usage_stats(db, days=1)

        return {
            'status': 'success',
            'timezone': timezone,
            'time_of_day': time_of_day,
            'traders_processed': len(traders),
            'trades_executed': len(results),
            'api_calls_made': api_calls_made,
            'api_usage': usage_stats['today'] if usage_stats else {},
            'trades': results
        }


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

            # Use Decimal for all calculations to avoid type mismatch
            from decimal import Decimal
            portfolio_value = sum(item.total_cost for item in portfolio)
            total_value = trader.current_balance + Decimal(str(portfolio_value))
            profit_loss = total_value - trader.initial_balance
            profit_loss_pct = (profit_loss / trader.initial_balance * 100) if trader.initial_balance > 0 else Decimal('0')

            performance = {
                'trader_id': trader.id,
                'trader_name': trader.name,
                'cash_balance': float(trader.current_balance),
                'portfolio_value': float(portfolio_value),
                'total_value': float(total_value),
                'initial_balance': float(trader.initial_balance),
                'profit_loss': float(profit_loss),
                'profit_loss_pct': float(profit_loss_pct),
                'positions': len(portfolio)
            }

            results.append(performance)
            logger.info(f"{trader.name}: Total value ${total_value:.2f}, P&L: {performance['profit_loss_pct']:.2f}%")

        return {
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'traders': results
        }


def update_portfolio_prices():
    """
    Update current market prices for all tickers in ticker_prices table (single source of truth)
    This is called at the end of trading sessions to keep prices fresh
    """
    from app import app
    from models import db, Portfolio, TickerPrice

    with app.app_context():
        logger.info("Updating ticker prices...")

        # Get all unique tickers across all portfolios
        unique_tickers = db.session.query(Portfolio.ticker).filter(Portfolio.quantity > 0).distinct().all()
        tickers = [t[0] for t in unique_tickers]

        if not tickers:
            logger.info("No tickers to update")
            return {'status': 'success', 'updated': 0}

        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='json')
        updated_count = 0
        errors = []

        for ticker in tickers:
            try:
                # Fetch current price from API
                data, _ = ts.get_quote_endpoint(symbol=ticker)
                current_price = Decimal(str(data['05. price']))

                # Update or create ticker price entry (single source of truth)
                ticker_price = TickerPrice.query.filter_by(ticker=ticker).first()
                if ticker_price:
                    ticker_price.current_price = current_price
                    ticker_price.last_updated = datetime.utcnow()
                else:
                    ticker_price = TickerPrice(
                        ticker=ticker,
                        current_price=current_price,
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(ticker_price)

                updated_count += 1
                logger.info(f"Updated {ticker}: ${current_price}")

            except Exception as e:
                error_msg = f"Error updating {ticker}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Commit all updates
        db.session.commit()

        logger.info(f"Updated prices for {updated_count} tickers")

        return {
            'status': 'success' if not errors else 'partial',
            'updated': updated_count,
            'errors': errors
        }


def execute_single_trade(trader_id, ticker):
    """
    Execute a single trade for a specific trader and ticker
    Useful for manual triggering or testing
    """
    from app import app
    from models import db, Trader
    from app.services import IndicatorService, TradingAnalysisService, TradingService

    with app.app_context():
        trader = Trader.query.get(trader_id)

        if not trader:
            return {'status': 'error', 'message': 'Trader not found'}

        # Initialize services
        indicator_service = IndicatorService()
        analysis_service = TradingAnalysisService(indicator_service)
        trading_service = TradingService()

        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')

        # Analyze ticker
        decision = fetch_and_analyze_ticker(
            ticker, ts, indicator_service, analysis_service, trader
        )

        if not decision:
            return {'status': 'error', 'message': f'Could not analyze {ticker}'}

        # Execute trade
        trade_result = None
        portfolio_tickers = trading_service.get_trader_portfolio_tickers(trader.id)

        if decision['action'] == 'buy':
            trade_result = trading_service.execute_buy_trade(trader, ticker, decision, 'manual')
        elif decision['action'] == 'sell' and ticker in portfolio_tickers:
            trade_result = trading_service.execute_sell_trade(trader, ticker, decision, 'manual')

        if trade_result:
            db.session.commit()
            return {'status': 'success', 'trade': trade_result}
        else:
            return {'status': 'success', 'message': f'No trade executed (action: {decision["action"]})'}
