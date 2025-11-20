#!/bin/bash
# Database creation script for local development
# This script creates the PostgreSQL database for the application

set -e

DB_NAME="vibe-stock-market-predictor-development"

echo "🔧 Creating PostgreSQL database: $DB_NAME"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed or not in PATH"
    echo "Please install PostgreSQL first:"
    echo "  macOS: brew install postgresql"
    echo "  Ubuntu: sudo apt-get install postgresql"
    exit 1
fi

# Check if database already exists
if psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "⚠️  Database '$DB_NAME' already exists"
    read -p "Do you want to drop and recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Dropping existing database..."
        dropdb "$DB_NAME" || true
    else
        echo "✅ Using existing database"
        exit 0
    fi
fi

# Create the database
echo "🏗️  Creating database..."
createdb "$DB_NAME"

echo "✅ Database '$DB_NAME' created successfully!"
echo ""
echo "Next steps:"
echo "1. Set up environment variables: cp .env.example .env"
echo "2. Edit .env and add your ALPHA_VANTAGE_API_KEY"
echo "3. Run database setup: python setup_db.py"
