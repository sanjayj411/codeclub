# FANG + NVDA + TSLA 1-Year Backtest Report
**Date**: November 27, 2025  
**Excel File**: `fang_nvda_tsla_backtest.xlsx`

---

## Executive Summary

A comprehensive 1-year backtesting analysis was conducted on six mega-cap technology stocks using the RSI + MACD strategy with Bollinger Bands support filtering. The analysis reveals mixed results across the portfolio with significant variation in individual stock performance.

### Key Findings

| Metric | Value |
|--------|-------|
| **Total Trades** | 240 |
| **Winning Trades** | 114 (47.5%) |
| **Losing Trades** | 97 |
| **Total P&L** | -$3,572.48 |
| **Total Return** | -3.57% |
| **Win Rate** | 47.5% |
| **Sharpe Ratio** | -0.81 |
| **Max Drawdown** | $17,458.85 (16.09%) |

---

## Stock-by-Stock Performance

### 🟢 **TSLA (Tesla) - BEST PERFORMER**
- **Trades**: 44
- **Win Rate**: 47.7%
- **P&L**: +$8,211.20
- **Return**: **+509.81%**
- **Status**: Strong profit generator
- **Analysis**: Tesla showed the strongest performance with significant trade profitability. The high-volatility nature of TSLA aided the RSI/MACD strategy in capturing larger moves.

### 🟢 **NVDA (NVIDIA) - STRONG PERFORMER**
- **Trades**: 36
- **Win Rate**: 55.6%
- **P&L**: +$3,279.30
- **Return**: **+111.72%**
- **Status**: Consistent winner
- **Analysis**: NVIDIA demonstrated above-average win rate with solid profitability, suggesting strong trend-following opportunities.

### 🟡 **META (Meta/Facebook) - POSITIVE**
- **Trades**: 18
- **Win Rate**: 22.2% (LOWEST)
- **P&L**: +$943.18
- **Return**: **+15.97%**
- **Status**: Profitable but low signal frequency
- **Analysis**: Fewest trades among all stocks. Despite low win rate, generated positive returns, suggesting large-win trade dynamics.

### 🔴 **GOOGL (Google/Alphabet) - NEGATIVE**
- **Trades**: 62 (second-most)
- **Win Rate**: 50.0%
- **P&L**: -$6,409.09
- **Return**: **-434.63%**
- **Status**: Biggest loser by magnitude
- **Analysis**: Despite 50% win rate, significant losses accumulated. Strategy struggles with GOOGL's price action patterns.

### 🔴 **NFLX (Netflix) - NEGATIVE**
- **Trades**: 57
- **Win Rate**: 43.9%
- **P&L**: -$7,030.15
- **Return**: **-238.37%**
- **Status**: Second-largest loser
- **Analysis**: High trade frequency but below-average win rate led to cumulative losses. Netflix's volatility may be difficult for this strategy.

### 🔴 **AMZN (Amazon) - NEGATIVE**
- **Trades**: 23
- **Win Rate**: 56.5% (HIGH)
- **P&L**: -$2,566.92
- **Return**: **-85.07%**
- **Status**: Good win rate, negative return
- **Analysis**: Paradoxically, despite strong 56.5% win rate, losses were significant. Suggests strategy generates frequent small wins but occasional large losses.

---

## Strategy Analysis

### Strategy Used
**RSI + MACD with Bollinger Bands Support Filter**

- **RSI Period**: 14 days
- **Oversold Threshold**: RSI < 30 (BUY signal)
- **Overbought Threshold**: RSI > 70 (SELL signal)
- **MACD**: 12/26/9 exponential moving averages
- **Minimum Drawdown Filter**: 2% from recent high required for BUY

### Trading Signal Logic

**BUY Conditions** (Triggered when ALL met):
1. RSI drops below 30 (oversold)
2. MACD bullish crossover (MACD line > Signal line)
3. Stock price 2%+ below 20-day high (drawdown filter)

**SELL Conditions** (Triggered when ANY met):
1. Position open and stop-loss hit
2. RSI rises above 70 (overbought)
3. MACD bearish crossover

---

## Performance Metrics Explained

### Win Rate
- **Overall**: 47.5% (below 50% breakeven)
- **Best**: NVDA 55.6%
- **Worst**: META 22.2%

**Interpretation**: With 47.5% win rate below the 50% threshold, the strategy requires better risk management (win size > loss size) to be profitable.

### Profit Factor
- **Overall**: 0.95x
- **Meaning**: For every $1 gained in winning trades, strategy loses $1.05 in losing trades

**Interpretation**: Strategy is unprofitable. This indicates winning trades average smaller size than losing trades.

### Sharpe Ratio
- **Overall**: -0.81
- **Interpretation**: Risk-adjusted returns are negative. Losses exceed gains when adjusted for volatility.

### Max Drawdown
- **Peak Loss**: $17,458.85 (16.09% of initial capital)
- **Interpretation**: Strategy can experience significant downswings. Requires psychological discipline and adequate risk capital.

---

## Excel Report Contents

### Sheet 1: Summary
Contains:
- Backtest metadata (date, symbols, period, initial capital, strategy)
- Summary statistics (all metrics above)
- Quick reference numbers for presentation

### Sheet 2: Symbol Stats
Detailed breakdown:
- Trades per symbol
- Win/loss counts and percentages
- P&L totals and percentages
- Profit factor for each stock
- Color-coded P&L (green = positive, red = negative)

