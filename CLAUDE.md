# Vibe Stock Market Predictor

**AI-powered stock market analysis and automated trading platform with intelligent machine traders**

[![GitHub](https://img.shields.io/badge/github-repo-blue)](https://github.com/benri/vibe-stock-market-predictor)

## 🎯 Project Vision & Goals

### Primary Vision
Create an intelligent, autonomous stock trading platform that combines technical analysis with AI-driven decision making through personalized machine traders, each with unique trading philosophies and risk profiles.

### Core Goals
1. **Automated Trading Intelligence** - Machine traders that autonomously execute trades during market hours based on technical analysis
2. **Personalized Trading Strategies** - Each trader has a unique "ethos" that can be used to guide decision making (ready for LLM integration)
3. **Performance Tracking** - Real-time monitoring of trader performance, P&L, and portfolio holdings
4. **Educational Tool** - Help users understand technical indicators and market dynamics through visualization
5. **Scalable Architecture** - Support multiple concurrent traders with different strategies

### Future Roadmap
- [ ] **LLM Integration** - Use trader ethos to influence trading decisions via GPT/Claude
- [ ] **Advanced Strategies** - Support for options, futures, and other instruments
- [ ] **Social Features** - Share trader configurations and performance with community
- [ ] **Backtesting Engine** - Test strategies against historical data before deployment
- [ ] **Real-Time Alerts** - Notify users of significant trades or portfolio changes
- [ ] **Machine Learning** - Learn from successful traders to improve decision making
- [ ] **Multi-Exchange Support** - Expand beyond stocks to crypto, forex, etc.

---

## 🏗️ Project Architecture

### Tech Stack
- **Backend:** Python 3.12, Flask, SQLAlchemy
- **Database:** PostgreSQL (Heroku Postgres)
- **Queue/Cache:** Redis (Heroku Redis)
- **Task Queue:** Celery with Celery Beat for scheduled jobs
- **Market Data:** Alpha Vantage API (free tier, 25 requests/day)
- **Deployment:** Heroku with Cloud Native Buildpacks
- **Frontend:** Vanilla JavaScript, CSS3 with modern gradients

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐   │
│  │ Stock        │  │ Trader         │  │ Performance  │   │
│  │ Analysis     │  │ Management     │  │ Dashboard    │   │
│  └──────────────┘  └────────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      FLASK REST API                          │
│  • /analyze - Stock analysis                                 │
│  • /api/traders - CRUD for traders                          │
│  • /api/traders/<id>/trades - Trade execution & history    │
│  • /api/traders/<id>/portfolio - Portfolio management      │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴──────────┐
                ↓                      ↓
┌──────────────────────┐  ┌─────────────────────────┐
│  POSTGRESQL DB       │  │  CELERY WORKERS         │
│  • Traders           │  │  • Morning trades (9:45) │
│  • Trades            │  │  • Midday trades (12:30) │
│  • Portfolio         │  │  • Evening trades (3:00) │
└──────────────────────┘  │  • Health check (4:30)  │
                          └─────────────────────────┘
                                      │
                                      ↓
                          ┌─────────────────────┐
                          │  ALPHA VANTAGE API  │
                          │  Market Data        │
                          └─────────────────────┘
```

### Database Schema

**Traders Table:**
- `id` - Primary key
- `name` - Trader name (unique)
- `status` - active | paused | disabled
- `initial_balance` - Starting capital
- `current_balance` - Current cash balance
- `strategy_name` - Strategy identifier
- `risk_tolerance` - low | medium | high
- `trading_ethos` - Free-form philosophy text (for LLM integration)
- `created_at`, `last_trade_at` - Timestamps

**Trades Table:**
- `id` - Primary key
- `trader_id` - Foreign key to traders
- `ticker` - Stock symbol
- `action` - buy | sell
- `quantity` - Number of shares
- `price` - Execution price
- `total_amount` - Total transaction value
- `balance_after` - Account balance after trade
- Technical indicators at time of trade: `rsi`, `macd`, `sma_20`, `sma_50`
- `recommendation`, `confidence` - Decision factors
- `notes` - Trade reasoning
- `executed_at` - Timestamp

**Portfolio Table:**
- `id` - Primary key
- `trader_id` - Foreign key to traders
- `ticker` - Stock symbol
- `quantity` - Number of shares held
- `average_price` - Average cost basis
- `total_cost` - Total invested
- `first_purchased_at`, `last_updated_at` - Timestamps
- Unique constraint: (trader_id, ticker)

---

## 📁 Project Structure

```
vibe-stock-market-predictor/
├── app.py                  # Flask application & REST API
├── models.py              # SQLAlchemy database models
├── celery_app.py          # Celery configuration & scheduling
├── tasks.py               # Background trading tasks
├── requirements.txt       # Python dependencies
├── Procfile              # Heroku process definitions
├── .python-version       # Python version (3.12.12)
├── .env                  # Environment variables (not in git)
├── .env.example          # Environment template
├── templates/
│   └── index.html        # Main frontend page
├── static/
│   ├── app.js           # Frontend JavaScript
│   └── style.css        # Styling & animations
└── CLAUDE.md            # This file
```

### Key Files Explained

**app.py** - Main Flask application
- REST API endpoints for traders, trades, portfolio
- Stock analysis endpoint using Alpha Vantage
- Technical indicator calculations
- Buy/sell signal generation

**models.py** - Database models
- Trader, Trade, Portfolio classes
- Enums for status types (TraderStatus, TradeAction)
- Relationships and constraints
- Serialization methods (to_dict)

**celery_app.py** - Celery configuration
- Redis broker/backend setup
- SSL configuration for Heroku
- Beat schedule for automated trading (3x daily + health check)

**tasks.py** - Background jobs
- `execute_all_trader_decisions()` - Main trading logic
- `portfolio_health_check()` - Daily performance report
- Technical indicator calculations
- Trading decision algorithm

---

## 🔧 Development Setup

### Prerequisites
- Python 3.12+
- PostgreSQL (local dev)
- Redis (local dev)
- Alpha Vantage API key

### Local Development

1. **Clone and setup environment:**
```bash
git clone https://github.com/benri/vibe-stock-market-predictor.git
cd vibe-stock-market-predictor

# Copy environment template
cp .env.example .env

# Edit .env and add your API key:
# ALPHA_VANTAGE_API_KEY=your_key_here
```

2. **Install dependencies:**
```bash
# Using mise (recommended)
mise exec -- pip install -r requirements.txt

# Or with standard pip
pip install -r requirements.txt
```

3. **Setup local database:**
```bash
# Create PostgreSQL database
createdb vibe_stock_predictor

# Run migrations (if using Flask-Migrate)
mise exec -- flask db upgrade
```

4. **Run the application:**
```bash
# Terminal 1: Flask app
PORT=5001 mise exec -- python app.py

# Terminal 2: Celery worker
mise exec -- celery -A celery_app worker --loglevel=info

# Terminal 3: Celery beat (scheduler)
mise exec -- celery -A celery_app beat --loglevel=info
```

5. **Access the app:**
- http://localhost:5001

---

## 🚀 Deployment (Heroku)

### Deploy Updates
```bash
git push heroku main
```

### Heroku Configuration
```bash
# Set environment variables
heroku config:set ALPHA_VANTAGE_API_KEY=your_key --app <app_name>

# Scale dynos
heroku ps:scale web=1 worker=1 beat=1 --app <app_name>

# View logs
heroku logs --tail --app <app_name>
```

---

## 🤖 Trading System

### Technical Indicators Used
- **SMA (20, 50)** - Simple Moving Averages for trend identification
- **EMA (12, 26)** - Exponential Moving Averages for MACD
- **MACD** - Momentum indicator (EMA12 - EMA26)
- **RSI (14)** - Relative Strength Index for overbought/oversold
- **Momentum (10-day)** - Price change percentage

### Trading Logic
Traders analyze each ticker in the watchlist and generate a score:
- **Trend signals:** +20 for strong uptrend, -20 for strong downtrend
- **RSI signals:** +15 if oversold (<30), -15 if overbought (>70)
- **MACD crossover:** +15 bullish, -15 bearish
- **Momentum:** +10 strong positive, -10 strong negative

**Risk-adjusted thresholds:**
- Low risk: ±35 score to trade
- Medium risk: ±25 score to trade
- High risk: ±15 score to trade

### Position Sizing
- Low risk: 5% of balance per trade
- Medium risk: 10% of balance per trade
- High risk: 15% of balance per trade

### Trading Schedule (EST)
- **9:45 AM** - Morning session (after market open)
- **12:30 PM** - Midday session
- **3:00 PM** - Afternoon session (before close)
- **4:30 PM** - Portfolio health check (after close)

### Watchlist
AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META

---

## 💡 Development Workflow

### Before Starting Work
1. Pull latest changes: `git pull origin main`
2. Check Heroku status: `heroku ps --app <app_name>`
3. Review recent logs: `heroku logs --tail --app <app_name>`

### Making Changes
1. Create feature branch (optional): `git checkout -b feature/your-feature`
2. Make changes and test locally
3. Run any necessary type checking or linting
4. Test with sample data before touching production

### Testing
- Test API endpoints with curl or Postman
- Verify database changes with psql or pgAdmin
- Check Celery tasks execute correctly
- Test UI in browser (Chrome DevTools)

### Committing Code
```bash
git add .
git commit -m "Clear description of changes"
git push origin main
```

### Deploying
```bash
# Push to Heroku
git push heroku main

# Monitor deployment
heroku logs --tail --app <app_name>

# Check dyno status
heroku ps --app <app_name>
```

### Important Notes
- **API Rate Limits:** Alpha Vantage free tier = 25 requests/day, 5/minute
- **Database Migrations:** Use Flask-Migrate for schema changes
- **Environment Variables:** Never commit `.env` to git
- **Trading Hours:** All times are EST (NYSE timezone)

---

## 🎨 UI Development

### Design Principles
- **Modern & Clean** - Gradient backgrounds, smooth animations
- **Responsive** - Works on mobile, tablet, desktop
- **Intuitive** - Clear CTAs, helpful tooltips
- **Performance** - Vanilla JS, no framework overhead

### Styling Guidelines
- Primary gradient: `#667eea → #764ba2`
- Success green: `#10b981`
- Error red: `#ef4444`
- Warning yellow: `#fbbf24`
- Neutral grays: `#f8f9fa`, `#e9ecef`, `#666`, `#333`

### Adding New Features
1. Update HTML structure in `templates/index.html`
2. Add styles to `static/style.css`
3. Implement functionality in `static/app.js`
4. Create backend endpoints in `app.py` if needed
5. Test responsiveness at multiple breakpoints

---

## 🔮 Future Features & Ideas

### High Priority
1. **LLM Integration** - Feed trader ethos to GPT/Claude for decision augmentation
2. **Backtesting** - Test strategies against historical data
3. **Performance Charts** - Visualize trader P&L over time
4. **Trade History View** - Detailed table of all trades with filters

### Medium Priority
5. **Email Notifications** - Alert on large trades or losses
6. **Strategy Templates** - Pre-built trader configurations
7. **Paper Trading Mode** - Test without real (simulated) money
8. **Multi-timeframe Analysis** - Support hourly, daily, weekly views

### Low Priority
9. **Social Features** - Share traders, leaderboards
10. **Custom Watchlists** - Let traders focus on specific sectors
11. **Advanced Orders** - Stop-loss, take-profit, trailing stops
12. **Mobile App** - Native iOS/Android versions

---

## 🤝 Contributing

When working on this project:

1. **Understand the Domain** - Familiarize yourself with technical indicators and trading concepts
2. **Test Thoroughly** - Trading logic bugs can lead to losses (even virtual ones!)
3. **Document Changes** - Update this CLAUDE.md file when adding features
4. **Follow Conventions** - Maintain existing code style and patterns
5. **Think About Scale** - Consider performance with 100+ traders

### Code Style
- Use type hints where helpful
- Write docstrings for complex functions
- Keep functions focused and single-purpose
- Use descriptive variable names
- Comment non-obvious logic

---

## 📚 Resources

### APIs & Services
- [Alpha Vantage Docs](https://www.alphavantage.co/documentation/)
- [Heroku Dev Center](https://devcenter.heroku.com/)
- [Celery Documentation](https://docs.celeryproject.org/)

### Trading & Finance
- [Investopedia - Technical Indicators](https://www.investopedia.com/terms/t/technicalindicator.asp)
- [Understanding RSI](https://www.investopedia.com/terms/r/rsi.asp)
- [MACD Explained](https://www.investopedia.com/terms/m/macd.asp)

### Development
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

---

## 📝 Notes for AI Agents

### Key Context
- This is a **learning/demo project**, not production trading software
- All trades are simulated with virtual money
- Focus on education and experimentation
- Prioritize code clarity over premature optimization

### When Adding Features
- Check if it requires new database migrations
- Consider Alpha Vantage API rate limits
- Test trading logic during non-market hours to avoid confusion
- Update this CLAUDE.md file with new features, but don't include specific app information / sensitive info

### Common Tasks
- **Add new indicator:** Modify `calculate_technical_indicators()` in app.py/tasks.py
- **Change trading schedule:** Update `beat_schedule` in celery_app.py
- **Add watchlist ticker:** Update watchlist in `execute_all_trader_decisions()` task
- **Modify UI:** Edit templates/index.html, static/app.js, static/style.css

### Debugging Tips
- Check Celery worker logs: `heroku logs --tail --dyno=worker`
- Verify Redis connection: `heroku redis:cli --app <app_name>`
- Test API endpoints: `curl -X POST https://<app_name>.herokuapp.com/api/traders`
- Database console: `heroku pg:psql --app <app_name>`

---

**Last Updated:** 2025-11-19
**Maintainer:** benri
**License:** MIT (or specify your license)
