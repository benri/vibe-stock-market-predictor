# 📈 Vibe Stock Market Predictor

AI-powered stock market trend analysis with intelligent machine traders that automatically execute trades based on technical indicators.

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-latest-blue.svg)
![Heroku](https://img.shields.io/badge/heroku-deployed-purple.svg)

## ✨ Features

- **Real-time Stock Analysis**: Analyze any stock ticker with comprehensive technical indicators
- **Technical Indicators**: SMA (20/50), RSI, MACD, EMA, and momentum analysis
- **AI-Powered Recommendations**: Get buy/sell/hold recommendations with confidence scores
- **Machine Traders**: Create virtual traders with unique trading philosophies
- **Automated Trading**: Background workers execute trades 3x daily during market hours
- **Portfolio Tracking**: Monitor trader performance, P&L, and holdings in real-time
- **Beautiful UI**: Responsive design with gradient styling and smooth animations
- **Beginner Friendly**: Clear explanations of technical indicators and trading signals

## 📸 Screenshots

### Stock Analysis
Analyze stocks with real-time technical indicators and AI-powered recommendations:
- Enter any ticker symbols (e.g., AAPL, TSLA, MSFT)
- View moving averages, RSI, MACD, and momentum
- Get clear buy/sell/hold signals with confidence scores
- See key trading signals and price trends

### Machine Traders
Create and manage virtual traders with unique personalities:
- Configure starting balance and risk tolerance
- Define trading philosophy (bullish, bearish, value-focused, etc.)
- Track performance metrics and P&L
- View portfolio holdings and trade history
- Automated trading during market hours

## 🛠️ Technology Stack

- **Backend**: Flask (Python 3.11)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Scheduling**: GitHub Actions for automated trading
- **Market Data**: Alpha Vantage API
- **Frontend**: Vanilla JavaScript + Modern CSS
- **Deployment**: Heroku (Cloud Native Buildpacks)

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL
- Alpha Vantage API key ([Get one free](https://www.alphavantage.co/support/#api-key))

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/benri/vibe-stock-market-predictor.git
   cd vibe-stock-market-predictor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```
   ALPHA_VANTAGE_API_KEY=your_api_key_here
   DATABASE_URL=postgresql://localhost/vibe-stock-market-predictor-development
   ```

4. **Create and initialize the database**
   ```bash
   # Create the PostgreSQL database
   ./create_db.sh

   # Run database migrations
   mise exec -- flask db upgrade

   # (Optional) Seed with sample data
   mise exec -- python seed_data.py
   ```

   Or manually:
   ```bash
   createdb vibe-stock-market-predictor-development
   mise exec -- flask db upgrade
   ```

5. **Run the application**

   ```bash
   python app.py
   ```

   Note: Automated trading is handled by GitHub Actions. See SCHEDULER_SETUP.md for setup instructions.

6. **Open your browser**
   ```
   http://localhost:5000
   ```

## 🎯 Usage

### Analyzing Stocks

1. Navigate to the **Stock Analysis** tab
2. Enter one or more ticker symbols (comma-separated)
3. Click **Analyze Stocks**
4. Review the technical indicators and recommendations
5. Use quick picks for popular stock categories (Tech Giants, EV Stocks, etc.)

### Managing Machine Traders

1. Switch to the **Machine Traders** tab
2. Click **+ New Trader** to create a trader
3. Configure:
   - **Name**: Give your trader a unique name
   - **Initial Balance**: Set starting capital ($100 minimum)
   - **Risk Tolerance**: Choose Low, Medium, or High
   - **Trading Ethos**: Describe the trader's philosophy (e.g., "Bullish on tech, focuses on growth companies")
4. Click **Create Trader**
5. View trader performance, edit settings, or delete traders

### Understanding Recommendations

- **Strong Buy** (80-95% confidence): Multiple bullish signals aligned
- **Buy** (65-80% confidence): Positive technical indicators
- **Hold** (50-65% confidence): Mixed or neutral signals
- **Sell** (65-80% confidence): Negative technical indicators
- **Strong Sell** (80-95% confidence): Multiple bearish signals aligned

## 📊 Technical Indicators Explained

| Indicator | Purpose | Interpretation |
|-----------|---------|----------------|
| **20-Day MA** | Short-term trend | Price above = bullish, below = bearish |
| **50-Day MA** | Long-term trend | Price above both MAs = strong uptrend |
| **RSI** | Momentum strength | <30 = oversold (buy), >70 = overbought (sell) |
| **MACD** | Trend changes | Bullish/bearish crossovers signal buy/sell |
| **Momentum** | Price velocity | Positive = growth, negative = decline |

## 🤖 Automated Trading

Machine traders execute trades automatically at:
- **9:45 AM EST** - Morning session
- **12:30 PM EST** - Midday session
- **3:00 PM EST** - Afternoon session
- **4:30 PM EST** - Portfolio health check

Traders analyze a watchlist of popular stocks: AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META

### Position Sizing

- **Low Risk**: 5% of balance per trade
- **Medium Risk**: 10% of balance per trade
- **High Risk**: 15% of balance per trade

## 🚢 Deployment

### Heroku Deployment

1. **Create a Heroku app**
   ```bash
   heroku create your-app-name
   ```

2. **Add PostgreSQL addon**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

3. **Set environment variables**
   ```bash
   heroku config:set ALPHA_VANTAGE_API_KEY=your_api_key
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

6. **Scale dynos**
   ```bash
   heroku ps:scale web=1
   ```

7. **Set up GitHub Actions** - See SCHEDULER_SETUP.md for automated trading setup

## 🧪 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | Analyze stock tickers |
| GET | `/api/traders` | List all traders |
| POST | `/api/traders` | Create new trader |
| GET | `/api/traders/:id` | Get trader details |
| PUT | `/api/traders/:id` | Update trader |
| DELETE | `/api/traders/:id` | Delete trader |
| GET | `/api/traders/:id/trades` | Get trader's trades |
| POST | `/api/traders/:id/trades` | Execute a trade |
| GET | `/api/traders/:id/portfolio` | Get trader's portfolio |

## 📝 Project Structure

```
vibe-stock-market-predictor/
├── app.py                 # Flask application and REST API
├── models.py              # Database models (Trader, Trade, Portfolio)
├── tasks.py               # Trading task functions
├── requirements.txt       # Python dependencies
├── Procfile               # Heroku process types
├── runtime.txt            # Python version
├── .env.example           # Environment variables template
├── CLAUDE.md              # Technical documentation for developers
├── MIGRATIONS.md          # Database migration guide
├── README.md              # This file
├── create_db.sh           # Database creation script
├── release.sh             # Heroku release phase script
├── migrations/            # Flask-Migrate database migrations
├── src/                   # Backend services and utilities
│   ├── services/         # Business logic services
│   ├── models/           # Pydantic schemas
│   └── config/           # Configuration files
├── web/                   # Frontend files
│   ├── templates/        # Jinja2 HTML templates
│   ├── js/              # JavaScript components
│   └── style.css        # Styling and animations
└── tests/                # Test suite
```

### Database Migrations

This project uses **Flask-Migrate** (Alembic) for database schema management:

- **create_db.sh**: Creates the PostgreSQL database for local development
  - Interactive script that checks if database exists
  - Prompts before dropping existing database
  - Works on macOS and Linux

- **Flask-Migrate**: Industry-standard migration system
  - `flask db migrate -m "message"` - Generate migrations from model changes
  - `flask db upgrade` - Apply migrations to database
  - `flask db downgrade` - Rollback migrations
  - See `MIGRATIONS.md` for detailed guide

- **release.sh**: Heroku release phase script
  - Runs automatically during deployment
  - Ensures database is set up before app starts
  - Part of Heroku's deployment pipeline

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ALPHA_VANTAGE_API_KEY` | API key for stock data | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SCHEDULER_API_KEY` | API key for GitHub Actions | Yes (for automation) |
| `PORT` | Server port (default: 5000) | No |

## 🐛 Troubleshooting

### API Rate Limits

Alpha Vantage free tier allows:
- 25 API requests per day
- 5 API requests per minute

If you hit rate limits, consider upgrading your API plan or implementing caching.

### Automated Trading Not Running

Check GitHub Actions:
1. Go to your repository's Actions tab
2. Verify workflows are enabled
3. Check for any failed workflow runs
4. Ensure SCHEDULER_API_KEY is set in GitHub Secrets

### Database Connection Issues

Verify DATABASE_URL is set correctly:
```bash
heroku config:get DATABASE_URL
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- [Alpha Vantage](https://www.alphavantage.co/) for free stock market data API
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [GitHub Actions](https://docs.github.com/en/actions) for automated scheduling
- Technical analysis concepts from traditional trading strategies

## 📞 Support

For technical documentation and AI agent guidance, see [CLAUDE.md](CLAUDE.md).

For issues or questions, please open an issue on GitHub.

---

Made with ❤️ for traders who want to learn technical analysis and experiment with automated trading strategies.
