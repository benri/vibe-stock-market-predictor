release: bash release.sh
web: gunicorn app:app
worker: celery -A celery_app worker --loglevel=info
beat: celery -A celery_app beat --loglevel=info
