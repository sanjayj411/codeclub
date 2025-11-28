# Enhanced Stock Scanner with Bollinger Bands & Options Integration

## Overview

Advanced stock scanner that:
1. **Technical Analysis**: RSI + MACD + Bollinger Bands convergence
2. **Stock Signals**: Identifies BUY/SELL opportunities
3. **Options Trigger**: When stock BUY triggered, analyzes call options (30 DTE)
4. **Configurable**: Scan any list of stocks you provide
5. **Professional**: Black-Scholes pricing, Monte Carlo risk analysis

---

## Quick Start

### 1. Basic Scan (5 stocks)

```bash
python stock_scanner.py --stocks AAPL,SPY,QQQ,META,GOOGL
```

Output:
```
======================================================================
  STOCK SCANNER - 5 symbols
  Time: 2025-11-27 14:30:00
  Data Type: Sample
======================================================================

📈 BUY SIGNALS
----------------------------------------------------------------------
  AAPL     | bb_rsi               | Conf: 85% | Price: $149.50
  └─ RSI oversold + BB lower bounce + 2.5% drawdown
  
  SPY      | macd_bullish         | Conf: 72% | Price: $614.25
  └─ MACD bullish crossover at lower Bollinger Band

📞 OPTIONS OPPORTUNITIES (Call Options)
----------------------------------------------------------------------
  AAPL     | $ 150.00 Call | Delta: 0.413 | Prob ITM: 48.3%
  └─ Entry: $2.75 | Contracts: 5 | Conf: 78%
  
  SPY      | $ 615.00 Call | Delta: 0.389 | Prob ITM: 45.2%
  └─ Entry: $3.25 | Contracts: 3 | Conf: 71%
```

### 2. Scan from Configuration File

```bash
python stock_scanner.py --config stocks_config.txt
```

File format (`stocks_config.txt`):
```
# Tech stocks
AAPL
MSFT
NVDA

# ETFs
SPY
QQQ

# Pharma
JNJ
UNH
```

### 3. Use Live Schwab Data

```bash
python stock_scanner.py --stocks AAPL,SPY --live
```

Requires Schwab OAuth credentials in `.env`

### 4. Export Results to JSON

```bash
python stock_scanner.py --stocks AAPL,SPY --output scan_results.json
```

### 5. Custom Thresholds

```bash
python stock_scanner.py \
  --stocks AAPL,SPY,QQQ \
  --rsi-oversold 28 \
  --rsi-overbought 72 \
  --bb-period 20 \
  --min-drawdown 2.5 \
  --days 90
```

---

## Technical Indicators

### Bollinger Bands (BB)

**Formula:**
```
Middle Band = 20-day SMA
Upper Band = Middle + (2 × std dev)
Lower Band = Middle - (2 × std dev)
%B = (Price - Lower) / (Upper - Lower)
```

**Signals:**
- Price at lower BB + RSI oversold = **Strong BUY**
- Price at upper BB + RSI overbought = **Strong SELL**
- Low band width = Squeeze (breakout coming)

**Position Indicators:**
- %B < 0.25: Price at lower band (potential reversal)
- 0.25 ≤ %B ≤ 0.75: Price in middle (neutral)
- %B > 0.75: Price at upper band (potential reversal)

### RSI (Relative Strength Index)

**Thresholds:**
- RSI < 30: Oversold (BUY signal)
- 30 ≤ RSI ≤ 70: Neutral
- RSI > 70: Overbought (SELL signal)

### MACD (Moving Average Convergence Divergence)

**Signals:**
- MACD crosses above signal line: Bullish (BUY)
- MACD crosses below signal line: Bearish (SELL)
- Histogram > 0: Bullish momentum
- Histogram < 0: Bearish momentum

### Drawdown Filter

**Purpose:** Prevent buying at market tops

**Requirement:** Stock must be 2%+ below 20-candle high

**Example:**
```
High (past 20 days): $150.00
Current: $146.50
Drawdown: 2.33% ✓ (meets 2% threshold)
```

---

## Signal Scoring

