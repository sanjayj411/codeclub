# Options Trading Bot v2.0

Advanced options trading bot with **Schwab broker integration**, **quantitative analysis**, RSI and Bollinger Bands indicators, and strict 10% risk management.

## 🚀 New Features (v2.0)

### Schwab Broker Integration
- Real-time price data from Schwab
- Live order execution and management
- Account monitoring and position tracking
- Options and equity trading support

### Quantitative Analysis
- Volatility calculation (Historical and Annualized)
- Sharpe Ratio for risk-adjusted returns
- Maximum Drawdown analysis
- Beta and Alpha calculations
- Correlation analysis
- Value at Risk (VaR)
- Regression analysis
- Monte Carlo simulations
- Portfolio optimization

### Enhanced Trading Signals
- Combined technical + quantitative signals
- Signal strength scoring
- Recommendation system (STRONG_BUY, BUY, WEAK_BUY, HOLD, WEAK_SELL, SELL, STRONG_SELL)
- Probability-based decision making

## 📊 Technical Indicators

### RSI (14 period)
- Overbought: > 70 (Sell signal)
- Oversold: < 30 (Buy signal)

### Bollinger Bands (20 period, 2 std dev)
- Support/resistance identification
- Volatility measurement
- Entry/exit optimization

## 💰 Risk Management

- **Maximum Risk**: 10% of account per trade
- **Position Sizing**: Automatic based on stop loss distance
- **Risk/Reward**: Minimum 1:2 ratio enforcement
- **Account Monitoring**: Real-time balance tracking

## 🔧 Installation

```bash
# Clone and navigate to project
cd /Users/sanjayj/codeclub/options-trading-bot

# Install dependencies
python3.9 -m pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your Schwab credentials
```

## 🏃 Running the Bot

### Start API Server

```bash
python3.9 -m uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
```

Server runs at: `http://127.0.0.1:8000`

### API Documentation

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Run Tests

```bash
pytest -q                    # Quick test run
pytest -v                    # Verbose output
pytest --cov=src            # With coverage
```

**Current test status**: 18+ passing tests ✅

## 📡 API Endpoints

### Technical Analysis
- `POST /signal` - Generate trading signal
- `POST /validate-trade` - Validate trade setup
- `POST /position-update` - Check position exits

### Quantitative Analysis
- `POST /quant/volatility` - Calculate volatility
- `POST /quant/sharpe` - Calculate Sharpe ratio
- `POST /quant/drawdown` - Calculate max drawdown
- `POST /quant/regression` - Regression analysis
- `POST /quant/monte-carlo` - Monte Carlo simulation

### Schwab Broker Integration
- `POST /schwab/analyze` - Comprehensive symbol analysis with Schwab data
- `POST /schwab/execute` - Execute trades on Schwab
- `POST /schwab/monitor` - Monitor open positions

### System
- `GET /health` - Health check
- `GET /indicators-info` - Indicator parameters
- `GET /features` - List all features

## 💡 Usage Examples

### 1. Comprehensive Symbol Analysis

```bash
curl -X POST http://127.0.0.1:8000/schwab/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "YOUR_ACCOUNT",
    "token": "YOUR_SCHWAB_TOKEN",
    "account_size": 10000,
    "symbol": "AAPL",
    "days": 60
  }'
```

Response includes:
- Current price and quote
- Technical signals (RSI, Bollinger Bands)
- Quantitative metrics (Volatility, Sharpe, etc.)
- Monte Carlo probability distribution
- Trading recommendation

### 2. Calculate Volatility

```bash
curl -X POST http://127.0.0.1:8000/quant/volatility \
  -H "Content-Type: application/json" \
  -d '{
    "prices": [100, 101, 102, 101, 100, 99, 98, 97, 96, 95],
    "window": 20
  }'
```

### 3. Run Monte Carlo Simulation

```bash
curl -X POST http://127.0.0.1:8000/quant/monte-carlo \
  -H "Content-Type: application/json" \
  -d '{
    "current_price": 100,
    "returns_mean": 0.001,
    "returns_std": 0.02,
    "days": 20,
    "simulations": 1000
  }'
```

Returns probability distribution of future prices.

### 4. Execute Trade on Schwab

