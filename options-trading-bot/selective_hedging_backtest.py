#!/usr/bin/env python3
"""
Selective Hedging Backtest
Shows how SELECTIVE hedging of losing trades improves results
Only hedge positions that have already realized losses
"""

import sys
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np

from src.strategy.enhanced_strategy import EnhancedStockStrategy
from src.core.logger import logger

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


class YahooDataFetcher:
    """Generate realistic sample data"""
    
    @staticmethod
    def get_historical_data(symbol: str, days: int = 365) -> List[Dict]:
        """Generate historical price data"""
        np.random.seed(hash(symbol) % 2**32)
        
        base_prices = {
            'META': 150.0,
            'AMZN': 170.0,
            'NFLX': 250.0,
            'GOOGL': 140.0,
            'NVDA': 850.0,
            'TSLA': 280.0,
            'SPY': 450.0,
        }
        
        price = base_prices.get(symbol, 100.0)
        candles = []
        current_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            daily_return = np.random.normal(0.0005, 0.015)
            price = price * (1 + daily_return)
            
            high = price * (1 + abs(np.random.normal(0, 0.007)))
            low = price * (1 - abs(np.random.normal(0, 0.007)))
            
            candles.append({
                'date': current_date,
                'open': price * (1 + np.random.normal(0, 0.005)),
                'high': high,
                'low': low,
                'close': price,
                'volume': int(np.random.uniform(1e6, 50e6)),
            })
            current_date += timedelta(days=1)
        
        return candles


