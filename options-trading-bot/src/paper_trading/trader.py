"""
Paper trading module for simulated live trading
Executes trades in real-time without risking capital
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from datetime import datetime
from enum import Enum
import uuid

from src.strategy.trading_strategy import TradingStrategy, TradeSignal
from src.core.logger import logger


class PaperOrderStatus(Enum):
    """Paper order status"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class PaperOrder:
    """Simulated order"""
    symbol: str
    action: str  # BUY or SELL
    quantity: float
    price: float
    timestamp: datetime
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: PaperOrderStatus = PaperOrderStatus.PENDING
    filled_price: float = 0.0
    filled_time: Optional[datetime] = None
    commission: float = 0.0  # Broker commission
    slippage: float = 0.0  # Price slippage


@dataclass
class PaperPosition:
    """Paper trading position"""
    symbol: str
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    position_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    @property
    def value(self) -> float:
        """Current value"""
        return self.quantity * self.current_price
    
    @property
    def entry_value(self) -> float:
        """Entry value"""
        return self.quantity * self.entry_price
    
    @property
    def pnl(self) -> float:
        """Unrealized P&L"""
        return self.value - self.entry_value
    
    @property
    def pnl_pct(self) -> float:
        """Unrealized P&L %"""
        if self.entry_value == 0:
            return 0.0
        return (self.pnl / self.entry_value) * 100


@dataclass
class DailyStats:
    """Daily performance statistics"""
    date: datetime
    starting_equity: float = 0.0
    ending_equity: float = 0.0
    daily_return: float = 0.0
    daily_return_pct: float = 0.0
    trades_executed: int = 0
    winners: int = 0
    losers: int = 0
    largest_win: float = 0.0
    largest_loss: float = 0.0


