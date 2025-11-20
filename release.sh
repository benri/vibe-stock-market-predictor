#!/bin/bash
# Heroku release phase script
# This script runs automatically during deployment before the app starts

set -e

echo "🚀 Running Heroku release phase..."

# Run database setup
echo "📊 Setting up database..."
python setup_db.py

echo "✅ Release phase complete!"
