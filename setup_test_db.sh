#!/bin/bash
# Setup test database for running tests

set -e

DB_NAME="vibe-stock-market-predictor-test"

echo "🧪 Setting up test database: $DB_NAME"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed or not in PATH"
    exit 1
fi

# Drop test database if it exists
if psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "🗑️  Dropping existing test database..."
    dropdb "$DB_NAME" || true
fi

# Create test database
echo "🏗️  Creating test database..."
createdb "$DB_NAME"

echo "✅ Test database '$DB_NAME' created successfully!"
echo ""
echo "Run tests with:"
echo "  pytest                           # Run all tests"
echo "  pytest tests/test_models.py      # Run model tests only"
echo "  pytest -v                        # Verbose output"
echo "  pytest --cov                     # With coverage report"
