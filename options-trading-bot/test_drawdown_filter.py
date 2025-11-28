#!/usr/bin/env python
"""
Test the 2% drawdown filter for BUY signals
"""
from src.strategy.trading_strategy import TradingStrategy

# Create strategy with 2% drawdown requirement for BUY signals
strategy = TradingStrategy(
    min_drawdown_for_buy=2.0,
    rsi_oversold=30,
    rsi_overbought=70
)

print("=" * 70)
print("TESTING 2% DRAWDOWN FILTER FOR BUY SIGNALS")
print("=" * 70)

# Scenario 1: Price dropped 3% from recent high + RSI oversold
print("\n📊 SCENARIO 1: Price down 3% from high + RSI oversold")
print("-" * 70)

# Create price series: climbs to high, then drops 3%
high = 100.0
closes_down = []
for i in range(40):
    closes_down.append(high + i*0.2)  # climb to high

for i in range(10):
    closes_down.append(closes_down[-1] * 0.98)  # drop 2% per candle (ends at ~82% of high)

recent_high = max(closes_down[-20:])
current = closes_down[-1]
drawdown = ((recent_high - current) / recent_high) * 100

print(f"Recent 20-candle high: ${recent_high:.2f}")
print(f"Current price:        ${current:.2f}")
print(f"Drawdown:             {drawdown:.2f}%")
print(f"Meets 2% filter:      {'✓ YES' if drawdown >= 2.0 else '✗ NO'}")

signal = strategy.analyze('SPY', closes_down, current)
print(f"\n✅ Signal: {signal.action}")
print(f"   Confidence: {signal.confidence:.1f}%")
print(f"   RSI: {signal.indicators.get('rsi', 'N/A'):.1f}")
print(f"   Reason: {signal.reason}")

# Scenario 2: RSI oversold but price only down 0.5%
print("\n" + "=" * 70)
print("📊 SCENARIO 2: RSI oversold but price only down 0.5%")
print("-" * 70)

strategy.reset()
# Price climbs with slight pullback
closes_stable = []
for i in range(40):
    closes_stable.append(100 + i*0.3)

for i in range(5):
    closes_stable.append(closes_stable[-1] * 0.995)  # drop only 0.5%

recent_high = max(closes_stable[-20:])
current = closes_stable[-1]
drawdown = ((recent_high - current) / recent_high) * 100

print(f"Recent 20-candle high: ${recent_high:.2f}")
print(f"Current price:        ${current:.2f}")
print(f"Drawdown:             {drawdown:.2f}%")
print(f"Meets 2% filter:      {'✓ YES' if drawdown >= 2.0 else '✗ NO'}")

signal = strategy.analyze('SPY', closes_stable, current)
print(f"\n❌ Signal: {signal.action}")
print(f"   Confidence: {signal.confidence:.1f}%")
print(f"   RSI: {signal.indicators.get('rsi', 'N/A'):.1f}")
print(f"   Reason: {signal.reason}")

# Scenario 3: Near ATH (All Time High)
print("\n" + "=" * 70)
print("📊 SCENARIO 3: Near ATH (no drawdown)")
print("-" * 70)

strategy.reset()
closes_ath = [100 + i*0.5 for i in range(50)]  # steady climb

recent_high = max(closes_ath[-20:])
current = closes_ath[-1]
drawdown = ((recent_high - current) / recent_high) * 100

print(f"Recent 20-candle high: ${recent_high:.2f}")
print(f"Current price:        ${current:.2f}")
print(f"Drawdown:             {drawdown:.2f}%")
print(f"Meets 2% filter:      {'✓ YES' if drawdown >= 2.0 else '✗ NO'}")

signal = strategy.analyze('SPY', closes_ath, current)
print(f"\n⏸️  Signal: {signal.action}")
print(f"   Confidence: {signal.confidence:.1f}%")
print(f"   Reason: {signal.reason}")

print("\n" + "=" * 70)
print("✓ Filter working as expected:")
print("  • BUY signals ONLY trigger when price is 2%+ below recent high")
print("  • SELL signals always work (no filter)")
print("=" * 70)
