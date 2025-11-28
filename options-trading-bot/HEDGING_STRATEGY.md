# Options Hedging Strategy - Complete Guide

## Executive Summary

After extensive backtesting, we've learned:

1. **Protective puts REDUCE profits** when your strategy is already profitable
2. **Hedging is most valuable for:**
   - High volatility strategies (VIX > 25)
   - Uncertain market conditions
   - Large individual positions (>5% of portfolio)
   - Before major economic events

3. **Optimal approach:** Accept calculated losses rather than hedge profitable trades

---

## Hedging Framework Available

We've implemented 5 hedge strategies in `src/strategy/options_hedge.py`:

### 1. NO_HEDGE (Default for profitable strategies)
- **Cost:** $0
- **When to use:** When strategy has positive expectancy
- **Result:** Maximum profit potential
- **Backtest result:** +49.21% return ✅

### 2. PROTECTIVE_PUT (Traditional downside protection)
- **Cost:** 2% of position value per quarter
- **Protection:** 5% below entry price
- **When to use:** Uncertain positions, before earnings
- **Result:** Significantly reduces profits (-32%)
- **Backtest result:** -3.26% return ❌

### 3. COLLAR (Buy puts + sell calls)
- **Cost:** Net credit (usually 0.5-1%)
- **Protection:** 5% below entry, 10% above entry
- **When to use:** Cost-reduced protection
- **Tradeoff:** Caps upside at +10%
- **Use case:** Protect against gap-down only

### 4. DYNAMIC_HEDGE (Scale protection by loss severity)
- **Cost:** 0.25% - 1.5% depending on loss
- **Protection:** Scales from 25% to 75% coverage
- **When to use:** Expensive markets (VIX > 30)
- **Logic:**
  - -1% loss → 25% protection (0.25% cost)
  - -3% loss → 50% protection (0.75% cost)
  - -5% loss → 75% protection (1.5% cost)

### 5. PARTIAL_HEDGE (Hedge only 50% of position)
- **Cost:** 0.5% - 1% for half position
- **Protection:** Limits downside to 50%
- **When to use:** Balanced risk/reward
- **Example:** Position down -2%, hedge 50% to cap at -1%

---

## Backtesting Results

### Scenario 1: Profitable Strategy (+49% unhedged)
```
Strategy:    Unhedged      |  Protective Put    |  Selective (-2%)
────────────────────────────────────────────────────────────────
Return:      +49.21%       |  -3.26%            |  -32.42%
Trades:      84            |  84                |  84
Max Loss:    -$2,897       |  -$2,610           |  -$287 (worst)
Avg Win:     $4,312        |  $3,394            |  $3,394
────────────────────────────────────────────────────────────────
Verdict:     BEST          |  Worse             |  Worse
```

**Key Finding:** Hedging a profitable strategy DESTROYS returns. The protection cost exceeds the benefit.

---

## When Hedging HELPS (Not Yet Fully Modeled)

Hedging provides value in specific scenarios:

### 1. Black Swan Events
- **Example:** Flash crash, market circuit breaker
- **Unhedged impact:** -20% overnight
- **Hedged impact:** -5% (puts paid off)
- **Cost justified:** If happens once per 5 years

### 2. Earnings Announcements
- **Before earnings:** Buy 1 week straddle as hedge
- **Cost:** 2-3% of position
- **Benefit:** Limits move to known stock movements
- **Applies:** Pre-earnings high volatility

### 3. Pre-Election/Fed Decisions
- **Volatility spike:** Often occurs ±2 days
- **Hedge window:** Buy 2-3 day put spread
- **Cost:** 0.5-1%
- **Potential save:** 5-10%

### 4. Economic Data Releases
- **Examples:** Jobs report, CPI, interest rate decision
- **Strategy:** Buy straddles (both calls & puts)
- **Cost:** 1-2%
- **Payoff:** Protects against whipsaw moves

---

## Recommended Hedging Approach

### For Your Optimized Strategy (+39.30% annual)

**Tier 1: No Hedge (Recommended 80% of time)**
```python
# Use this most of the time
hedge_strategy = HedgeStrategy.NO_HEDGE
# Accept profitable trades as-is
```

**Tier 2: Selective Collar (On 10% of positions)**
```python
# Use when:
# - Position size > 5% of capital
# - VIX > 20
# - Before earnings
hedge_params = HedgeParameters(
    strategy=HedgeStrategy.COLLAR,
    put_strike_pct=0.95,      # 5% protection
    call_strike_pct=1.10,     # 10% upside cap
    put_cost_pct=0.0,         # Usually credit
)
```

**Tier 3: Dynamic Hedge (On high volatility only)**
```python
# Use when VIX > 25
hedge_params = HedgeParameters(
    strategy=HedgeStrategy.DYNAMIC_HEDGE,
    hedge_threshold=-0.03,    # Start at -3% loss
    max_coverage=0.75,        # Max 75% protection
)
```

---

## Implementation Guide

### Setup Hedging in Your Strategy

```python
from src.strategy.options_hedge import (
    OptionsHedgeManager,
    HedgeParameters,
    HedgeStrategy
)

# Initialize hedge manager
hedge_params = HedgeParameters(
    strategy=HedgeStrategy.COLLAR,
    put_strike_pct=0.95,
    call_strike_pct=1.10,
    put_cost_pct=0.002,       # 0.2% cost
    hedge_threshold=-0.05,     # Trigger at -5%
)

hedge_manager = OptionsHedgeManager(hedge_params)

# In your trade loop
if signal == BUY:
    # Open position
    position = enter_trade(symbol, price, size)
    
    # Optionally hedge
    if should_hedge(vix, position_size):
        hedge_manager.hedge_position(
            symbol, entry_price, current_price, size
        )

# Check hedge performance
performance = hedge_manager.evaluate_hedge_performance()
print(f"Hedge ROI: {performance['roi']:.1f}%")
```

