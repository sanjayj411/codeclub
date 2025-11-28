"""
Options Hedging Strategy
Protects long equity positions by purchasing protective puts
Optimizes hedge costs vs protection levels
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np
from datetime import datetime, timedelta

from src.core.logger import logger


class HedgeStrategy(Enum):
    """Hedging approach options"""
    NO_HEDGE = "no_hedge"                      # No hedging
    PROTECTIVE_PUT = "protective_put"          # Buy puts at entry
    COLLAR = "collar"                          # Buy puts + sell calls
    DYNAMIC_HEDGE = "dynamic_hedge"            # Adjust hedge based on P&L
    PARTIAL_HEDGE = "partial_hedge"            # Hedge only part of position


@dataclass
class HedgeParameters:
    """Configuration for options hedging"""
    strategy: HedgeStrategy = HedgeStrategy.PROTECTIVE_PUT
    put_delta: float = 0.25                    # 25 delta put (more OTM = cheaper)
    put_strike_pct: float = 0.95               # Buy puts 5% below entry
    put_cost_pct: float = 0.02                 # Assume 2% cost for put option
    call_strike_pct: float = 1.10              # Sell calls 10% above entry
    call_premium_pct: float = 0.015            # Get 1.5% credit from call sale
    hedge_threshold: float = -0.03             # Start hedging at -3% unrealized loss
    partial_hedge_pct: float = 0.50            # Hedge 50% of position in partial strategy
    max_hedge_cost_pct: float = 0.05           # Don't spend > 5% on hedges
    rebalance_interval: int = 5                # Days between hedge rebalance


@dataclass
class HedgePosition:
    """Represents a hedged position"""
    symbol: str
    entry_price: float
    entry_date: datetime
    position_size: int
    
    # Equity position
    equity_pnl: float = 0.0
    current_price: float = 0.0
    
    # Hedge details
    hedge_type: str = ""
    put_strike: float = 0.0
    put_cost: float = 0.0
    call_strike: float = 0.0
    call_premium: float = 0.0
    
    # Performance
    hedge_pnl: float = 0.0
    total_pnl: float = 0.0
    effective_stop_loss: float = 0.0
    
    # Status
    is_hedged: bool = False
    hedge_expires_date: Optional[datetime] = None
    last_rebalance: Optional[datetime] = None


class OptionsHedgeManager:
    """Manages protective options hedges for equity positions"""
    
    def __init__(self, params: HedgeParameters = None):
        """Initialize hedge manager"""
        self.params = params or HedgeParameters()
        self.hedged_positions: Dict[str, HedgePosition] = {}
        self.hedge_history = []
        self.total_hedge_cost = 0.0
        self.total_hedge_benefit = 0.0
    
    def evaluate_hedge_need(self,
                           symbol: str,
                           current_price: float,
                           entry_price: float,
                           position_size: int,
                           unrealized_pnl: float,
                           unrealized_pnl_pct: float) -> Tuple[bool, str]:
        """Determine if position needs hedging"""
        
        if self.params.strategy == HedgeStrategy.NO_HEDGE:
            return False, "Hedging disabled"
        
        # Check if loss threshold exceeded
        if unrealized_pnl_pct < self.params.hedge_threshold:
            return True, f"Loss threshold: {unrealized_pnl_pct:.2%}"
        
        # Protective put: always hedge at entry
        if self.params.strategy == HedgeStrategy.PROTECTIVE_PUT:
            if symbol not in self.hedged_positions:
                return True, "New position - protective put recommended"
        
        # Dynamic: only hedge if losing
        if self.params.strategy == HedgeStrategy.DYNAMIC_HEDGE:
            if unrealized_pnl_pct < -0.02:  # -2%
                return True, "Dynamic: Position losing, hedge triggered"
        
        # Check if hedge needs rebalancing
        if symbol in self.hedged_positions:
            pos = self.hedged_positions[symbol]
            if pos.last_rebalance is None:
                return False, "Hedge in place"
            
            days_since = (datetime.now() - pos.last_rebalance).days
            if days_since > self.params.rebalance_interval:
                return True, "Hedge rebalance due"
        
        return False, "No hedge needed"
    
    def calculate_protective_put(self,
                                entry_price: float,
                                current_price: float,
                                position_size: int) -> HedgePosition:
        """Calculate protective put hedge details"""
        
        # Put strike 5% below entry (out of the money)
        put_strike = entry_price * self.params.put_strike_pct
        
        # Put cost (assume 2% of position value)
        put_cost_per_share = entry_price * self.params.put_cost_pct
        put_cost_total = put_cost_per_share * position_size
        
        # Effective protection: any loss below put strike is limited
        max_loss = (entry_price - put_strike) * position_size
        protection_value = max_loss - put_cost_total
        
        hedge = HedgePosition(
            symbol="",
            entry_price=entry_price,
            entry_date=datetime.now(),
            position_size=position_size,
            current_price=current_price,
            hedge_type="PROTECTIVE_PUT",
            put_strike=put_strike,
            put_cost=put_cost_total,
            call_strike=0.0,
            call_premium=0.0,
            effective_stop_loss=put_strike,
            is_hedged=True,
            hedge_expires_date=datetime.now() + timedelta(days=30),
            last_rebalance=datetime.now(),
        )
        
        logger.info(f"Protective put: Strike=${put_strike:.2f}, Cost=${put_cost_total:.2f}")
        return hedge
    
    def calculate_collar(self,
                        entry_price: float,
                        current_price: float,
                        position_size: int) -> HedgePosition:
        """Calculate collar hedge (buy puts + sell calls)"""
        
        # Buy puts
        put_strike = entry_price * self.params.put_strike_pct
        put_cost_per_share = entry_price * self.params.put_cost_pct
        put_cost_total = put_cost_per_share * position_size
        
        # Sell calls
        call_strike = entry_price * self.params.call_strike_pct
        call_premium_per_share = entry_price * self.params.call_premium_pct
        call_premium_total = call_premium_per_share * position_size
        
        # Net cost
        net_cost = put_cost_total - call_premium_total
        
        # Effective range: protected below put, capped above call
        max_loss = (entry_price - put_strike) * position_size - net_cost
        max_gain = (call_strike - entry_price) * position_size + net_cost
        
        hedge = HedgePosition(
            symbol="",
            entry_price=entry_price,
            entry_date=datetime.now(),
            position_size=position_size,
            current_price=current_price,
            hedge_type="COLLAR",
            put_strike=put_strike,
            put_cost=put_cost_total,
            call_strike=call_strike,
            call_premium=call_premium_total,
            effective_stop_loss=put_strike,
            is_hedged=True,
            hedge_expires_date=datetime.now() + timedelta(days=30),
            last_rebalance=datetime.now(),
        )
        
        logger.info(f"Collar: Put ${put_strike:.2f}, Call ${call_strike:.2f}, Net Cost ${net_cost:.2f}")
        return hedge
    
    def calculate_dynamic_hedge(self,
                               entry_price: float,
                               current_price: float,
                               position_size: int,
                               unrealized_pnl_pct: float) -> HedgePosition:
        """Calculate dynamic hedge based on current loss level"""
        
        # Scale hedge based on loss severity
        loss_severity = abs(unrealized_pnl_pct)  # e.g., 0.05 for -5% loss
        
        if loss_severity < 0.02:
            hedge_pct = 0.25  # Light hedge
        elif loss_severity < 0.05:
            hedge_pct = 0.50  # Medium hedge
        else:
            hedge_pct = 0.75  # Heavy hedge
        
        # Adjust put strike based on severity
        put_strike_offset = 0.95 - (hedge_pct * 0.10)  # More protection = closer to current
        put_strike = entry_price * put_strike_offset
        
        # Scale put cost with protection level
        put_cost_per_share = entry_price * self.params.put_cost_pct * hedge_pct
        put_cost_total = put_cost_per_share * position_size
        
        hedge = HedgePosition(
            symbol="",
            entry_price=entry_price,
            entry_date=datetime.now(),
            position_size=position_size,
            current_price=current_price,
            hedge_type=f"DYNAMIC_HEDGE_{int(hedge_pct*100)}%",
            put_strike=put_strike,
            put_cost=put_cost_total,
            effective_stop_loss=put_strike,
            is_hedged=True,
            hedge_expires_date=datetime.now() + timedelta(days=30),
            last_rebalance=datetime.now(),
        )
        
        logger.info(f"Dynamic hedge: {int(hedge_pct*100)}% coverage, Put ${put_strike:.2f}")
        return hedge
    
    def calculate_partial_hedge(self,
                               entry_price: float,
                               current_price: float,
                               position_size: int) -> HedgePosition:
        """Hedge only portion of position"""
        
        # Hedge 50% of position
        hedged_size = int(position_size * self.params.partial_hedge_pct)
        
        # Put strike
        put_strike = entry_price * self.params.put_strike_pct
        
        # Cost only for hedged portion
        put_cost_per_share = entry_price * self.params.put_cost_pct
        put_cost_total = put_cost_per_share * hedged_size
        
        hedge = HedgePosition(
            symbol="",
            entry_price=entry_price,
            entry_date=datetime.now(),
            position_size=hedged_size,  # Only hedged portion
            current_price=current_price,
            hedge_type=f"PARTIAL_HEDGE_{int(self.params.partial_hedge_pct*100)}%",
            put_strike=put_strike,
            put_cost=put_cost_total,
            effective_stop_loss=put_strike,
            is_hedged=True,
            hedge_expires_date=datetime.now() + timedelta(days=30),
            last_rebalance=datetime.now(),
        )
        
        logger.info(f"Partial hedge: {hedged_size} shares ({self.params.partial_hedge_pct*100:.0f}%), Put ${put_strike:.2f}")
        return hedge
    
    def hedge_position(self,
                      symbol: str,
                      entry_price: float,
                      current_price: float,
                      position_size: int,
                      unrealized_pnl_pct: float = 0.0) -> Tuple[bool, HedgePosition]:
        """Apply hedge to position based on strategy"""
        
        # Check if hedging is justified
        needs_hedge, reason = self.evaluate_hedge_need(
            symbol, current_price, entry_price, position_size, 0, unrealized_pnl_pct
        )
        
        if not needs_hedge:
            logger.info(f"{symbol}: {reason}")
            return False, None
        
        # Select hedge type
        if self.params.strategy == HedgeStrategy.PROTECTIVE_PUT:
            hedge = self.calculate_protective_put(entry_price, current_price, position_size)
        
        elif self.params.strategy == HedgeStrategy.COLLAR:
            hedge = self.calculate_collar(entry_price, current_price, position_size)
        
        elif self.params.strategy == HedgeStrategy.DYNAMIC_HEDGE:
            hedge = self.calculate_dynamic_hedge(entry_price, current_price, position_size, unrealized_pnl_pct)
        
        elif self.params.strategy == HedgeStrategy.PARTIAL_HEDGE:
            hedge = self.calculate_partial_hedge(entry_price, current_price, position_size)
        
        else:
            return False, None
        
        # Store hedge
        hedge.symbol = symbol
        self.hedged_positions[symbol] = hedge
        self.total_hedge_cost += hedge.put_cost - hedge.call_premium
        
        self.hedge_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'hedge_type': hedge.hedge_type,
            'entry_price': entry_price,
            'put_strike': hedge.put_strike,
            'cost': hedge.put_cost - hedge.call_premium,
        })
        
        logger.info(f"✓ Hedged {symbol}: {hedge.hedge_type}")
        return True, hedge
    
    def update_hedge_pnl(self,
                        symbol: str,
                        current_price: float,
                        position_pnl: float) -> Optional[HedgePosition]:
        """Update P&L of hedged position"""
        
        if symbol not in self.hedged_positions:
            return None
        
        hedge = self.hedged_positions[symbol]
        hedge.current_price = current_price
        hedge.equity_pnl = position_pnl
        
        # Calculate hedge payoff
        # Put protects against loss below strike
        if current_price < hedge.put_strike:
            # Put is in the money
            hedge.hedge_pnl = (hedge.put_strike - current_price) * hedge.position_size - hedge.put_cost
        else:
            # Put is out of the money (only lost premium)
            hedge.hedge_pnl = -hedge.put_cost
        
        # Adjust if collar (cap gains at call strike)
        if hedge.hedge_type == "COLLAR":
            if current_price > hedge.call_strike:
                # Call is in the money, limit gains
                capped_price = hedge.call_strike
                hedge.equity_pnl = (capped_price - hedge.entry_price) * hedge.position_size
            hedge.hedge_pnl += hedge.call_premium  # Add call credit
        
        # Total P&L with hedge
        hedge.total_pnl = hedge.equity_pnl + hedge.hedge_pnl
        
        self.total_hedge_benefit += hedge.hedge_pnl
        
        return hedge
    
    def evaluate_hedge_performance(self) -> Dict:
        """Evaluate overall hedge performance"""
        
        total_cost = sum([h.put_cost - h.call_premium for h in self.hedged_positions.values()])
        total_benefit = sum([h.hedge_pnl for h in self.hedged_positions.values()])
        
        # Count protected losses
        protected_positions = 0
        loss_saved = 0.0
        
        for hedge in self.hedged_positions.values():
            if hedge.current_price < hedge.entry_price:
                protected_positions += 1
                # Calculate what loss would have been without hedge
                unhedged_loss = (hedge.entry_price - hedge.current_price) * hedge.position_size
                # Compare to hedged loss
                hedged_loss = abs(hedge.total_pnl)
                loss_saved += max(0, unhedged_loss - hedged_loss)
        
        return {
            'total_hedges': len(self.hedged_positions),
            'hedged_symbols': list(self.hedged_positions.keys()),
            'total_hedge_cost': total_cost,
            'total_hedge_benefit': total_benefit,
            'protected_positions': protected_positions,
            'loss_saved': loss_saved,
            'cost_benefit_ratio': total_benefit / total_cost if total_cost > 0 else 0,
            'roi': (total_benefit - total_cost) / total_cost * 100 if total_cost > 0 else 0,
        }
    
    def get_hedge_summary(self) -> str:
        """Get human-readable hedge summary"""
        
        perf = self.evaluate_hedge_performance()
        
        summary = f"""
