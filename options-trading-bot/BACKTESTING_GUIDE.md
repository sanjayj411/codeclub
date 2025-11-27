# Backtesting Guide

## Quick Start

### Run Backtest with Sample Data
```bash
python backtest_example.py --sample
```

### Run Backtest with Live Schwab Data
```bash
python backtest_example.py --live
```

## Backtester Components

### 1. Backtester Class
Main backtesting engine that simulates trading strategy on historical data.

**Usage:**
```python
from src.backtesting import Backtester
from src.strategy import TradingStrategy

# Create strategy and backtester
strategy = TradingStrategy()
backtester = Backtester(strategy, initial_capital=10000.0)

# Run backtest
stats = backtester.run(price_data)
print(backtester.get_summary())
```

**Methods:**
- `run(price_data)` - Execute backtest on historical OHLCV data
- `get_summary()` - Get formatted statistics report
- `_calculate_stats()` - Calculate performance metrics

**Price Data Format:**
```python
price_data = {
    'AAPL': [
        {
            'timestamp': datetime(...),
            'open': 150.0,
            'high': 152.0,
            'low': 149.5,
            'close': 151.5,
            'volume': 1000000
        },
        ...
    ],
    'SPY': [...],
}
```

### 2. BacktestStats
Performance metrics from backtest run.

**Metrics:**
- `total_trades` - Number of completed trades
- `winning_trades` - Count of profitable trades
- `losing_trades` - Count of losing trades
- `win_rate` - Percentage of winning trades
- `total_pnl` - Total profit/loss in dollars
- `total_pnl_pct` - Total return percentage
- `avg_win` - Average winning trade size
- `avg_loss` - Average losing trade size
- `profit_factor` - Ratio of gross wins to gross losses
- `max_drawdown` - Peak-to-trough decline
- `max_drawdown_pct` - Drawdown as percentage
- `sharpe_ratio` - Risk-adjusted returns

### 3. Trade Class
Represents a completed trade.

```python
trade.symbol        # e.g., 'AAPL'
trade.entry_price   # Entry price
trade.exit_price    # Exit price
trade.quantity      # Shares traded
trade.entry_time    # Entry timestamp
trade.exit_time     # Exit timestamp
trade.pnl           # Profit/loss in dollars
trade.pnl_pct       # Profit/loss percentage
```

### 4. Position Class
Represents an open position.

```python
position.symbol         # e.g., 'AAPL'
position.quantity       # Shares held
position.entry_price    # Entry price
position.current_price  # Current market price
position.value          # Current position value
position.pnl            # Unrealized P&L
position.pnl_pct        # Unrealized P&L %
```

## Strategy Integration

The backtester works with `TradingStrategy` which combines RSI and MACD indicators:

```python
from src.indicators import RSIIndicator, MACDIndicator
from src.strategy import TradingStrategy

# Strategy analyzes:
# - RSI < 30 (oversold) + MACD bullish crossover = BUY signal
# - RSI > 70 (overbought) + MACD bearish crossover = SELL signal
# - Confidence score based on signal agreement (0-100%)
```

## Performance Metrics Explanation

### Win Rate
Percentage of trades that resulted in profit.
- 50%+ = Profitable strategy (roughly break-even)
- 60%+ = Good strategy
- 40%- = Needs improvement

### Profit Factor
Ratio of total gains to total losses.
- > 1.5 = Excellent
- 1.0-1.5 = Good
- < 1.0 = Losing strategy

### Sharpe Ratio
Risk-adjusted returns. Annualized based on trade frequency.
- > 1.0 = Good risk-adjusted returns
- > 2.0 = Excellent
- < 0 = Returns worse than risk-free rate

### Max Drawdown
Largest peak-to-trough decline during backtest.
- < 10% = Conservative
- 10-20% = Moderate
- > 30% = Aggressive/Risky

## Example Output

```
====== BACKTEST SUMMARY ======
Initial Capital: $10,000.00
Final Equity: $9,767.68

Total Return: $-232.32 (-2.32%)

Total Trades: 11
Winning Trades: 4
Losing Trades: 7
Win Rate: 36.4%

Avg Win: $128.08
Avg Loss: $106.37
Profit Factor: 0.69

Max Drawdown: $624.87 (6.02%)
Sharpe Ratio: -4.16
==============================
```

## Optimization Tips

### 1. Adjust Position Size
```python
backtester = Backtester(strategy, initial_capital=50000.0)  # More capital
```

### 2. Test Different Timeframes
Use daily, 4-hour, or 1-hour candles by filtering price_data

### 3. Test Different Symbols
Run backtest on multiple sectors to validate strategy robustness

### 4. Parameter Tuning
Modify RSI thresholds and MACD periods in trading_strategy.py:
```python
rsi_oversold = 30   # Lower = more sensitive
rsi_overbought = 70 # Higher = less sensitive
```

### 5. Compare Against Benchmark
Compare strategy performance (Sharpe ratio, drawdown) vs buy-and-hold SPY

## Known Limitations

1. **Slippage**: Assumed perfect execution at market price
2. **Commissions**: Not included in calculations
3. **Gap Risk**: Gaps between days not modeled
4. **Liquidity**: Assumes all positions can be filled
5. **Historical Bias**: Past performance ≠ future results

## Next Steps

1. ✅ Backtest RSI/MACD strategy
2. ⏳ Add paper trading (simulated live trading)
3. ⏳ Add position tracking and P&L
4. ⏳ Add parameter optimization
5. ⏳ Deploy to live trading with safeguards
