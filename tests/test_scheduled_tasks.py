"""
Tests for scheduled task API endpoints
"""

import pytest
import os
from unittest.mock import patch, MagicMock


def test_scheduler_health_endpoint(client):
    """Test the health check endpoint (no auth required)"""
    response = client.get('/api/scheduled/health')

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert 'message' in data


def test_execute_trades_without_api_key(client):
    """Test that execute-trades endpoint requires API key"""
    response = client.post('/api/scheduled/execute-trades', json={
        'timezone': 'America/New_York',
        'time_of_day': 'morning'
    })

    assert response.status_code == 401
    data = response.get_json()
    assert 'Unauthorized' in data['error']


def test_execute_trades_with_invalid_api_key(client):
    """Test that execute-trades endpoint rejects invalid API key"""
    response = client.post('/api/scheduled/execute-trades',
        headers={'X-API-Key': 'invalid-key'},
        json={
            'timezone': 'America/New_York',
            'time_of_day': 'morning'
        })

    assert response.status_code == 401
    data = response.get_json()
    assert 'Unauthorized' in data['error']


def test_execute_trades_with_valid_api_key(client, app):
    """Test that execute-trades endpoint works with valid API key"""
    # Mock the trading task to avoid actual execution
    with patch('tasks.execute_trader_decisions_by_timezone') as mock_task:
        mock_task.return_value = {
            'status': 'success',
            'timezone': 'America/New_York',
            'time_of_day': 'morning',
            'traders_processed': 2,
            'trades_executed': 5,
            'trades': []
        }

        # Get the API key from app config
        with app.app_context():
            api_key = os.getenv('SCHEDULER_API_KEY', 'change-me-in-production')

        response = client.post('/api/scheduled/execute-trades',
            headers={'X-API-Key': api_key},
            json={
                'timezone': 'America/New_York',
                'time_of_day': 'morning'
            })

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'result' in data
        assert data['result']['timezone'] == 'America/New_York'


def test_execute_trades_with_api_key_in_query_string(client, app):
    """Test that API key can be passed as query parameter"""
    with patch('tasks.execute_trader_decisions_by_timezone') as mock_task:
        mock_task.return_value = {
            'status': 'success',
            'timezone': 'Europe/London',
            'time_of_day': 'midday',
            'traders_processed': 0,
            'trades_executed': 0,
            'trades': []
        }

        with app.app_context():
            api_key = os.getenv('SCHEDULER_API_KEY', 'change-me-in-production')

        response = client.post(f'/api/scheduled/execute-trades?api_key={api_key}',
            json={
                'timezone': 'Europe/London',
                'time_of_day': 'midday'
            })

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'


def test_execute_trades_with_default_parameters(client, app):
    """Test that execute-trades uses defaults if no parameters provided"""
    with patch('tasks.execute_trader_decisions_by_timezone') as mock_task:
        mock_task.return_value = {
            'status': 'success',
            'timezone': 'America/New_York',
            'time_of_day': 'morning',
            'traders_processed': 0,
            'trades_executed': 0,
            'trades': []
        }

        with app.app_context():
            api_key = os.getenv('SCHEDULER_API_KEY', 'change-me-in-production')

        # Send POST with empty JSON
        response = client.post('/api/scheduled/execute-trades',
            headers={'X-API-Key': api_key},
            json={})

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        # Should use defaults: America/New_York, morning
        mock_task.assert_called_once_with('America/New_York', 'morning')


def test_execute_trades_error_handling(client, app):
    """Test that execute-trades handles errors gracefully"""
    with patch('tasks.execute_trader_decisions_by_timezone') as mock_task:
        mock_task.side_effect = Exception('Database connection error')

        with app.app_context():
            api_key = os.getenv('SCHEDULER_API_KEY', 'change-me-in-production')

        response = client.post('/api/scheduled/execute-trades',
            headers={'X-API-Key': api_key},
            json={
                'timezone': 'America/New_York',
                'time_of_day': 'morning'
            })

        assert response.status_code == 500
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Database connection error' in data['message']


def test_portfolio_health_check_without_api_key(client):
    """Test that portfolio-health-check endpoint requires API key"""
    response = client.post('/api/scheduled/portfolio-health-check')

    assert response.status_code == 401
    data = response.get_json()
    assert 'Unauthorized' in data['error']