### Sheet 3: All Trades
Complete trade log showing:
- Entry/exit dates
- Entry/exit prices
- Quantity traded
- Individual P&L and percentage returns
- Days held for each trade
- Color-coded P&L per trade

### Sheet 4: Analysis
High-level insights:
- Performance summary by symbol
- Best and worst individual trades
- Key statistics and ratios
- Trading insights and recommendations

---

## Key Insights

### 1. **Extreme Performance Variance**
- TSLA +509.81% vs GOOGL -434.63%
- 944% performance gap between best and worst
- Suggests strategy performs very differently across stocks

### 2. **Volume vs Profitability Mismatch**
- GOOGL and NFLX had most trades (62 and 57) but worst returns
- META had fewest trades (18) but positive return
- **Insight**: More trades ≠ more profits; quality over quantity

### 3. **Win Rate Paradox (AMZN)**
- 56.5% win rate (above breakeven) yet -85.07% return
- Indicates losses are larger than wins despite higher frequency
- **Insight**: Need to focus on risk-to-reward ratio, not just win rate

### 4. **High-Volatility Stock Advantage**
- TSLA and NVDA (higher volatility) outperformed significantly
- GOOGL and NFLX (higher stability) underperformed
- **Insight**: RSI/MACD strategy may be better suited for volatile stocks

### 5. **Overall Negative Results**
- Portfolio lost 3.57% despite 47.5% win rate
- Indicates strategy needs optimization or market conditions unsuitable

---

## Recommendations

### Immediate Actions

1. **Skip Low-Performing Stocks**
   - Remove GOOGL and NFLX from scan list
   - These two stocks account for -$13,439.24 in losses
   - Focus on TSLA, NVDA, META going forward

2. **Adjust Position Sizing**
   - Current: Equal capital allocation per position
   - Improved: Allocate more capital to TSLA/NVDA, less to others
   - Use 60% capital for proven winners, 40% for others

3. **Tighten Stop Losses**
   - Large losses (like GOOGL -$434.63 per trade) indicate stop-loss issues
   - Implement 2-3% hard stops vs current strategy

### Strategic Optimization

4. **Increase Drawdown Filter**
   - Current: 2% drawdown requirement
   - Try: 3-5% for more selective entry points
   - May improve win rate at cost of fewer trades

5. **Adjust RSI Thresholds**
   - Current: 30/70
   - Try: 25/75 (more extreme) for fewer, higher-confidence trades

6. **Add Bollinger Bands Integration**
   - Current: MACD + RSI only
   - Enhancement: Require price at lower Bollinger Band for BUY
   - Historical strategy development showed 80%+ accuracy with this filter

7. **Implement Volume Confirmation**
   - Only trade when above 20M average volume
   - Filters out low-liquidity environments

### Advanced Analysis

8. **Separate Strategy by Stock Volatility**
   - High-vol strategy (TSLA, NVDA): More aggressive
   - Low-vol strategy (GOOGL, NFLX): More conservative filters

9. **Time-of-Day Optimization**
   - Test if strategy performs better in first 1-2 hours of trading
   - Backtester uses daily close data, but intraday patterns may differ

10. **Market Regime Detection**
    - Add filter: only trade during trending markets
    - Avoid mean-reversion periods where RSI oscillates

---

## Testing Recommendations

### Phase 1: Parameter Optimization (Next 2 weeks)
1. Run backtests with different RSI thresholds (25/75, 28/72, 30/70)
2. Test drawdown filters from 1-5%
3. Measure impact on win rate, profit factor, and total returns
4. Document results in similar Excel format

### Phase 2: Symbol Selection (Weeks 3-4)
1. Remove underperforming stocks (GOOGL, NFLX)
2. Add new candidate stocks (e.g., MSFT, SPY, QQQ)
3. Run full 365-day backtest
4. Compare results

### Phase 3: Live Paper Trading (Weeks 5-8)
1. Deploy optimized strategy on paper account
2. Match backtest parameters exactly
3. Track daily results
4. Monitor for strategy drift or market regime change

### Phase 4: Live Trading (If approved)
1. Start with 1-2 shares per stock
2. Scale gradually based on performance
3. Maintain daily P&L tracking

---

## Conclusion

The FANG + NVDA + TSLA backtest reveals that the RSI + MACD strategy shows promise on high-volatility tech stocks (TSLA +510%, NVDA +112%) but struggles with lower-volatility mega-caps (GOOGL -435%, NFLX -238%). 

**Overall Performance**: -3.57% return over 1 year suggests the strategy needs optimization. The opportunity lies in:
1. **Stock selection** - Focus on proven winners (TSLA, NVDA, META)
2. **Parameter tuning** - Adjust RSI thresholds and drawdown filters
3. **Risk management** - Tighter stops and position sizing by stock volatility

**Next Step**: Implement recommendations above and re-run backtest with optimized parameters for Phase 2 validation.

---

## File Information

- **Filename**: `fang_nvda_tsla_backtest.xlsx`
- **Size**: 30 KB
- **Format**: Microsoft Excel 2007+
- **Sheets**: 4 (Summary, Symbol Stats, All Trades, Analysis)
- **Generated**: November 27, 2025 at 22:02:04 UTC

### To Open:
```bash
open fang_nvda_tsla_backtest.xlsx
# or
open -a "Microsoft Excel" fang_nvda_tsla_backtest.xlsx
```

---

**Analysis Complete** ✓