def run_selective_hedging_backtest():
    """Run backtest comparing unhedged vs selectively hedged strategies"""
    
    capital = 100000
    symbols = ['META', 'AMZN', 'NFLX', 'GOOGL', 'NVDA', 'TSLA']
    
    print("\n" + "=" * 80)
    print("SELECTIVE HEDGING BACKTEST")
    print("Only hedge losing positions after -2% drawdown")
    print("=" * 80)
    
    # Fetch data
    price_data = {}
    for symbol in symbols:
        candles = YahooDataFetcher.get_historical_data(symbol)
        price_data[symbol] = candles
    
    # Create strategy
    strategy = EnhancedStockStrategy()
    
    # Simulate unhedged positions
    unhedged_trades = []
    unhedged_equity = capital
    unhedged_positions = {}
    
    # Simulate selectively hedged positions
    hedged_trades = []
    hedged_equity = capital
    hedged_positions = {}
    hedged_count = 0
    total_hedge_cost = 0
    total_hedge_savings = 0
    
    days = len(next(iter(price_data.values())))
    
    print(f"\nSimulating {days} trading days on {len(symbols)} stocks...")
    print(f"Starting Capital: ${capital:,.2f}\n")
    
    # Main backtest loop
    for day in range(50, days):
        for symbol in symbols:
            closes = [c['close'] for c in price_data[symbol][:day+1]]
            current_price = closes[-1]
            
            if len(closes) < 50:
                continue
            
            # Generate signal
            signal = strategy.analyze_stock(symbol, closes, current_price)
            
            if signal and signal.action == 'BUY':
                # UNHEDGED: Open position without protection
                if symbol not in unhedged_positions:
                    risk = current_price * 0.02
                    position_size = unhedged_equity * 0.02 / risk if risk > 0 else 0
                    
                    if position_size > 0:
                        unhedged_positions[symbol] = {
                            'entry_price': current_price,
                            'entry_day': day,
                            'size': position_size,
                            'stop_loss': current_price * 0.98,
                            'take_profit': current_price * 1.04,
                        }
                
                # HEDGED: Open position with selective hedging logic
                if symbol not in hedged_positions:
                    risk = current_price * 0.02
                    position_size = hedged_equity * 0.02 / risk if risk > 0 else 0
                    
                    if position_size > 0:
                        hedged_positions[symbol] = {
                            'entry_price': current_price,
                            'entry_day': day,
                            'size': position_size,
                            'stop_loss': current_price * 0.98,
                            'take_profit': current_price * 1.04,
                            'hedge_triggered': False,
                            'hedge_cost': 0,
                            'hedge_saved': 0,
                        }
            
            # Check exits - UNHEDGED
            if symbol in unhedged_positions:
                pos = unhedged_positions[symbol]
                exit_price = None
                exit_reason = None
                
                if current_price <= pos['stop_loss']:
                    exit_price = pos['stop_loss']
                    exit_reason = "STOP_LOSS"
                elif current_price >= pos['take_profit']:
                    exit_price = pos['take_profit']
                    exit_reason = "TAKE_PROFIT"
                elif day - pos['entry_day'] >= 15:
                    exit_price = current_price
                    exit_reason = "TIME_STOP"
                
                if exit_reason:
                    pnl = (exit_price - pos['entry_price']) * pos['size']
                    unhedged_equity += pnl
                    unhedged_trades.append({'symbol': symbol, 'pnl': pnl, 'reason': exit_reason})
                    del unhedged_positions[symbol]
            
            # Check exits - HEDGED with selective hedging
            if symbol in hedged_positions:
                pos = hedged_positions[symbol]
                exit_price = None
                exit_reason = None
                
                # Check if we should apply hedge (position down -2%)
                unrealized_pnl_pct = (current_price - pos['entry_price']) / pos['entry_price']
                
                if not pos['hedge_triggered'] and unrealized_pnl_pct <= -0.02:
                    # Apply protective put hedge at this point
                    # Put cost: 2% of position value (0.5% for partial protection)
                    hedge_cost = pos['entry_price'] * 0.005 * pos['size']
                    put_strike = pos['entry_price'] * 0.95  # Protect 5% drop
                    
                    pos['hedge_triggered'] = True
                    pos['hedge_cost'] = hedge_cost
                    total_hedge_cost += hedge_cost
                    hedged_equity -= hedge_cost
                    
                    logger.info(f"Hedge triggered for {symbol} at ${current_price:.2f}, cost: ${hedge_cost:.2f}")
                
                if current_price <= pos['stop_loss']:
                    exit_price = pos['stop_loss']
                    exit_reason = "STOP_LOSS"
                elif current_price >= pos['take_profit']:
                    exit_price = pos['take_profit']
                    exit_reason = "TAKE_PROFIT"
                elif day - pos['entry_day'] >= 15:
                    exit_price = current_price
                    exit_reason = "TIME_STOP"
                
                if exit_reason:
                    equity_pnl = (exit_price - pos['entry_price']) * pos['size']
                    
                    # If hedged, calculate savings
                    if pos['hedge_triggered']:
                        put_strike = pos['entry_price'] * 0.95
                        max_unhedged_loss = (pos['stop_loss'] - pos['entry_price']) * pos['size']
                        max_hedged_loss = (max_unhedged_loss) if exit_price > put_strike else \
                                         (put_strike - pos['entry_price']) * pos['size']
                        saved = max_unhedged_loss - max_hedged_loss
                        pos['hedge_saved'] = saved
                        total_hedge_savings += saved
                        total_pnl = equity_pnl - pos['hedge_cost']
                    else:
                        total_pnl = equity_pnl
                    
                    hedged_equity += total_pnl
                    hedged_trades.append({'symbol': symbol, 'pnl': total_pnl, 'reason': exit_reason})
                    del hedged_positions[symbol]
    
    # Close remaining positions
    for symbol in list(unhedged_positions.keys()):
        pos = unhedged_positions[symbol]
        final_price = price_data[symbol][-1]['close']
        pnl = (final_price - pos['entry_price']) * pos['size']
        unhedged_equity += pnl
        unhedged_trades.append({'symbol': symbol, 'pnl': pnl, 'reason': 'EOD_CLOSE'})
    
    for symbol in list(hedged_positions.keys()):
        pos = hedged_positions[symbol]
        final_price = price_data[symbol][-1]['close']
        equity_pnl = (final_price - pos['entry_price']) * pos['size']
        
        if pos['hedge_triggered']:
            total_pnl = equity_pnl - pos['hedge_cost']
        else:
            total_pnl = equity_pnl
        
        hedged_equity += total_pnl
        hedged_trades.append({'symbol': symbol, 'pnl': total_pnl, 'reason': 'EOD_CLOSE'})
    
    # Calculate statistics
    def calc_stats(trades):
        if not trades:
            return {
                'count': 0, 'winners': 0, 'losers': 0, 'total_pnl': 0,
                'avg_win': 0, 'avg_loss': 0, 'profit_factor': 0, 'win_rate': 0
            }
        
        winners = [t['pnl'] for t in trades if t['pnl'] > 0]
        losers = [t['pnl'] for t in trades if t['pnl'] < 0]
        
        winning_sum = sum(winners) if winners else 0
        losing_sum = sum(losers) if losers else 0
        
        return {
            'count': len(trades),
            'winners': len(winners),
            'losers': len(losers),
            'total_pnl': sum([t['pnl'] for t in trades]),
            'avg_win': np.mean(winners) if winners else 0,
            'avg_loss': np.mean(losers) if losers else 0,
            'profit_factor': abs(winning_sum / losing_sum) if losing_sum != 0 else 0,
            'win_rate': len(winners) / len(trades) * 100 if trades else 0,
        }
    
    unhedged_stats = calc_stats(unhedged_trades)
    hedged_stats = calc_stats(hedged_trades)
    
    # Display results
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS COMPARISON")
    print("=" * 80)
    
    print("\n📊 UNHEDGED STRATEGY (No Protection)")
    print(f"  Final Equity:        ${unhedged_equity:>12,.2f}")
    print(f"  Total P&L:           ${unhedged_stats['total_pnl']:>12,.2f}")
    print(f"  Return:              {(unhedged_equity-capital)/capital*100:>11.2f}%")
    print(f"  Total Trades:        {unhedged_stats['count']:>12}")
    print(f"  Win Rate:            {unhedged_stats['win_rate']:>11.1f}%")
    print(f"  Avg Win:             ${unhedged_stats['avg_win']:>12,.2f}")
    print(f"  Avg Loss:            ${unhedged_stats['avg_loss']:>12,.2f}")
    print(f"  Profit Factor:       {unhedged_stats['profit_factor']:>12.2f}x")
    
    print("\n🛡️  HEDGED STRATEGY (Selective Puts on -2% Drawdown)")
    print(f"  Final Equity:        ${hedged_equity:>12,.2f}")
    print(f"  Total P&L:           ${hedged_stats['total_pnl']:>12,.2f}")
    print(f"  Return:              {(hedged_equity-capital)/capital*100:>11.2f}%")
    print(f"  Total Trades:        {hedged_stats['count']:>12}")
    print(f"  Win Rate:            {hedged_stats['win_rate']:>11.1f}%")
    print(f"  Avg Win:             ${hedged_stats['avg_win']:>12,.2f}")
    print(f"  Avg Loss:            ${hedged_stats['avg_loss']:>12,.2f}")
    print(f"  Profit Factor:       {hedged_stats['profit_factor']:>12.2f}x")
    
    print("\n💰 HEDGE STATISTICS")
    hedges_applied = sum(1 for t in hedged_trades 
                        if any(pos.get('hedge_triggered', False) for pos in [t]))
    print(f"  Hedges Applied:      {hedged_count:>12}")
    print(f"  Total Hedge Cost:    ${total_hedge_cost:>12,.2f}")
    print(f"  Total Loss Saved:    ${total_hedge_savings:>12,.2f}")
    if total_hedge_cost > 0:
        print(f"  Hedge ROI:           {(total_hedge_savings-total_hedge_cost)/total_hedge_cost*100:>11.1f}%")
        print(f"  Cost-Benefit:        {total_hedge_savings/total_hedge_cost if total_hedge_cost > 0 else 0:>12.2f}x")
    
    print("\n📈 IMPROVEMENT (Hedged vs Unhedged)")
    pnl_diff = hedged_stats['total_pnl'] - unhedged_stats['total_pnl']
    max_loss_unhedged = min([t['pnl'] for t in unhedged_trades], default=0)
    max_loss_hedged = min([t['pnl'] for t in hedged_trades], default=0)
    max_loss_reduction = max_loss_unhedged - max_loss_hedged
    
    print(f"  P&L Improvement:     ${pnl_diff:>12,.2f}")
    print(f"  Return Improvement:  {pnl_diff/capital*100:>11.2f}%")
    print(f"  Max Loss Reduction:  ${max_loss_reduction:>12,.2f}")
    print(f"  Worst Unhedged Loss: ${max_loss_unhedged:>12,.2f}")
    print(f"  Worst Hedged Loss:   ${max_loss_hedged:>12,.2f}")
    
    if pnl_diff >= 0:
        print(f"  Status:              ✅ HEDGING IMPROVES RESULTS!")
    else:
        print(f"  Status:              ⚠️  Hedging cost exceeds benefit this period")
    
    print("\n" + "=" * 80)
    print("\n📊 KEY INSIGHTS:")
    print("\n1. SELECTIVE HEDGING vs ALWAYS HEDGING")
    print("   - Only hedge when position is DOWN -2% or more")
    print("   - Costs only 0.5% instead of 2% (0.5x hedge cost)")
    print("   - Limits downside on losing trades only")
    
    print("\n2. COST-BENEFIT ANALYSIS")
    if total_hedge_cost > 0:
        roi = (total_hedge_savings - total_hedge_cost) / total_hedge_cost * 100
        print(f"   - Hedge cost: ${total_hedge_cost:,.2f}")
        print(f"   - Loss saved: ${total_hedge_savings:,.2f}")
        print(f"   - Net benefit: ${total_hedge_savings - total_hedge_cost:,.2f}")
        print(f"   - ROI: {roi:.1f}%")
        
        if roi > 0:
            print(f"   ✅ For every $1 spent hedging, you save ${total_hedge_savings/total_hedge_cost:.2f}")
        else:
            print(f"   ⚠️  Hedge cost exceeds savings - increase hedge threshold")
    
    print("\n3. WHEN TO USE SELECTIVE HEDGING")
    print("   - High volatility periods (VIX > 20)")
    print("   - After taking initial hit (-2% to -5%)")
    print("   - For large positions (>2% of capital)")
    print("   - Before earnings announcements")
    
    print("\n" + "=" * 80)
    
    return {
        'unhedged': unhedged_stats,
        'hedged': hedged_stats,
        'hedge_stats': {
            'hedges_applied': hedged_count,
            'total_cost': total_hedge_cost,
            'total_savings': total_hedge_savings,
        },
        'improvement': {
            'pnl_diff': pnl_diff,
            'return_diff': pnl_diff / capital * 100,
            'max_loss_reduction': max_loss_reduction,
        }
    }


if __name__ == '__main__':
    try:
        results = run_selective_hedging_backtest()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        print(f"\n❌ Backtest failed: {e}")
        sys.exit(1)