### Confidence Calculation

**Components:**
1. **Technical Signal Strength** (30%)
   - RSI + MACD + BB convergence
   - Single signal = 50% strength
   - Two signals = 70% strength
   - All three + drawdown = 95% strength

2. **Indicator Convergence** (40%)
   - RSI oversold + BB lower = +20%
   - MACD bullish + histogram positive = +15%
   - All converging = +25%

3. **Drawdown Confirmation** (30%)
   - Meeting 2% threshold = +30%
   - Below 1% = +20%
   - No drawdown = +0%

**Example Scoring:**
```
Signal: BUY
- RSI oversold (< 30): +30%
- MACD bullish crossover: +25%
- Price at lower BB: +20%
- Drawdown 2.5%: +30%
- Total Confidence: 85%
```

---

## Options Analysis

When stock generates **BUY signal**, scanner analyzes calls:

### Strike Selection

**Target Delta:** 0.40 (40% ITM probability)

**Candidates:**
- ATM: Current price
- 1% OTM: Current × 1.01
- 2% OTM: Current × 1.02
- 2.5% OTM: Current × 1.025

**Algorithm:**
```
For each candidate strike:
  delta = BS_delta(stock, strike, 30_days)
  score = distance to target delta (0.40)
  select strike with best score
```

### Options Confidence

**Factors:**
1. Stock signal confidence (40%)
2. Delta appropriateness (30%)
3. Probability ITM (20%)
4. Risk/Reward ratio (10%)

**Example:**
```
AAPL $150 Call, 30 DTE
- Stock signal: 85% confidence → +34%
- Delta 0.413 (close to 0.40 target) → +28%
- Prob ITM: 48.3% (ideal range 40-60%) → +18%
- Risk/Reward: $450 loss / $1200 gain → +10%
- Total: 90% confidence → STRONG BUY
```

### Greeks Interpretation

| Greek | Value | Meaning |
|-------|-------|---------|
| Delta | 0.40 | 40% probability ITM, $0.40 profit per $1 stock move |
| Gamma | 0.035 | Delta increases 0.035 per $1 move |
| Vega | 0.15 | +$0.15 profit per 1% IV increase |
| Theta | -0.08 | -$0.08 daily time decay |
| Prob ITM | 48% | Fair probability of finishing ITM |

---

## Risk Management

### Position Sizing

**Default:** 2% max risk per trade

```
Max Risk = Account Size × 2%
Contracts = Max Risk / (Option Price × 100)

Example:
- Account: $50,000
- Max Risk: $1,000
- Option Price: $2.75
- Contracts = 1,000 / 275 = 3.6 → 3 contracts
```

### VaR/CVaR

**Value at Risk (VaR):** 95% confidence level
```
VaR(95%) = maximum expected loss in 95% of scenarios
```

**Example:**
```
Position: 5 AAPL $150 Calls
VaR(95%): $450
CVaR(95%): $650
Worst case: -$1,200

Meaning: 95% chance loss ≤ $450, worst 5% average loss is $650
```

### Stop Loss

**Recommended:** Exit when:
- VaR(95%) exceeded
- Theta decay > 25% of entry premium
- IV volatility spike (short vega risk)
- Stock closes below drawdown high

---

## File Locations

```
stock_scanner.py                    # Main scanner entry point
stocks_config.txt                   # Example stock list config

src/indicators/
├── bollinger_bands.py             # Bollinger Bands indicator
├── rsi.py                         # RSI indicator
├── macd.py                        # MACD indicator

src/strategy/
├── enhanced_strategy.py           # Stock + options strategy
├── options_strategy.py            # Options-specific analysis
├── trading_strategy.py            # Basic stock strategy

src/quant/
├── black_scholes.py              # Option pricing & Greeks
├── monte_carlo.py                # Simulation & risk analysis

tests/
├── test_enhanced_strategy.py     # Strategy tests
├── test_options_pricing.py       # Options tests
```

---

## Usage Examples

### Example 1: Daily Scan Routine