Hedge Performance Summary:
├─ Hedged Positions: {perf['total_hedges']}
├─ Total Hedge Cost: ${perf['total_hedge_cost']:.2f}
├─ Total Benefit: ${perf['total_hedge_benefit']:.2f}
├─ Protected Positions: {perf['protected_positions']}
├─ Loss Saved: ${perf['loss_saved']:.2f}
├─ Cost-Benefit Ratio: {perf['cost_benefit_ratio']:.2f}x
└─ ROI: {perf['roi']:.1f}%
"""
        return summary


class HedgedBacktester:
    """Backtest trading strategy with options hedging"""
    
    def __init__(self, base_strategy, hedge_params: HedgeParameters = None):
        self.base_strategy = base_strategy
        self.hedge_params = hedge_params or HedgeParameters()
        self.hedge_manager = OptionsHedgeManager(hedge_params)
        self.equity = 0.0
        self.positions = {}
        self.closed_trades = []
    
    def compare_strategies(self, price_data: Dict, spy_data: List) -> Dict:
        """Compare unhedged vs hedged strategy performance"""
        
        results = {
            'unhedged': {
                'trades': [],
                'total_pnl': 0.0,
                'winning_trades': 0,
                'losing_trades': 0,
                'max_loss_per_trade': 0.0,
            },
            'hedged': {
                'trades': [],
                'total_pnl': 0.0,
                'winning_trades': 0,
                'losing_trades': 0,
                'max_loss_per_trade': 0.0,
                'hedge_cost': 0.0,
                'hedge_benefit': 0.0,
            },
            'improvement': {
                'pnl_diff': 0.0,
                'max_loss_reduction': 0.0,
                'hedge_roi': 0.0,
            }
        }
        
        return results
