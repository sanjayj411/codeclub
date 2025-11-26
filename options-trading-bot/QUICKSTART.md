# Options Trading Bot - Quick Start Guide

Your new **Options Trading Bot** has been successfully created at:
```
/Users/sanjayj/codeclub/options-trading-bot
```

## ✅ What's Been Built

### Core Features
- **RSI Indicator** - Detect overbought (>70) and oversold (<30) conditions
- **Bollinger Bands** - Identify support/resistance and volatility levels
- **Risk Management** - Max 10% per trade with automatic position sizing
- **Trading Signals** - Buy/Sell signals with signal strength scoring
- **API Server** - RESTful API for all trading functions

### Project Structure
```
options-trading-bot/
├── src/
│   ├── api/              # FastAPI endpoints
│   ├── core/            # Database & logging
│   ├── indicators/      # RSI & Bollinger Bands
│   ├── risk/           # Risk management (10% max)
│   └── strategy/       # Trading strategy logic
├── tests/              # 14 passing tests ✅
├── main.py            # Entry point
├── requirements.txt   # Dependencies
└── README.md          # Full documentation
```

## 🚀 Getting Started

### 1. Install Dependencies
```bash
cd /Users/sanjayj/codeclub/options-trading-bot
python3.9 -m pip install -r requirements.txt
```

### 2. Run Tests
```bash
pytest -q
# Output: 14 passed ✅
```

### 3. Start the API Server
```bash
cd /Users/sanjayj/codeclub/options-trading-bot
python3.9 -m uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
```

Server will run at: **http://127.0.0.1:8000**

### 4. Access API Documentation
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 📊 API Endpoints

### Generate Trading Signal
```bash
curl -X POST http://127.0.0.1:8000/signal \
  -H "Content-Type: application/json" \
  -d '{
    "prices": [100, 101, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85],
    "current_price": 85
  }'
```

Response Example:
```json
{
  "signal": "BUY",
  "entry": 85.0,
  "stop_loss": 82.5,
  "take_profit": 90.0,
  "position": {
    "contracts": 1,
    "risk_amount": 250.0,
    "position_size": 8500.0,
    "risk_percent": 2.5
  },
  "risk_reward_ratio": 2.0,
  "signal_strength": 0.85
}
```

### Validate Trade Setup
```bash
curl -X POST http://127.0.0.1:8000/validate-trade \
  -H "Content-Type: application/json" \
  -d '{
    "entry_price": 100,
    "stop_loss": 95,
    "take_profit": 110
  }'
```

### Update Position
```bash
curl -X POST http://127.0.0.1:8000/position-update \
  -H "Content-Type: application/json" \
  -d '{
    "position_id": "pos_123",
    "current_price": 105
  }'
```

## 🎯 Trading Rules

### Entry Signals
- **BUY**: RSI < 30 AND price < Lower Bollinger Band
- **SELL**: RSI > 70 AND price > Upper Bollinger Band

### Exit Signals
- **Take Profit**: When price reaches 2x the risk distance
- **Stop Loss**: When price hits the stop loss level

### Risk Management
- Maximum risk: **10% of account** per trade
- Default account: $10,000
- Max risk per trade: $1,000
- Position size automatically adjusted based on stop loss distance

## 🧪 Test Coverage

```bash
# All tests passing ✅
pytest -q
# 14 passed in 0.53s

# Test categories:
# - Technical Indicators (RSI, Bollinger Bands)
# - Risk Management (Position sizing, Trade validation)
# - Strategy Logic (Signal generation, Position updates)
```

## 🔧 Configuration

Edit in `src/strategy/__init__.py`:

```python
# Default settings
strategy = OptionsStrategy(
    account_size=10000,        # Your account balance
    max_risk_percent=0.10      # 10% max risk per trade
)
```

## 📈 Technical Indicators

### RSI (14 period)
- **Overbought**: > 70 (Sell signal)
- **Oversold**: < 30 (Buy signal)
- Update frequency: Every new candle

### Bollinger Bands (20 period, 2 std dev)
- **Upper Band**: SMA + 2×StdDev
- **Middle**: 20-period Simple Moving Average
- **Lower Band**: SMA - 2×StdDev

## 💡 Usage Example

```python
from src.strategy import OptionsStrategy

# Initialize bot
bot = OptionsStrategy(account_size=10000, max_risk_percent=0.10)

# Generate signal
prices = [100, 101, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85]
signal = bot.generate_signal(prices, current_price=85)

# Check if valid trade
if signal['signal'] == 'BUY':
    print(f"Entry: {signal['entry']}")
    print(f"Stop Loss: {signal['stop_loss']}")
    print(f"Take Profit: {signal['take_profit']}")
    print(f"Risk: {signal['position']['risk_percent']}% of account")
```

## ⚠️ Important Notes

1. **Paper Trading First**: Always test on paper trading before real money
2. **Backtest**: Validate strategy performance on historical data
3. **Monitor**: Watch your trades and adjust parameters as needed
4. **Risk Management**: Never exceed 10% risk per trade
5. **Education**: This is for educational purposes

## 📝 Next Steps

1. ✅ Run the server
2. ✅ Test API endpoints in Swagger UI
3. ✅ Connect to your broker's API
4. ✅ Set up data feed
5. ✅ Deploy with real data (in paper trading first!)

## 🆘 Troubleshooting

**Module not found error?**
```bash
cd /Users/sanjayj/codeclub/options-trading-bot
export PYTHONPATH=.
pytest -q
```

**Port 8000 already in use?**
```bash
python3.9 -m uvicorn src.api:app --port 8001
# Then access at http://127.0.0.1:8001
```

**Tests failing?**
```bash
pytest -v          # Verbose output
pytest --tb=short  # Show short traceback
```

---

**Your trading bot is ready to go! 🚀**