```bash
# Morning scan of watchlist
python stock_scanner.py \
  --config my_watchlist.txt \
  --live \
  --output morning_scan_$(date +%Y%m%d).json

# Review results for trading opportunities
```

### Example 2: Sector Scan

```bash
# Scan tech sector
python stock_scanner.py \
  --stocks AAPL,MSFT,GOOGL,META,NVDA,AMD,TSLA \
  --rsi-oversold 28 \
  --output tech_sector_scan.json
```

### Example 3: Earnings Watch

```bash
# Scan stocks with upcoming earnings (higher volatility expected)
python stock_scanner.py \
  --stocks AAPL,MSFT,AMZN \
  --days 90 \
  --bb-period 20 \
  --min-drawdown 1.5
```

### Example 4: Create Custom Scanner

```python
from stock_scanner import StockScanner
from src.strategy.enhanced_strategy import EnhancedStockStrategy

# Custom parameters
strategy = EnhancedStockStrategy(
    rsi_oversold=25,
    rsi_overbought=75,
    bb_period=20,
    min_drawdown_for_buy=1.0
)

scanner = StockScanner(strategy, use_live_data=False)

# Scan specific stocks
results = scanner.scan_multiple_stocks(['AAPL', 'SPY', 'QQQ'])

# Process results
for result in results:
    if result['stock_signal'] and result['stock_signal']['action'] == 'BUY':
        print(f"BUY signal: {result['symbol']}")
        if result['options_opportunity']:
            opp = result['options_opportunity']
            print(f"  → Call: ${opp['strike']:.2f}, Entry: ${opp['entry_price']:.2f}")
```

---

## Configuration Examples

### Aggressive Settings

```bash
python stock_scanner.py \
  --stocks AAPL,SPY \
  --rsi-oversold 35 \
  --rsi-overbought 65 \
  --min-drawdown 1.0
```

More signals, more false positives

### Conservative Settings

```bash
python stock_scanner.py \
  --stocks AAPL,SPY \
  --rsi-oversold 25 \
  --rsi-overbought 75 \
  --min-drawdown 3.0
```

Fewer signals, more reliable

### Extended History

```bash
python stock_scanner.py \
  --stocks AAPL,SPY \
  --days 180
```

Uses 6 months of history instead of 2 months

---

## Troubleshooting

### Q: No signals detected
**A:** Check threshold settings:
```bash
# Lower thresholds for more signals
python stock_scanner.py --stocks AAPL --rsi-oversold 35 --min-drawdown 1.0
```

### Q: API connection error
**A:** Verify Schwab credentials:
```bash
# Check .env file
cat .env | grep SCHWAB

# Fall back to sample data
python stock_scanner.py --stocks AAPL
```

### Q: Want to modify signal logic
**A:** Edit `src/strategy/enhanced_strategy.py`:
```python
# Add custom condition in _evaluate_signal()
if custom_condition:
    return 'BUY', 75.0, 'custom_signal', 'Custom logic triggered'
```

---

## Next Steps

1. **Backtest Results**: Test scanner on historical data
2. **Paper Trade**: Run 1-2 weeks with simulated capital
3. **Monitor Accuracy**: Track signal quality vs actual price moves
4. **Refine Thresholds**: Adjust RSI/Drawdown based on results
5. **Live Trading**: Start with 1-2 stocks if confident

---

## Command Reference

```bash
# Help
python stock_scanner.py --help

# Basic scan
python stock_scanner.py --stocks AAPL,SPY,QQQ

# From file
python stock_scanner.py --config stocks_config.txt

# Live data
python stock_scanner.py --stocks AAPL --live

# Export results
python stock_scanner.py --stocks AAPL --output results.json

# Custom thresholds
python stock_scanner.py --stocks AAPL --rsi-oversold 28 --min-drawdown 2.5

# Extended history
python stock_scanner.py --stocks AAPL --days 180

# Combine options
python stock_scanner.py --config stocks.txt --live --output results.json
```

---

**Version**: 1.0
**Status**: Production Ready ✓
**Last Updated**: November 27, 2025
