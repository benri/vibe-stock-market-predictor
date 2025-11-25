# Hybrid Dynamic Watchlist System

## Overview

The Hybrid Dynamic Watchlist System enables traders to analyze a broad pool of stock tickers without hitting API rate limits. It combines portfolio-first prioritization, intelligent rotation, and custom watchlist support.

## Key Features

### 1. **Dynamic Ticker Pools**
- Automatically fetches tickers from major indices:
  - **S&P 500** (~500 US stocks)
  - **FTSE 100** (UK/LSE stocks)
  - **Nikkei 225** (Japanese/TSE stocks)
- Updates via Wikipedia (no API limits)
- Expandable to custom ticker lists

### 2. **Portfolio-First Prioritization**
- **Always** analyzes tickers currently held in portfolio
- Then analyzes 5-8 discovery tickers per session
- Ensures you never miss sell opportunities

### 3. **Random Rotation Strategy**
- Randomly selects discovery tickers from pool each session
- Ensures broad market coverage over time
- Tracks analysis history per trader

### 4. **Per-Trader Custom Watchlists**
- Each trader can define their own ticker list
- Optional: Use timezone-based pool or custom list
- Configurable analysis budget (watchlist_size)

### 5. **Rate Limit Management**
- Automatic API quota tracking (25 calls/day limit)
- Request caching (15-minute expiry)
- Throttling (12-second delay between calls)
- Aborts sessions if insufficient quota

## Architecture

### Database Models

**TickerPool** - Stores available tickers
- Fields: ticker, name, exchange, timezone, sector, source, is_active
- Indexed by: ticker, exchange, timezone, sector
- Sources: sp500, ftse100, nikkei225, custom

**TickerRotation** - Tracks analysis history
- Fields: ticker, timezone, trader_id, last_analyzed_at, analysis_count
- Unique per ticker-timezone-trader combination

**ApiUsageLog** - Tracks daily API calls
- Fields: date, call_count, last_reset
- Prevents exceeding rate limits

**Trader (updated)** - Custom watchlist support
- New fields:
  - `custom_watchlist` (JSON array of tickers)
  - `watchlist_size` (int, default 6)
  - `use_custom_watchlist` (boolean, default False)

### Services

**WatchlistService** (`src/services/watchlist_service.py`)
- `get_priority_tickers()` - Main method for getting watchlist
- `set_custom_watchlist()` - Configure trader's custom list
- `get_analysis_history()` - View rotation history

**TickerSourceService** (`src/services/ticker_source_service.py`)
- `fetch_sp500_tickers()` - Scrape S&P 500 from Wikipedia
- `fetch_ftse100_tickers()` - Scrape FTSE 100
- `fetch_nikkei225_tickers()` - Scrape Nikkei 225
- `refresh_ticker_pools()` - Update database from sources

**ApiLimitService** (`src/services/api_limit_service.py`)
- `can_make_request()` - Check if quota available
- `throttle_request()` - Enforce 12-second delay
- `record_api_call()` - Track usage
- `get_usage_stats()` - View API consumption

## Usage

### Setup & Migration

1. **Run the migration:**
```bash
python migrate_watchlist_system.py
```

This will:
- Add custom watchlist fields to traders table
- Create new tables (ticker_pool, ticker_rotation, api_usage_log)
- Seed initial ticker data

2. **Update ticker pools (optional):**
```bash
python scripts/update_ticker_pools.py
```

Refreshes ticker lists from Wikipedia (run weekly/monthly).

### API Endpoints

#### Trader Watchlist Management

**Get trader's watchlist configuration:**
```bash
GET /api/traders/{trader_id}/watchlist
```

**Set custom watchlist:**
```bash
PUT /api/traders/{trader_id}/watchlist
Body: {
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "watchlist_size": 8
}
```

**Clear custom watchlist (revert to timezone pool):**
```bash
DELETE /api/traders/{trader_id}/watchlist
```

**View available ticker pool:**
```bash
GET /api/traders/{trader_id}/watchlist/pool
```

**View analysis history:**
```bash
GET /api/traders/{trader_id}/watchlist/history?limit=50
```

#### Ticker Pool Management

**Get ticker pool with filters:**
```bash
GET /api/ticker-pool?timezone=America/New_York&sector=Technology&active_only=true
```

**Get ticker pool statistics:**
```bash
GET /api/ticker-pool/stats
```

