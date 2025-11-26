#!/bin/bash
# Heroku release phase script
# This script runs automatically during deployment before the app starts

set -e

echo "🚀 Running Heroku release phase..."

# Run database migrations using Flask-Migrate
echo "🔄 Running database migrations..."
flask db upgrade

echo "✅ Release phase complete!"
