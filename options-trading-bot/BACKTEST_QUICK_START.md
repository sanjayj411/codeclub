# FANG + NVDA + TSLA Backtest - Quick Reference

## Files Generated

| File | Size | Purpose |
|------|------|---------|
| `fang_nvda_tsla_backtest.xlsx` | 30 KB | **Main Report** - Excel with all data |
| `BACKTEST_REPORT.md` | 9.6 KB | **Analysis** - Detailed findings & recommendations |
| `fang_backtest.py` | 22 KB | **Engine** - Reusable backtest framework |
| `quick_backtest.py` | 1.5 KB | **Utility** - Quick CLI for custom backtests |

## Results Summary

### Overall Performance
- **Total Trades**: 240
- **Win Rate**: 47.5% (114 wins, 97 losses)
- **Total P&L**: -$3,572.48 (-3.57%)
- **Max Drawdown**: $17,458.85 (16.09%)

### Winners
| Stock | Trades | P&L | Return |
|-------|--------|-----|--------|
| TSLA | 44 | +$8,211.20 | +509.81% ✓ |
| NVDA | 36 | +$3,279.30 | +111.72% ✓ |
| META | 18 | +$943.18 | +15.97% ✓ |

### Losers
| Stock | Trades | P&L | Return |
|-------|--------|-----|--------|
| AMZN | 23 | -$2,566.92 | -85.07% ✗ |
| NFLX | 57 | -$7,030.15 | -238.37% ✗ |
| GOOGL | 62 | -$6,409.09 | -434.63% ✗ |

## Opening the Excel Report

### Option 1: Finder
1. Open Finder
2. Navigate to `/Users/sanjayj/codeclub/options-trading-bot/`
3. Double-click `fang_nvda_tsla_backtest.xlsx`
4. Opens in Excel or Numbers

### Option 2: Terminal
```bash
open /Users/sanjayj/codeclub/options-trading-bot/fang_nvda_tsla_backtest.xlsx
```

### Option 3: Direct Excel
```bash
open -a "Microsoft Excel" fang_nvda_tsla_backtest.xlsx
```

## Excel Sheets Explained

### Sheet 1: Summary
- Backtest metadata
- All key statistics
- Quick reference numbers
- Professional format for presentations

### Sheet 2: Symbol Stats
- Performance by stock
- Win rates, P&L, profit factors
- Color-coded results (green=good, red=bad)
- Easy comparison across 6 stocks

### Sheet 3: All Trades
- Complete trade log (240 rows)
- Entry/exit dates and prices
- Individual P&L per trade
- Days held for each trade
- Color-coded by result

### Sheet 4: Analysis
- Performance insights
- Best/worst trades
- Key metrics explained
- Strategic recommendations

## Running Custom Backtests

### Test Different Stocks
```bash
python3 quick_backtest.py --symbols AAPL,SPY,QQQ --days 365
```

### Different Time Period
```bash
python3 quick_backtest.py --days 180  # 6 months instead of 1 year
```

### Different Capital
```bash
python3 quick_backtest.py --capital 50000  # Start with $50k
```

### Custom Output File
```bash
python3 quick_backtest.py --output my_backtest.xlsx
```

### Full Example
```bash
python3 quick_backtest.py \
  --symbols MSFT,AAPL,GOOG \
  --capital 100000 \
  --days 365 \
  --output tech_stocks_backtest.xlsx
```

## Key Insights

### 1. High Volatility = Better Results
- TSLA (+509.81%) - Most volatile
- NVDA (+111.72%) - Highly volatile
- GOOGL (-434.63%) - Stable, underperformed

**Lesson**: RSI/MACD works better with volatile stocks

### 2. More Trades ≠ More Money
- GOOGL: 62 trades → -$6,409 loss
- META: 18 trades → +$943 gain

**Lesson**: Quality over quantity; fewer good trades beat many bad ones

### 3. Win Rate Isn't Everything
- AMZN: 56.5% win rate → -$2,566.92 loss
- Reason: Average loss ($808.74) > Average win ($656.80)

**Lesson**: Need larger wins than losses, not just higher frequency

## Recommendations

### Immediate
1. **Focus on Winners**: Trade TSLA, NVDA, META going forward
2. **Skip Losers**: Remove GOOGL and NFLX from watchlist
3. **Reduce Positions**: Cut capital allocation to underperformers

### Short-term (2-4 weeks)
1. Optimize RSI thresholds (try 25/75 instead of 30/70)
2. Increase drawdown filter (try 3-5% instead of 2%)
3. Add Bollinger Bands support level requirement
4. Test on 6-month period to confirm patterns

### Medium-term (1-2 months)
1. Paper trade optimized settings for 4 weeks
2. Track accuracy and refine further
3. Document any differences from backtest
4. Prepare for live trading if profitable

### Long-term (3+ months)
1. Live trade with smallest position size
2. Scale gradually as confidence increases
3. Monitor monthly performance
4. Adjust parameters seasonally if needed

## Strategy Parameters Used

| Parameter | Value |
|-----------|-------|
| **RSI Period** | 14 days |
| **RSI Oversold** | < 30 (BUY signal) |
| **RSI Overbought** | > 70 (SELL signal) |
| **MACD Fast** | 12 EMA |
| **MACD Slow** | 26 EMA |
| **MACD Signal** | 9 EMA |
| **Drawdown Filter** | 2% minimum |
| **Data Type** | Daily closes |
| **Position Size** | 50% of capital per trade |

## Backtesting Framework

The `fang_backtest.py` framework includes:

- **YahooDataFetcher**: Gets historical price data
- **FANGBacktester**: Main backtesting engine
- **Trade Tracking**: Records every buy/sell with P&L
- **Statistics Calculation**: Win rates, profit factors, Sharpe ratios
- **Excel Export**: Professional multi-sheet reports

Can be easily extended to:
- Add new stocks
- Test different parameters
- Run multiple strategies
- Compare performance

## Troubleshooting

### Excel won't open
```bash
# Check file exists
ls -lh fang_nvda_tsla_backtest.xlsx

# Verify it's valid Excel
file fang_nvda_tsla_backtest.xlsx
# Should say "Microsoft Excel 2007+"
```

### Need to rerun backtest
```bash
cd /Users/sanjayj/codeclub/options-trading-bot
python3 fang_backtest.py --output new_backtest.xlsx
```

### Want to try different stocks
```bash
python3 quick_backtest.py --symbols AAPL,MSFT,GOOG --days 365
```

## Next Actions Checklist

- [ ] Open Excel file and review all 4 sheets
- [ ] Read BACKTEST_REPORT.md for detailed analysis
- [ ] Identify 2-3 stocks to focus on
- [ ] Note RSI/MACD thresholds to optimize
- [ ] Plan 2-week parameter optimization period
- [ ] Set up paper trading environment
- [ ] Run optimized backtest with new parameters
- [ ] Compare results before live trading

---

**Status**: ✓ Backtest Complete  
**Date**: November 27, 2025  
**Duration**: 1 Year (365 days)  
**Stocks**: META, AMZN, NFLX, GOOGL, NVDA, TSLA  
**Trades**: 240  
**Result**: -3.57% (Needs optimization)

📊 **Open Excel file now**: `fang_nvda_tsla_backtest.xlsx`