```bash
curl -X POST http://127.0.0.1:8000/schwab/execute \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "YOUR_ACCOUNT",
    "token": "YOUR_SCHWAB_TOKEN",
    "symbol": "AAPL",
    "signal": "BUY",
    "entry": 150.50,
    "stop_loss": 145.00,
    "take_profit": 160.00,
    "contracts": 1
  }'
```

## 🐍 Python Usage

```python
from src.bot import EnhancedTradingBot

# Initialize bot
bot = EnhancedTradingBot(
    account_number="YOUR_ACCOUNT",
    schwab_token="YOUR_TOKEN",
    account_size=10000
)

# Analyze a symbol
analysis = bot.analyze_symbol("AAPL", days=60)
print(f"Signal: {analysis['technical']['signal']}")
print(f"Volatility: {analysis['quantitative']['volatility']:.2%}")
print(f"Sharpe Ratio: {analysis['quantitative']['sharpe_ratio']:.2f}")
print(f"Recommendation: {analysis['recommendation']}")

# Execute a signal
result = bot.execute_signal("AAPL", analysis['technical'])

# Monitor positions
updates = bot.monitor_positions()
for pos in updates:
    print(f"{pos['symbol']}: {pos.get('pnl_percent', 0):.2f}%")
```

## 📈 Quantitative Metrics Explained

### Volatility
Measure of price fluctuation. Higher = more risk. Annualized for comparison.

### Sharpe Ratio
Risk-adjusted return. Higher is better. >1.0 is good, >2.0 is excellent.

### Maximum Drawdown
Largest peak-to-trough decline. Shows worst-case scenario.

### Beta
Systematic risk relative to market. >1 = more volatile than market.

### Alpha
Risk-adjusted outperformance vs market.

### Value at Risk (VaR)
Worst expected loss at 95% confidence level.

### Monte Carlo Simulation
Probability distribution of future prices based on historical volatility.

## 🔐 Schwab API Setup

1. **Register Application**
   - Go to https://developer.schwab.com
   - Create an app
   - Get Client ID and Client Secret

2. **Get OAuth Token**
   - Use Schwab OAuth flow to get token
   - Set in `.env` file or pass to API

3. **Test Connection**
   ```bash
   curl -X GET "http://127.0.0.1:8000/health"
   ```

## 🧪 Testing

```bash
# Run all tests
pytest -q

# Run specific test module
pytest tests/test_quant_analysis.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

## ⚠️ Important Notes

1. **Paper Trading First** - Always test on paper trading before real money
2. **API Rate Limits** - Schwab has rate limits, implement backoff if needed
3. **Live Data** - Use end-of-day data for backtesting accuracy
4. **Risk Management** - Never exceed 10% per trade
5. **Authentication** - Secure your Schwab tokens

## 🏗️ Project Structure

```
options-trading-bot/
├── src/
│   ├── api/                 # FastAPI endpoints
│   ├── bot/                 # Enhanced trading bot
│   ├── brokers/            # Schwab integration
│   ├── core/               # Database & logging
│   ├── indicators/         # RSI & Bollinger Bands
│   ├── quant/             # Quantitative analysis
│   ├── risk/              # Risk management
│   └── strategy/          # Trading strategy
├── tests/                 # 18+ passing tests
├── main.py               # Entry point
├── requirements.txt      # Dependencies
├── .env.example         # Environment template
└── README.md            # This file
```

## 📚 Dependencies

- **fastapi** - API framework
- **pandas/numpy** - Data analysis
- **scipy/scikit-learn** - Quantitative analysis
- **sqlalchemy** - Database ORM
- **requests** - HTTP client for Schwab API
- **python-dotenv** - Environment config

## 🚀 Next Steps

1. ✅ Set up Schwab API credentials
2. ✅ Test on paper trading account
3. ✅ Run backtests on historical data
4. ✅ Monitor live signals
5. ✅ Deploy to production

## 📞 Support

Check logs in `logs/` directory for debugging:
```bash
tail -f logs/$(date +%Y%m%d).log
```

## ⚖️ Disclaimer

This bot is for educational and research purposes. Always do your own research before trading. Past performance does not guarantee future results. Use at your own risk.

---

**Version**: 2.0.0  
**Last Updated**: November 26, 2025  
**Status**: Production Ready ✅
