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
# Market hours: 9:30 AM - 4:00 PM EST, Monday-Friday
celery_app.conf.beat_schedule = {
    'execute-morning-trades': {
        'task': 'tasks.execute_all_trader_decisions',
        'schedule': crontab(hour=9, minute=45, day_of_week='mon-fri'),  # 9:45 AM EST
        'args': ('morning',),
    },
    'execute-midday-trades': {
        'task': 'tasks.execute_all_trader_decisions',
        'schedule': crontab(hour=12, minute=30, day_of_week='mon-fri'),  # 12:30 PM EST
        'args': ('midday',),
    },
    'execute-afternoon-trades': {
        'task': 'tasks.execute_all_trader_decisions',
        'schedule': crontab(hour=15, minute=0, day_of_week='mon-fri'),  # 3:00 PM EST
        'args': ('afternoon',),
    },
    'portfolio-health-check': {
        'task': 'tasks.portfolio_health_check',
        'schedule': crontab(hour=16, minute=30, day_of_week='mon-fri'),  # 4:30 PM EST (after market close)
    },
}

if __name__ == '__main__':
    celery_app.start()
