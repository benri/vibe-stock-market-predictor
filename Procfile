release: bash release.sh
web: gunicorn app:app

# Worker and beat dynos removed - using GitHub Actions for scheduled tasks
# This saves money by eliminating the need for background dynos
# Trading tasks are triggered via API endpoints by GitHub Actions workflows
