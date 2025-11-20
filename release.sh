#!/bin/bash
# Heroku release phase script
# This script runs automatically during deployment before the app starts

set -e

echo "🚀 Running Heroku release phase..."

# Run database migrations first
echo "🔄 Running database migrations..."
python migrate_db.py

# Run database setup (creates tables if they don't exist)
echo "📊 Setting up database tables..."
python setup_db.py || echo "⚠️  Setup encountered an issue, but migrations ran successfully"

echo "✅ Release phase complete!"
