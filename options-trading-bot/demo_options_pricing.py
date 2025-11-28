#!/usr/bin/env python3
"""
Demo: Options Strategy with Black-Scholes & Monte Carlo

Shows practical examples of:
1. Pricing options with Black-Scholes
2. Comparing to Monte Carlo estimates
3. Analyzing Greeks
4. Risk assessment with VaR/CVaR
5. Technical signal integration
"""

import math
import sys
from datetime import datetime, timedelta
from src.quant.black_scholes import BlackScholesModel, estimate_volatility_from_prices
from src.quant.monte_carlo import MonteCarloSimulator
from src.strategy.options_strategy import OptionsStrategy, format_trade_report


def print_header(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title:^76}  ")
    print("="*80)


def demo_black_scholes_basics():
    """Demo 1: Black-Scholes pricing"""
    print_header("DEMO 1: BLACK-SCHOLES PRICING")
    
    spot = 150.00
    strike = 152.50
    days_to_expiry = 30
    volatility = 0.22
    risk_free_rate = 0.05
    
    print(f"\n📊 Option Setup:")
    print(f"   Spot Price: ${spot}")
    print(f"   Strike: ${strike}")
    print(f"   Days to Expiry: {days_to_expiry}")
    print(f"   Volatility: {volatility:.1%}")
    print(f"   Risk-Free Rate: {risk_free_rate:.1%}")
    
    # Calculate prices
    call_price = BlackScholesModel.call_price(spot, strike, days_to_expiry/365, volatility, risk_free_rate)
    put_price = BlackScholesModel.put_price(spot, strike, days_to_expiry/365, volatility, risk_free_rate)
    
    print(f"\n💰 Theoretical Prices (Black-Scholes):")
    print(f"   Call Price: ${call_price:.2f}")
    print(f"   Put Price: ${put_price:.2f}")
    
    # Verify put-call parity
    diff = call_price - put_price
    expected = spot - strike * math.exp(-risk_free_rate * days_to_expiry/365)
    print(f"\n✓ Put-Call Parity Check:")
    print(f"   C - P = ${diff:.2f}")
    print(f"   S - K*e^(-rT) = ${expected:.2f}")
    print(f"   Difference: ${abs(diff - expected):.4f} (should be ~0)")


def demo_greeks_analysis():
    """Demo 2: Greeks and sensitivity analysis"""
    print_header("DEMO 2: GREEKS & SENSITIVITY ANALYSIS")
    
    spot = 150.00
    strike = 150.00  # ATM
    days_to_expiry = 30
    volatility = 0.22
    
    print(f"\n📊 ATM Option Greeks (Call):")
    print(f"   Stock: ${spot}")
    print(f"   Strike: ${strike}")
    
    greeks = BlackScholesModel.calculate_greeks(
        spot, strike, days_to_expiry/365, volatility, 'call'
    )
    
    print(f"\n📈 Greek Values:")
    print(f"   Price:  ${greeks['price']:.4f}")
    print(f"   Delta:  {greeks['delta']:>7.4f}  (↑ $1 stock = ↑ ${greeks['delta']:.4f} option)")
    print(f"   Gamma:  {greeks['gamma']:>7.6f}  (Delta changes by {greeks['gamma']:.4f} per $1 move)")
    print(f"   Vega:   {greeks['vega']:>7.4f}  (↑ 1% IV = ↑ ${greeks['vega']:.4f} option)")
    print(f"   Theta:  {greeks['theta']:>7.6f}  (Daily decay = ${abs(greeks['theta']):.6f}/day)")
    print(f"   Rho:    {greeks['rho']:>7.4f}  (↑ 1% rate = ↑ ${greeks['rho']:.4f} option)")
    
    # Show sensitivity to different spot prices
    print(f"\n📊 Delta Sensitivity (spot price changes):")
    for new_spot in [145, 148, 150, 152, 155]:
        new_delta = BlackScholesModel.delta(new_spot, strike, days_to_expiry/365, volatility, 'call')
        price_change = new_spot - spot
        print(f"   Stock ${new_spot}: Delta = {new_delta:.4f}")
    
    # Show volatility impact
    print(f"\n📊 Vega Sensitivity (volatility changes):")
    for new_vol in [0.15, 0.20, 0.22, 0.25, 0.30]:
        call = BlackScholesModel.call_price(spot, strike, days_to_expiry/365, new_vol)
        vol_change = (new_vol - volatility) * 100
        print(f"   Vol {new_vol:.0%}: Price = ${call:.4f} ({vol_change:+.0f}% IV)")


