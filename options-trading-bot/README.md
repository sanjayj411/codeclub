# Options Trading Bot

An AI-powered options trading bot using RSI and Bollinger Bands indicators with strict 10% maximum risk management.

## Features

- **Technical Indicators**
  - RSI (Relative Strength Index) for overbought/oversold detection
  - Bollinger Bands for volatility and support/resistance
  
- **Risk Management**
  - Maximum 10% risk per trade
  - Dynamic position sizing based on stop loss
  - Risk/reward ratio validation (1:2 minimum)
  
- **Trading Signals**
  - Buy signals: RSI < 30/40 with price near lower Bollinger Band
  - Sell signals: RSI > 60/70 with price near upper Bollinger Band
  - Signal strength scoring (0-1)
  
- **API Endpoints**
  - `/signal` - Generate trading signals
  - `/validate-trade` - Validate trade setup
  - `/position-update` - Check position exit conditions
  - `/indicators-info` - Technical indicator parameters

## Installation

```bash
pip install -r requirements.txt
```

## Running the Bot

### Start the API Server
```bash
python3.9 main.py
```

The server will run on `http://127.0.0.1:8000`

### API Documentation
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Testing

Run all tests:
```bash
pytest -q
```

Run specific test file:
```bash
pytest tests/test_indicators.py -v
```

## Usage Examples

### Generate Trading Signal
```bash
curl -X POST http://127.0.0.1:8000/signal \
  -H "Content-Type: application/json" \
  -d '{
    "prices": [100, 101, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85],
    "current_price": 85,
    "atr": 2.5
  }'
```

### Validate Trade
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

## Risk Management Rules

- **Max Risk Per Trade**: 10% of account
- **Min Risk/Reward**: 1:2 (risk $1 to make $2)
- **Position Sizing**: Automatically calculated based on:
  - Account size
  - Entry price
  - Stop loss distance
  
## Indicator Settings

### RSI (14 period)
- **Overbought**: > 70 (potential sell signal)
- **Oversold**: < 30 (potential buy signal)

### Bollinger Bands (20 period, 2 std dev)
- **Upper Band**: Used for short entry/long exit
- **Middle Band**: 20-period SMA
- **Lower Band**: Used for long entry/short exit

## Project Structure

```
.
├── src/
│   ├── api/              # FastAPI application
│   ├── core/             # Core utilities (db, logger)
│   ├── indicators/       # Technical indicators
│   ├── risk/            # Risk management
│   └── strategy/        # Trading strategy
├── tests/               # Unit tests
├── main.py             # Entry point
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Project configuration
└── README.md          # This file
```

## Configuration

Edit account settings in the API calls:

```python
# Default: 10,000 account, 10% max risk
strategy = OptionsStrategy(account_size=10000, max_risk_percent=0.10)
```

## Disclaimer

This is a trading bot for educational purposes. Always backtest thoroughly and use paper trading before risking real capital. Past performance does not guarantee future results.
