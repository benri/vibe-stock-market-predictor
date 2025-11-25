"""
API Limit Service

Manages Alpha Vantage API rate limits, caching, and throttling
to ensure we stay within free tier limits (25 requests/day, 5/minute).
"""

import logging
import time
from datetime import date, datetime, timedelta
from typing import Optional, Dict
import requests_cache

logger = logging.getLogger(__name__)


class ApiLimitService:
    """Service for managing API rate limits and caching"""

    # Alpha Vantage free tier limits
    DAILY_LIMIT = 25
    MINUTE_LIMIT = 5
    SAFETY_BUFFER = 2  # Leave buffer for safety

    # Cache configuration
    CACHE_EXPIRY_SECONDS = 900  # 15 minutes

    # Rate limiting
    _last_request_time = None
    _request_count_this_minute = 0
    _minute_start_time = None

    @staticmethod
    def initialize_cache():
        """Initialize requests-cache for API responses"""
        try:
            # Use SQLite backend for cache
            requests_cache.install_cache(
                'alpha_vantage_cache',
                backend='sqlite',
                expire_after=ApiLimitService.CACHE_EXPIRY_SECONDS,
                allowable_codes=[200],  # Only cache successful responses
                allowable_methods=['GET'],
            )
            logger.info(f"✅ Initialized API cache (expires after {ApiLimitService.CACHE_EXPIRY_SECONDS}s)")
        except Exception as e:
            logger.error(f"❌ Error initializing cache: {e}")

    @staticmethod
    def can_make_request(db) -> tuple[bool, str]:
        """
        Check if we can make an API request without exceeding limits

        Args:
            db: SQLAlchemy database session

        Returns:
            Tuple of (can_make_request: bool, reason: str)
        """
        from models import ApiUsageLog

        try:
            # Check daily limit
            today = date.today()
            usage_log = ApiUsageLog.query.filter_by(date=today).first()

            if not usage_log:
                # Create new log for today
                usage_log = ApiUsageLog(date=today, call_count=0)
                db.session.add(usage_log)
                db.session.commit()

            daily_remaining = ApiLimitService.DAILY_LIMIT - usage_log.call_count - ApiLimitService.SAFETY_BUFFER

            if daily_remaining <= 0:
                return False, f"Daily limit reached ({usage_log.call_count}/{ApiLimitService.DAILY_LIMIT} calls)"

            # Check per-minute limit
            now = datetime.utcnow()

            if ApiLimitService._minute_start_time is None:
                ApiLimitService._minute_start_time = now
                ApiLimitService._request_count_this_minute = 0

            # Reset minute counter if more than 60 seconds have passed
            if (now - ApiLimitService._minute_start_time).total_seconds() >= 60:
                ApiLimitService._minute_start_time = now
                ApiLimitService._request_count_this_minute = 0

            if ApiLimitService._request_count_this_minute >= ApiLimitService.MINUTE_LIMIT:
                return False, f"Minute limit reached ({ApiLimitService._request_count_this_minute}/{ApiLimitService.MINUTE_LIMIT} calls)"

            return True, f"OK ({usage_log.call_count}/{ApiLimitService.DAILY_LIMIT} daily, {ApiLimitService._request_count_this_minute}/{ApiLimitService.MINUTE_LIMIT}/min)"

        except Exception as e:
            logger.error(f"Error checking API limits: {e}")
            return False, f"Error checking limits: {e}"

    @staticmethod
    def throttle_request():
        """
        Add delay between requests to respect per-minute limit
        Ensures we don't make more than 5 requests per minute (1 per 12 seconds)
        """
        MIN_INTERVAL_SECONDS = 12  # 60 seconds / 5 requests = 12 seconds per request

        if ApiLimitService._last_request_time:
            elapsed = time.time() - ApiLimitService._last_request_time
            if elapsed < MIN_INTERVAL_SECONDS:
                sleep_time = MIN_INTERVAL_SECONDS - elapsed
                logger.info(f"⏱️  Throttling: sleeping {sleep_time:.1f}s to respect rate limit")
                time.sleep(sleep_time)

        ApiLimitService._last_request_time = time.time()
        ApiLimitService._request_count_this_minute += 1

    @staticmethod
    def record_api_call(db):
        """
        Record an API call in the usage log

        Args:
            db: SQLAlchemy database session
        """
        from models import ApiUsageLog

        try:
            today = date.today()
            usage_log = ApiUsageLog.query.filter_by(date=today).first()

            if not usage_log:
                usage_log = ApiUsageLog(date=today, call_count=1)
                db.session.add(usage_log)
            else:
                usage_log.call_count += 1

            db.session.commit()
            logger.debug(f"Recorded API call: {usage_log.call_count}/{ApiLimitService.DAILY_LIMIT}")

        except Exception as e:
            logger.error(f"Error recording API call: {e}")
            db.session.rollback()

    @staticmethod
    def get_usage_stats(db, days: int = 7) -> Dict[str, any]:
        """
        Get API usage statistics

        Args:
            db: SQLAlchemy database session
            days: Number of days to include

        Returns:
            Dictionary with usage stats
        """
        from models import ApiUsageLog
        from sqlalchemy import func

        try:
            # Get today's usage
            today = date.today()
            today_log = ApiUsageLog.query.filter_by(date=today).first()
            today_count = today_log.call_count if today_log else 0

            # Get usage for last N days
            start_date = today - timedelta(days=days)
            recent_logs = ApiUsageLog.query.filter(
                ApiUsageLog.date >= start_date
            ).order_by(ApiUsageLog.date.desc()).all()

            # Calculate stats
            daily_usage = [{'date': log.date.isoformat(), 'calls': log.call_count} for log in recent_logs]
            total_calls = sum(log.call_count for log in recent_logs)
            avg_daily = total_calls / len(recent_logs) if recent_logs else 0

            # Remaining today
            remaining_today = max(0, ApiLimitService.DAILY_LIMIT - today_count)

            return {
                'today': {
                    'date': today.isoformat(),
                    'calls': today_count,
                    'remaining': remaining_today,
                    'limit': ApiLimitService.DAILY_LIMIT,
                    'percentage_used': (today_count / ApiLimitService.DAILY_LIMIT * 100) if ApiLimitService.DAILY_LIMIT > 0 else 0
                },
                'recent': {
                    'days': days,
                    'total_calls': total_calls,
                    'avg_daily': round(avg_daily, 1),
                    'daily_breakdown': daily_usage
                },
                'limits': {
                    'daily': ApiLimitService.DAILY_LIMIT,
                    'per_minute': ApiLimitService.MINUTE_LIMIT,
                    'cache_expiry_seconds': ApiLimitService.CACHE_EXPIRY_SECONDS
                }
            }

        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {}

    @staticmethod
    def reset_daily_usage(db, target_date: Optional[date] = None):
        """
        Reset usage counter for a specific date (mainly for testing)

        Args:
            db: SQLAlchemy database session
            target_date: Date to reset (defaults to today)
        """
        from models import ApiUsageLog

        try:
            target_date = target_date or date.today()
            usage_log = ApiUsageLog.query.filter_by(date=target_date).first()

            if usage_log:
                usage_log.call_count = 0
                usage_log.last_reset = datetime.utcnow()
                db.session.commit()
                logger.info(f"Reset API usage for {target_date}")
            else:
                logger.warning(f"No usage log found for {target_date}")

        except Exception as e:
            logger.error(f"Error resetting daily usage: {e}")
            db.session.rollback()

    @staticmethod
    def clear_cache():
        """Clear the API response cache"""
        try:
            requests_cache.clear()
            logger.info("✅ Cleared API response cache")
        except Exception as e:
            logger.error(f"❌ Error clearing cache: {e}")

    @staticmethod
    def estimate_remaining_capacity(db, traders_count: int, tickers_per_trader: int) -> Dict[str, any]:
        """
        Estimate if we have capacity for a trading session

        Args:
            db: SQLAlchemy database session
            traders_count: Number of traders
            tickers_per_trader: Average tickers per trader

        Returns:
            Dictionary with capacity estimation
        """
        from models import ApiUsageLog

        try:
            today = date.today()
            usage_log = ApiUsageLog.query.filter_by(date=today).first()
            current_usage = usage_log.call_count if usage_log else 0

            estimated_calls = traders_count * tickers_per_trader
            remaining = ApiLimitService.DAILY_LIMIT - current_usage
            can_proceed = estimated_calls <= (remaining - ApiLimitService.SAFETY_BUFFER)

            return {
                'can_proceed': can_proceed,
                'current_usage': current_usage,
                'estimated_calls': estimated_calls,
                'remaining': remaining,
                'buffer': ApiLimitService.SAFETY_BUFFER,
                'message': f"{'✅ Sufficient' if can_proceed else '❌ Insufficient'} capacity: "
                          f"{estimated_calls} calls needed, {remaining} remaining"
            }

        except Exception as e:
            logger.error(f"Error estimating capacity: {e}")
            return {
                'can_proceed': False,
                'message': f"Error estimating capacity: {e}"
            }