def demo_monte_carlo_pricing():
    """Demo 3: Monte Carlo simulation vs Black-Scholes"""
    print_header("DEMO 3: MONTE CARLO vs BLACK-SCHOLES")
    
    spot = 150.00
    strike = 152.50
    days_to_expiry = 30
    volatility = 0.22
    
    print(f"\n📊 Setup: AAPL $152.50 Call (30 DTE)")
    print(f"   Stock: ${spot}")
    print(f"   Volatility: {volatility:.1%}")
    
    # Black-Scholes price
    bs_price = BlackScholesModel.call_price(spot, strike, days_to_expiry/365, volatility)
    print(f"\n💰 Black-Scholes Price: ${bs_price:.4f}")
    
    # Monte Carlo prices with different simulation counts
    print(f"\n🎲 Monte Carlo Simulations:")
    for num_sims in [1000, 5000, 10000]:
        mc_result = MonteCarloSimulator.price_european_option(
            spot, strike, volatility, 0.05, days_to_expiry, 'call', num_sims
        )
        error = abs(mc_result['option_price'] - bs_price)
        error_pct = (error / bs_price) * 100 if bs_price > 0 else 0
        
        print(f"\n   {num_sims:,} simulations:")
        print(f"      Price: ${mc_result['option_price']:.4f}")
        print(f"      95% CI: ${mc_result['ci_lower']:.4f} - ${mc_result['ci_upper']:.4f}")
        print(f"      Error vs BS: {error_pct:.2f}%")


def demo_monte_carlo_probability():
    """Demo 4: Probability analysis"""
    print_header("DEMO 4: MONTE CARLO PROBABILITY ANALYSIS")
    
    spot = 150.00
    volatility = 0.22
    
    print(f"\n📊 Stock: ${spot}")
    print(f"   Volatility: {volatility:.1%}")
    print(f"   Expiration: 30 days")
    
    print(f"\n📈 Call Probability Analysis (Strike, Prob ITM):")
    for strike in [148, 150, 152.50, 155, 157.50]:
        prob = MonteCarloSimulator.calculate_probability_itm(
            spot, strike, volatility, 0.05, 30, 'call', 5000
        )
        moneyness = (strike - spot) / spot * 100
        print(f"   ${strike:>6.2f} ({moneyness:>+5.1f}%): {prob['prob_itm_at_expiry']:>5.1%}")


def demo_risk_analysis():
    """Demo 5: VaR and risk metrics"""
    print_header("DEMO 5: RISK ANALYSIS (VaR/CVaR)")
    
    print(f"\n📊 Position Setup:")
    print(f"   Position: Long 5 AAPL $152.50 Calls")
    print(f"   Current Stock: $150")
    print(f"   Volatility: 22%")
    
    var_result = MonteCarloSimulator.calculate_var_cvar(
        spot_price=150.00,
        strike_price=152.50,
        position_size=5,
        option_type='call',
        volatility=0.22,
        risk_free_rate=0.05,
        days_to_expiry=30,
        num_simulations=10000
    )
    
    print(f"\n⚠️  Risk Metrics (95% Confidence):")
    print(f"   Value at Risk (VaR): ${var_result['var_95']:>8.2f}")
    print(f"   (95% chance loss ≤ this amount)")
    
    print(f"\n   Conditional VaR (CVaR): ${var_result['cvar_95']:>6.2f}")
    print(f"   (Average loss if VaR exceeded)")
    
    print(f"\n📊 Price Distribution Percentiles:")
    print(f"   Worst Case (1%): ${var_result['worst_loss']:>8.2f}")
    print(f"   10th %ile: ${var_result['percentile_10']:>8.2f}")
    print(f"   Median: ${var_result['median_pnl']:>8.2f}")
    print(f"   90th %ile: ${var_result['percentile_90']:>8.2f}")
    print(f"   Best Case: ${var_result['best_gain']:>8.2f}")


