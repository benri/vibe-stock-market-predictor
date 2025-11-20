import os
import ssl
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Redis URL from environment
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Configure SSL for Redis if using rediss:// (Heroku Redis)
broker_use_ssl = None
redis_backend_use_ssl = None

if REDIS_URL and REDIS_URL.startswith('rediss://'):
    # SSL configuration for Heroku Redis
    broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }
    redis_backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
    }

# Create Celery app
celery_app = Celery(
    'vibe_stock_predictor',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/New_York',  # NYSE timezone
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes soft limit
    broker_use_ssl=broker_use_ssl,
    redis_backend_use_ssl=redis_backend_use_ssl,
)

# Celery Beat schedule for automated trading
# Configured for multiple timezones and exchanges
#
# NYSE (America/New_York): 9:30 AM - 4:00 PM EST, Mon-Fri
#   - Trading starts at 7:00 AM PST / 10:00 AM EST
# LSE (Europe/London): 8:00 AM - 4:30 PM GMT, Mon-Fri
# TSE (Asia/Tokyo): 9:00 AM - 3:00 PM JST, Mon-Fri (with lunch break 11:30-12:30)
celery_app.conf.beat_schedule = {
    # NYSE Trading Sessions (America/New_York)
    'nyse-morning-trades': {
        'task': 'tasks.execute_trader_decisions_by_timezone',
        'schedule': crontab(hour=10, minute=0, day_of_week='mon-fri'),  # 10:00 AM EST = 7:00 AM PST
        'args': ('America/New_York', 'morning'),
    },
    'nyse-midday-trades': {
        'task': 'tasks.execute_trader_decisions_by_timezone',
        'schedule': crontab(hour=12, minute=30, day_of_week='mon-fri'),  # 12:30 PM EST = 9:30 AM PST
        'args': ('America/New_York', 'midday'),
    },
    'nyse-afternoon-trades': {
        'task': 'tasks.execute_trader_decisions_by_timezone',
        'schedule': crontab(hour=15, minute=0, day_of_week='mon-fri'),  # 3:00 PM EST = 12:00 PM PST
        'args': ('America/New_York', 'afternoon'),
    },

    # LSE Trading Sessions (Europe/London)
    'lse-morning-trades': {
        'task': 'tasks.execute_trader_decisions_by_timezone',
        'schedule': crontab(hour=8, minute=30, day_of_week='mon-fri'),  # 8:30 AM GMT
        'args': ('Europe/London', 'morning'),
    },
    'lse-midday-trades': {
        'task': 'tasks.execute_trader_decisions_by_timezone',
        'schedule': crontab(hour=12, minute=0, day_of_week='mon-fri'),  # 12:00 PM GMT
        'args': ('Europe/London', 'midday'),
    },
    'lse-afternoon-trades': {
        'task': 'tasks.execute_trader_decisions_by_timezone',
        'schedule': crontab(hour=15, minute=30, day_of_week='mon-fri'),  # 3:30 PM GMT
        'args': ('Europe/London', 'afternoon'),
    },

    # TSE Trading Sessions (Asia/Tokyo)
    'tse-morning-trades': {
        'task': 'tasks.execute_trader_decisions_by_timezone',
        'schedule': crontab(hour=9, minute=30, day_of_week='mon-fri'),  # 9:30 AM JST
        'args': ('Asia/Tokyo', 'morning'),
    },
    'tse-afternoon-trades': {
        'task': 'tasks.execute_trader_decisions_by_timezone',
        'schedule': crontab(hour=13, minute=0, day_of_week='mon-fri'),  # 1:00 PM JST (after lunch)
        'args': ('Asia/Tokyo', 'afternoon'),
    },
    'tse-closing-trades': {
        'task': 'tasks.execute_trader_decisions_by_timezone',
        'schedule': crontab(hour=14, minute=30, day_of_week='mon-fri'),  # 2:30 PM JST
        'args': ('Asia/Tokyo', 'closing'),
    },

    # Portfolio health check (runs once daily for all traders)
    'portfolio-health-check': {
        'task': 'tasks.portfolio_health_check',
        'schedule': crontab(hour=16, minute=30, day_of_week='mon-fri'),  # 4:30 PM EST (after NYSE close)
    },
}

if __name__ == '__main__':
    celery_app.start()