def test_portfolio_health_check_with_valid_api_key(client, app):
    """Test portfolio health check endpoint with valid API key"""
    with patch('tasks.portfolio_health_check') as mock_task:
        mock_task.return_value = {
            'status': 'success',
            'timestamp': '2025-11-19T12:00:00',
            'traders': [
                {
                    'trader_id': 1,
                    'trader_name': 'Test Trader',
                    'cash_balance': 10000.0,
                    'portfolio_value': 5000.0,
                    'total_value': 15000.0,
                    'initial_balance': 10000.0,
                    'profit_loss': 5000.0,
                    'profit_loss_pct': 50.0,
                    'positions': 3
                }
            ]
        }

        with app.app_context():
            api_key = os.getenv('SCHEDULER_API_KEY', 'change-me-in-production')

        response = client.post('/api/scheduled/portfolio-health-check',
            headers={'X-API-Key': api_key})

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'result' in data
        assert len(data['result']['traders']) == 1
        assert data['result']['traders'][0]['trader_name'] == 'Test Trader'


def test_portfolio_health_check_error_handling(client, app):
    """Test portfolio health check error handling"""
    with patch('tasks.portfolio_health_check') as mock_task:
        mock_task.side_effect = Exception('Portfolio calculation error')

        with app.app_context():
            api_key = os.getenv('SCHEDULER_API_KEY', 'change-me-in-production')

        response = client.post('/api/scheduled/portfolio-health-check',
            headers={'X-API-Key': api_key})

        assert response.status_code == 500
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Portfolio calculation error' in data['message']


def test_all_timezones_supported(client, app):
    """Test that all supported timezones work"""
    timezones = ['America/New_York', 'Europe/London', 'Asia/Tokyo']

    with patch('tasks.execute_trader_decisions_by_timezone') as mock_task:
        mock_task.return_value = {
            'status': 'success',
            'traders_processed': 0,
            'trades_executed': 0,
            'trades': []
        }

        with app.app_context():
            api_key = os.getenv('SCHEDULER_API_KEY', 'change-me-in-production')

        for timezone in timezones:
            response = client.post('/api/scheduled/execute-trades',
                headers={'X-API-Key': api_key},
                json={
                    'timezone': timezone,
                    'time_of_day': 'morning'
                })

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'


def test_all_time_of_day_options_supported(client, app):
    """Test that all time_of_day options work"""
    time_options = ['morning', 'midday', 'afternoon', 'closing']

    with patch('tasks.execute_trader_decisions_by_timezone') as mock_task:
        mock_task.return_value = {
            'status': 'success',
            'traders_processed': 0,
            'trades_executed': 0,
            'trades': []
        }

        with app.app_context():
            api_key = os.getenv('SCHEDULER_API_KEY', 'change-me-in-production')

        for time_option in time_options:
            response = client.post('/api/scheduled/execute-trades',
                headers={'X-API-Key': api_key},
                json={
                    'timezone': 'America/New_York',
                    'time_of_day': time_option
                })

            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'


def test_portfolio_health_check_actual_execution(client, app, db):
    """
    Regression test: portfolio health check should work without nested app context errors

    This test calls the actual portfolio_health_check function (not mocked)
    to ensure it doesn't create conflicting app contexts.
    """
    from models import Trader, TraderStatus
    from decimal import Decimal

    # Create a test trader
    trader = Trader(
        name='Health Check Test Trader',
        status=TraderStatus.ACTIVE,
        initial_balance=Decimal('10000.00'),
        current_balance=Decimal('10500.00'),
        risk_tolerance='medium',
        trading_timezone='America/New_York'
    )
    db.session.add(trader)
    db.session.commit()

    # Get API key
    with app.app_context():
        api_key = os.getenv('SCHEDULER_API_KEY', 'change-me-in-production')

    # Call the endpoint (NOT mocking the task function)
    response = client.post('/api/scheduled/portfolio-health-check',
        headers={'X-API-Key': api_key})

    # Should not return 500 error from nested app context
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.get_json()}"

    data = response.get_json()
    assert data['status'] == 'success'
    assert 'result' in data
    assert 'traders' in data['result']

    # Find our test trader in results
    test_trader_result = next(
        (t for t in data['result']['traders'] if t['trader_name'] == 'Health Check Test Trader'),
        None
    )
    assert test_trader_result is not None
    assert test_trader_result['cash_balance'] == 10500.00
    assert test_trader_result['initial_balance'] == 10000.00