**Refresh ticker pool from Wikipedia:**
```bash
POST /api/ticker-pool/refresh
Headers: X-API-Key: your-api-key
```

#### Monitoring

**Get API usage statistics:**
```bash
GET /api/api-usage?days=7
```

**Get watchlist usage statistics:**
```bash
GET /api/watchlist/stats
```

### Trading Execution Flow

When a trading session runs (`execute_trader_decisions_by_timezone()`):

1. **Check API capacity** - Estimate if enough quota for all traders
2. **For each trader:**
   - Get portfolio tickers (priority 1)
   - Get 5-8 discovery tickers (custom or pool-based)
   - Random selection for rotation
3. **For each ticker:**
   - Check if API quota available
   - Throttle request (12-second delay)
   - Fetch and analyze
   - Record API call
   - Execute trade if signal generated
4. **Track rotation** - Update `ticker_rotation` table
5. **Return stats** - Include API usage info

### Example: Trader Configuration

**Trader using timezone-based pool:**
```json
{
  "name": "Tech Trader",
  "trading_timezone": "America/New_York",
  "watchlist_size": 6,
  "use_custom_watchlist": false
}
```
→ Analyzes portfolio + 6 random tickers from US market pool

**Trader with custom watchlist:**
```json
{
  "name": "FAANG Specialist",
  "trading_timezone": "America/New_York",
  "custom_watchlist": ["AAPL", "AMZN", "NFLX", "GOOGL", "META"],
  "watchlist_size": 3,
  "use_custom_watchlist": true
}
```
→ Analyzes portfolio + 3 random picks from custom 5-ticker list

## Rate Limiting Strategy

### Alpha Vantage Free Tier
- **Daily limit:** 25 requests/day
- **Per-minute limit:** 5 requests/minute
- **Safety buffer:** Reserve 2 calls

### How We Stay Under Limits

**Before (old system):**
- 3 sessions/day × 7 tickers × 2 traders = **42 API calls/day** ❌ Exceeds limit!

**After (new system):**
- Portfolio tickers: ~2-3/trader
- Discovery tickers: 5-8/trader (random rotation)
- Total per session: ~6-8 calls/trader
- 3 sessions/day × 6 calls × 2 traders = **36 calls/day** with 1 trader
- Adaptive: Aborts if quota exceeded

**Optimizations:**
1. **Caching:** 15-minute cache prevents duplicate calls
2. **Throttling:** 12-second delay respects per-minute limit
3. **Rotation:** Different tickers each session spreads coverage
4. **Portfolio-first:** Never miss important sell signals

## Maintenance

### Weekly Tasks
1. **Update ticker pools:**
   ```bash
   python scripts/update_ticker_pools.py
   ```

2. **Review API usage:**
   ```bash
   curl https://your-app.com/api/api-usage?days=7
   ```

### Monitoring
- Check `/api/api-usage` endpoint daily
- Alert if usage > 20 calls/day
- Review `/api/watchlist/stats` for rotation coverage

### GitHub Actions Integration
Create `.github/workflows/update-ticker-pools.yml`:
```yaml
name: Update Ticker Pools
on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Update ticker pools
        run: |
          curl -X POST https://your-app.herokuapp.com/api/ticker-pool/refresh \
               -H "X-API-Key: ${{ secrets.SCHEDULER_API_KEY }}"
```

## Troubleshooting

### API Limit Exceeded
```json
{
  "status": "aborted",
  "message": "Insufficient API quota remaining"
}
```
**Solution:** Wait until next day, or reduce number of active traders

### No Tickers in Watchlist
```
WARNING: No tickers in watchlist for trader X
```
**Solution:** Check `ticker_pool` table has data for trader's timezone

### Rotation Not Working
Check `ticker_rotation` table for recent updates:
```sql
SELECT * FROM ticker_rotation
WHERE trader_id = X
ORDER BY last_analyzed_at DESC
LIMIT 10;
```

## Future Enhancements

- **Sector-balanced rotation** - Ensure coverage across sectors
- **Volume-weighted selection** - Prioritize high-volume stocks
- **Machine learning** - Predict which tickers likely to have trading signals
- **Multi-exchange support** - Add more international markets
- **Custom data sources** - Support CSV upload for ticker pools

---

**Version:** 1.0.0
**Last Updated:** 2025-11-25