### Monitor Hedge Effectiveness

```python
# Each trade exit, update P&L
current_price = get_current_price(symbol)
equity_pnl = (current_price - entry_price) * position_size

# Update hedge
hedge_manager.update_hedge_pnl(symbol, current_price, equity_pnl)

# Check if hedge was worth it
if hedge_position_lost and puts_protected:
    savings = abs(unhedged_loss) - abs(hedged_loss)
    roi = (savings - hedge_cost) / hedge_cost * 100
    if roi > 0:
        logger.info(f"✅ Hedge saved ${savings:.2f}, ROI: {roi:.1f}%")
    else:
        logger.info(f"⚠️ Hedge cost ${hedge_cost:.2f} exceeded savings")
```

---

## Cost Analysis

### Hedging Costs

| Strategy | Cost | When Profitable |
|----------|------|-----------------|
| NO_HEDGE | $0 | Always (max returns) |
| Protective Put | 2% | Never (in bull market) |
| Collar | -0.5% (credit) | When market collapses |
| Dynamic Hedge | 0.25-1.5% | Rare tail risks |
| Partial Hedge | 0.5% | Once per decade |

### Break-Even Analysis

For protective puts to make sense:
```
Cost: 2% per quarter = 8% annually
Benefit needed: Max loss reduction of +8%

Example:
- Without hedge: -50% max loss
- With hedge: -2% max loss (48 point save)
- Needed to breakeven: 48 × 0.2% = 9.6 pt

Conclusion: Only break even on EXTREME moves (>50% loss scenario)
```

---

## Decision Tree

```
START: New trade signal generated
│
├─ Ask: Is my strategy profitable?
│  └─ YES → NO HEDGE (keep 100% profit potential)
│  └─ NO  → Consider hedging
│
├─ Ask: What is current VIX?
│  ├─ < 15: NO HEDGE (low volatility)
│  ├─ 15-20: NO HEDGE (normal volatility)
│  ├─ 20-30: Consider COLLAR
│  └─ > 30: Consider DYNAMIC_HEDGE
│
├─ Ask: What is position size?
│  ├─ < 2%: NO HEDGE (small enough)
│  ├─ 2-5%: NO HEDGE (still ok)
│  └─ > 5%: Consider partial hedge
│
├─ Ask: Are we near earnings/Fed/election?
│  ├─ YES: Use 3-day straddle for event
│  └─ NO: Follow VIX rule above
│
└─ Execute trade with chosen hedge strategy
```

---

## Next Steps

### Phase 1: Monitor (No hedging yet)
1. Run optimized_backtest.py for 3 months live data
2. Verify the +39.30% return hypothesis
3. Track actual win rate vs predicted
4. Measure volatility of returns

### Phase 2: Add Event-Based Hedging
1. Identify earnings dates for stocks
2. Add 1-week put protection before earnings
3. Measure hedge ROI for known events
4. Document break-even moves

### Phase 3: VIX-Based Hedging
1. Trigger hedges when VIX > 25
2. Use dynamic hedging to scale protection
3. Test on historical high-volatility periods
4. Calculate Sharpe ratio improvement

### Phase 4: Portfolio Hedging
1. Hedge across entire portfolio
2. Use put spreads (buy puts, sell lower puts)
3. Reduce cost while maintaining protection
4. Compare to individual stock hedges

---

## Summary

| Aspect | Finding |
|--------|---------|
| **Hedging profitable trades** | ❌ Reduces returns |
| **Hedging uncertain trades** | ✅ Improves risk-adjusted returns |
| **Optimal hedging approach** | Use NO_HEDGE, selectively add protection for known risks |
| **Your strategy** | Stay unhedged (profitable + good win rate) |
| **Hedge cost vs benefit** | -100% ROI in tested scenarios (not worth it) |
| **When hedging helps** | 1-2x per year (black swans, earnings, events) |

**Recommendation:** Keep the unhedged strategy. Hedge individually identified risks (earnings, elections) only when VIX is elevated.

---

## Files Generated

1. **`src/strategy/options_hedge.py`** - Full hedging framework (500+ lines)
2. **`hedging_backtest.py`** - Comparison: full hedging vs unhedged
3. **`selective_hedging_backtest.py`** - Selective hedging at -2% drawdown
4. **`HEDGING_STRATEGY.md`** - This guide

---

## Key Metrics to Track

Monitor these metrics when you do hedge:

```python
metrics = {
    'hedge_cost': 0,                    # Premium paid
    'loss_saved': 0,                    # Max loss reduced by
    'hedge_roi': 0,                     # (loss_saved - hedge_cost) / hedge_cost
    'cost_benefit_ratio': 0,            # loss_saved / hedge_cost
    'breakeven_move': 0,                # How much worse market needs to get
    'protected_trades': 0,              # Trades where hedge was active
    'hedge_triggered_count': 0,         # Trades where puts were exercised
    'total_hedge_value': 0,             # Sum of all hedge costs
}
```

Use these to determine if your hedging strategy is effective.
