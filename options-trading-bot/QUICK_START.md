# Quick Start Guide - Options Trading Bot

## Installation
```bash
cd /Users/sanjayj/codeclub/options-trading-bot
source .venv/bin/activate
```

## Configuration
```bash
# Set up environment variables in .env file
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

## Running Tests

### 1. Test Strategy on FANG Stocks
```bash
python test_fang_stocks.py
```
Shows signal generation across 4 market scenarios for META, AAPL, NFLX, GOOGL.
**Expected**: 16 signals total (7 BUY, 5 SELL, 4 HOLD)

### 2. Paper Trading Simulation
```bash
python test_fang_paper_trading.py
```
Simulates 100 days of trading on FANG stocks with $50K capital.
**Expected**: +6.12% return, 100% win rate

### 3. Validate Drawdown Filter
```bash
python test_drawdown_filter.py
```
Verifies that BUY signals only trigger when price is 2%+ below recent high.

### 4. Paper Trading with Telegram Alerts
```bash
python paper_trading_telegram.py --env
```
Live trading simulation with real-time Telegram notifications.

## Strategy Algorithm

**BUY Signal** (requires ALL conditions):
1. RSI < 30 (oversold), OR
2. MACD bullish crossover, AND
3. Price is 2%+ below 20-candle high ← **NEW FILTER**

**SELL Signal** (requires ANY):
1. RSI > 70 (overbought), OR
2. MACD bearish crossover

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| RSI Period | 14 | Standard RSI calculation period |
| RSI Oversold | 30 | Buy threshold |
| RSI Overbought | 70 | Sell threshold |
| MACD Fast | 12 | Fast EMA period |
| MACD Slow | 26 | Slow EMA period |
| MACD Signal | 9 | Signal line period |
| **Min Drawdown for BUY** | **2.0%** | **NEW: Prevents buying at tops** |

## Customizing Strategy

```python
from src.strategy.trading_strategy import TradingStrategy

# Create strategy with custom drawdown threshold
strategy = TradingStrategy(
    min_drawdown_for_buy=2.0,  # 2% default
    rsi_period=14,
    rsi_oversold=30,
    rsi_overbought=70,
    macd_fast=12,
    macd_slow=26,
    macd_signal=9
)
```

## Performance Metrics

From FANG testing:
- **Win Rate**: 100% (4/4 trades)
- **Return**: +6.12% (100 days, $50K)
- **Best Trade**: +24.02% (AAPL)
- **Drawdown Filter**: 100% effective (blocked 1 false signal)

## File Structure

```
├── src/
│   ├── strategy/trading_strategy.py      # RSI + MACD + 2% filter
│   ├── indicators/
│   │   ├── rsi.py                       # RSI calculation
│   │   └── macd.py                      # MACD calculation
│   ├── paper_trading/trader.py          # Paper trading engine
│   └── notifications/telegram.py        # Telegram alerts
│
├── test_fang_stocks.py                  # FANG signal testing
├── test_fang_paper_trading.py           # FANG trading simulation
├── test_drawdown_filter.py              # Filter validation
├── paper_trading_telegram.py            # Paper trading with alerts
│
└── FANG_TEST_RESULTS.txt               # Detailed results
```

## Troubleshooting

### Telegram not sending messages
1. Check .env file has correct TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
2. Run: `python setup_telegram.py --verify`
3. Run: `python get_telegram_chat_id.py` to get your chat ID

### Python environment issues
```bash
# Configure Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Next Steps

1. **Paper Trading**: Start with `python paper_trading_telegram.py --env`
2. **Monitor Performance**: Check Telegram for daily alerts
3. **Optimization**: Test different drawdown thresholds (1.5%, 3%)
4. **Live Trading**: Add safeguards (daily loss limit) before going live

## Learning Resources

- **Algorithm**: See section "Buy/Sell Signal Algorithm" in README.md
- **Indicators**: Read indicator docstrings (RSI = mean reversion, MACD = trend)
- **Results**: Full analysis in FANG_TEST_RESULTS.txt
- **Filter Details**: See DRAWDOWN_FILTER_SUMMARY.md

## Support

For issues or questions, check:
1. Test results in test files
2. Logs in logs/ directory
3. Documentation files (*.md)
4. Commit history for recent changes