def demo_integrated_strategy():
    """Demo 6: Full integrated strategy analysis"""
    print_header("DEMO 6: INTEGRATED OPTIONS STRATEGY")
    
    print(f"\n🤖 Setting up strategy with:")
    print(f"   Account Size: $50,000")
    print(f"   Max Risk per Trade: 2%")
    
    strat = OptionsStrategy(account_size=50000, max_risk_percent=0.02)
    
    # Generate synthetic price data (downtrend = RSI oversold)
    print(f"\n📊 Generating synthetic AAPL price data...")
    closes = []
    
    # Downtrend (days 1-20): 150 → 145
    for i in range(20):
        price = 150 - (i * 0.25) + (i % 3) * 0.1
        closes.append(price)
    
    # Recovery (days 21-30): 145 → 149
    for i in range(10):
        price = 145 + (i * 0.4)
        closes.append(price)
    
    current_price = closes[-1]
    print(f"   Days: 30 | Price range: ${min(closes):.2f} - ${max(closes):.2f}")
    print(f"   Current price: ${current_price:.2f}")
    
    # Analyze call opportunity
    print(f"\n🔍 Analyzing $150 Call (30 DTE)...")
    trade = strat.analyze(
        symbol='AAPL',
        closes=closes,
        current_price=current_price,
        strike_price=150.00,
        days_to_expiry=30,
        option_type='call',
        num_simulations=5000
    )
    
    if trade:
        print(f"\n{format_trade_report(trade)}")
    else:
        print("❌ Insufficient data for analysis")


def demo_strike_ladder():
    """Demo 7: Strike ladder analysis"""
    print_header("DEMO 7: STRIKE LADDER ANALYSIS")
    
    strat = OptionsStrategy()
    
    # Synthetic price data
    closes = [100 - 5*math.sin(i/10) for i in range(30)]
    current_price = 100
    
    print(f"\n📊 Analyzing multiple strikes for same expiration")
    print(f"   Stock: SPY @ ${current_price}")
    print(f"   Expiration: 30 days")
    print(f"   Analysis: Call options\n")
    
    results = strat.analyze_strike_ladder(
        symbol='SPY',
        closes=closes,
        current_price=current_price,
        strikes=[98, 99, 100, 101, 102],
        days_to_expiry=30,
        option_type='call'
    )
    
    print(f"📈 Strike Analysis Results:")
    print(f"\n{'Strike':<10} {'Price':<10} {'Delta':<10} {'Prob ITM':<12} {'Recommendation':<15}")
    print(f"{'-'*57}")
    
    for strike in sorted(results.keys()):
        trade = results[strike]
        print(f"${strike:<9.2f} ${trade.bs_price:<9.2f} {trade.delta:>+7.3f}    "
              f"{trade.prob_itm:>6.1%}      {trade.recommendation:<15}")


def main():
    """Run all demos"""
    print("\n" + "🚀 "*20)
    print("OPTIONS PRICING & RISK ANALYSIS - COMPREHENSIVE DEMO")
    print("🚀 "*20)
    
    try:
        demo_black_scholes_basics()
        demo_greeks_analysis()
        demo_monte_carlo_pricing()
        demo_monte_carlo_probability()
        demo_risk_analysis()
        demo_integrated_strategy()
        demo_strike_ladder()
        
        print_header("DEMO COMPLETE ✓")
        print("\n✅ All demonstrations completed successfully!\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