class PaperTrader:
    """Paper trading simulator"""
    
    def __init__(
        self,
        strategy: TradingStrategy,
        initial_capital: float = 10000.0,
        commission_percent: float = 0.1,
        slippage_percent: float = 0.05
    ):
        """
        Initialize paper trader
        
        Args:
            strategy: TradingStrategy to use
            initial_capital: Starting capital in dollars
            commission_percent: Commission as % of trade value
            slippage_percent: Expected slippage as % of price
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.commission_percent = commission_percent
        self.slippage_percent = slippage_percent
        
        # Trading state
        self.positions: Dict[str, PaperPosition] = {}
        self.orders: List[PaperOrder] = []
        self.closed_trades: List[Dict] = []
        self.daily_stats: List[DailyStats] = []
        
        # Callbacks for notifications
        self.on_order_placed: Optional[Callable] = None
        self.on_order_filled: Optional[Callable] = None
        self.on_position_opened: Optional[Callable] = None
        self.on_position_closed: Optional[Callable] = None
    
    def analyze_and_trade(self, symbol: str, closes: List[float], current_price: float):
        """Analyze signal and execute trade if warranted"""
        if len(closes) < 30:
            return
        
        # Get trading signal
        signal = self.strategy.analyze(symbol, closes, current_price)
        
        # Execute trades
        if signal.action == 'BUY' and symbol not in self.positions:
            self.open_position(symbol, current_price, signal.timestamp)
        
        elif signal.action == 'SELL' and symbol in self.positions:
            self.close_position(symbol, current_price, signal.timestamp)
    
    def open_position(self, symbol: str, price: float, timestamp: datetime):
        """Open a new position"""
        if symbol in self.positions:
            logger.warning(f"Position already exists for {symbol}")
            return
        
        if self.capital <= 0:
            logger.warning(f"Insufficient capital to open {symbol}")
            return
        
        # Use 20% of capital per position (conservative)
        position_capital = self.capital * 0.20
        quantity = position_capital / price
        
        # Calculate costs
        commission = (price * quantity) * (self.commission_percent / 100)
        slippage = (price * quantity) * (self.slippage_percent / 100)
        total_cost = price * quantity + commission + slippage
        
        if total_cost > self.capital:
            logger.warning(f"Insufficient capital for {symbol} position")
            return
        
        # Deduct from capital
        self.capital -= total_cost
        
        # Create position
        position = PaperPosition(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            entry_time=timestamp,
            current_price=price
        )
        self.positions[symbol] = position
        
        # Create order
        order = PaperOrder(
            symbol=symbol,
            action='BUY',
            quantity=quantity,
            price=price,
            timestamp=timestamp,
            status=PaperOrderStatus.FILLED,
            filled_price=price + (price * self.slippage_percent / 100),
            filled_time=timestamp,
            commission=commission,
            slippage=slippage
        )
        self.orders.append(order)
        
        logger.info(f"PAPER: BUY {quantity:.4f} {symbol} @ ${price:.2f} "
                   f"(cost: ${total_cost:.2f})")
        
        if self.on_position_opened:
            self.on_position_opened({
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'timestamp': timestamp
            })
    
    def close_position(self, symbol: str, price: float, timestamp: datetime):
        """Close a position"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Calculate costs
        commission = (price * position.quantity) * (self.commission_percent / 100)
        slippage = (price * position.quantity) * (self.slippage_percent / 100)
        
        # Calculate P&L
        proceeds = (price * position.quantity) - commission - slippage
        pnl = proceeds - position.entry_value
        pnl_pct = (pnl / position.entry_value) * 100 if position.entry_value > 0 else 0
        
        # Add proceeds back to capital
        self.capital += proceeds
        
        # Create order
        order = PaperOrder(
            symbol=symbol,
            action='SELL',
            quantity=position.quantity,
            price=price,
            timestamp=timestamp,
            status=PaperOrderStatus.FILLED,
            filled_price=price - (price * self.slippage_percent / 100),
            filled_time=timestamp,
            commission=commission,
            slippage=slippage
        )
        self.orders.append(order)
        
        # Record closed trade
        self.closed_trades.append({
            'symbol': symbol,
            'entry_price': position.entry_price,
            'exit_price': price,
            'quantity': position.quantity,
            'entry_time': position.entry_time,
            'exit_time': timestamp,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'position_id': position.position_id
        })
        
        logger.info(f"PAPER: SELL {position.quantity:.4f} {symbol} @ ${price:.2f} "
                   f"P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")
        
        if self.on_position_closed:
            self.on_position_closed({
                'symbol': symbol,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'timestamp': timestamp
            })
        
        # Remove position
        del self.positions[symbol]
    
    def update_positions(self, price_data: Dict[str, float]):
        """Update position prices and check unrealized P&L"""
        total_portfolio_value = self.capital
        
        for symbol, position in self.positions.items():
            if symbol in price_data:
                position.current_price = price_data[symbol]
                total_portfolio_value += position.value
        
        return total_portfolio_value
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        total_value = self.capital
        total_unrealized_pnl = 0.0
        
        for position in self.positions.values():
            total_value += position.value
            total_unrealized_pnl += position.pnl
        
        # Calculate realized P&L
        total_realized_pnl = sum(t['pnl'] for t in self.closed_trades)
        
        return {
            'capital': self.capital,
            'positions': len(self.positions),
            'total_equity': total_value,
            'unrealized_pnl': total_unrealized_pnl,
            'realized_pnl': total_realized_pnl,
            'total_return_pct': ((total_value - self.initial_capital) / self.initial_capital * 100),
            'trades_executed': len(self.closed_trades),
            'winning_trades': sum(1 for t in self.closed_trades if t['pnl'] > 0),
            'losing_trades': sum(1 for t in self.closed_trades if t['pnl'] < 0),
            'win_rate': (sum(1 for t in self.closed_trades if t['pnl'] > 0) / len(self.closed_trades) * 100
                        if self.closed_trades else 0)
        }
    
    def get_position_summary(self, symbol: str) -> Optional[Dict]:
        """Get summary for a specific position"""
        if symbol not in self.positions:
            return None
        
        pos = self.positions[symbol]
        return {
            'symbol': symbol,
            'quantity': pos.quantity,
            'entry_price': pos.entry_price,
            'current_price': pos.current_price,
            'entry_value': pos.entry_value,
            'current_value': pos.value,
            'unrealized_pnl': pos.pnl,
            'unrealized_pnl_pct': pos.pnl_pct,
            'entry_time': pos.entry_time,
            'position_id': pos.position_id
        }
    
    def print_summary(self):
        """Print paper trading summary"""
        summary = self.get_portfolio_summary()
        
        print(f"""
        ====== PAPER TRADING SUMMARY ======
        Initial Capital: ${self.initial_capital:,.2f}
        Current Equity: ${summary['total_equity']:,.2f}
        Available Capital: ${summary['capital']:,.2f}
        
        Total Return: ${summary['total_equity'] - self.initial_capital:,.2f} ({summary['total_return_pct']:.2f}%)
        
        Unrealized P&L: ${summary['unrealized_pnl']:,.2f}
        Realized P&L: ${summary['realized_pnl']:,.2f}
        
        Open Positions: {summary['positions']}
        
        Trades Executed: {summary['trades_executed']}
        Winning Trades: {summary['winning_trades']}
        Losing Trades: {summary['losing_trades']}
        Win Rate: {summary['win_rate']:.1f}%
        ===================================
        """)
    
    def export_trades(self, filename: str = 'paper_trades.json'):
        """Export trades to JSON file"""
        import json
        
        trades = []
        for trade in self.closed_trades:
            trade_copy = trade.copy()
            trade_copy['entry_time'] = str(trade_copy['entry_time'])
            trade_copy['exit_time'] = str(trade_copy['exit_time'])
            trades.append(trade_copy)
        
        with open(filename, 'w') as f:
            json.dump(trades, f, indent=2)
        
        logger.info(f"Exported {len(trades)} trades to {filename}")
