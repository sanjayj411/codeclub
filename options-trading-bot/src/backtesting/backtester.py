"""
Backtesting framework for trading strategies
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from enum import Enum
import json

from src.strategy.trading_strategy import TradingStrategy, TradeSignal
from src.core.logger import logger


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


@dataclass
class BacktestOrder:
    """Represents an order in backtest"""
    symbol: str
    action: str  # BUY or SELL
    quantity: float
    price: float
    timestamp: datetime
    status: OrderStatus = OrderStatus.FILLED
    order_id: str = ""


@dataclass
class Position:
    """Represents an open position"""
    symbol: str
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    
    @property
    def value(self) -> float:
        """Current position value"""
        return self.quantity * self.current_price
    
    @property
    def entry_value(self) -> float:
        """Initial position value"""
        return self.quantity * self.entry_price
    
    @property
    def pnl(self) -> float:
        """Unrealized P&L"""
        return self.value - self.entry_value
    
    @property
    def pnl_pct(self) -> float:
        """Unrealized P&L percentage"""
        if self.entry_value == 0:
            return 0.0
        return (self.pnl / abs(self.entry_value)) * 100


@dataclass
class Trade:
    """Represents a completed trade"""
    symbol: str
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: datetime
    exit_time: datetime
    pnl: float = 0.0
    pnl_pct: float = 0.0
    
    def __post_init__(self):
        if self.pnl == 0.0:
            self.pnl = (self.exit_price - self.entry_price) * self.quantity
            if self.entry_price != 0:
                self.pnl_pct = ((self.exit_price - self.entry_price) / self.entry_price) * 100


@dataclass
class BacktestStats:
    """Statistics from backtest run"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    trades: List[Trade] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)


class Backtester:
    """Backtesting engine for trading strategies"""
    
    def __init__(self, strategy: TradingStrategy, initial_capital: float = 10000.0):
        """
        Initialize backtester
        
        Args:
            strategy: TradingStrategy instance to backtest
            initial_capital: Starting capital in dollars
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.capital = initial_capital
        
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.orders: List[BacktestOrder] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
    
    def run(self, price_data: Dict[str, List[Dict]]) -> BacktestStats:
        """
        Run backtest on historical price data
        
        Args:
            price_data: Dict with symbol -> list of OHLCV candles
                Each candle: {'timestamp': datetime, 'open', 'high', 'low', 'close', 'volume'}
                
        Returns:
            BacktestStats with test results
        """
        logger.info(f"Starting backtest with ${self.initial_capital:.2f} capital")
        
        # Reset state
        self.positions = {}
        self.trades = []
        self.orders = []
        self.equity_curve = []
        self.capital = self.initial_capital
        
        # Get all timestamps across all symbols and sort them
        all_timestamps = set()
        for symbol, candles in price_data.items():
            for candle in candles:
                all_timestamps.add(candle['timestamp'])
        
        timestamps = sorted(all_timestamps)
        
        # Process each timestamp
        for timestamp in timestamps:
            # Get current prices for all positions
            current_prices = {}
            closes_by_symbol = {symbol: [] for symbol in price_data.keys()}
            
            for symbol, candles in price_data.items():
                candles_up_to = [c for c in candles if c['timestamp'] <= timestamp]
                if candles_up_to:
                    current_prices[symbol] = candles_up_to[-1]['close']
                    closes_by_symbol[symbol] = [c['close'] for c in candles_up_to]
            
            # Update position values
            portfolio_value = self.capital
            for symbol, position in self.positions.items():
                if symbol in current_prices:
                    position.current_price = current_prices[symbol]
                    portfolio_value += position.value
            
            # Record equity
            self.equity_curve.append((timestamp, portfolio_value))
            
            # Analyze each symbol for trading signals
            for symbol, closes in closes_by_symbol.items():
                if not closes or len(closes) < 30:
                    continue
                
                if symbol in current_prices:
                    current_price = current_prices[symbol]
                    
                    # Get trading signal
                    signal = self.strategy.analyze(symbol, closes, current_price)
                    
                    # Execute trades based on signal
                    self._execute_signal(signal, timestamp)
        
        # Close all remaining positions
        final_timestamp = timestamps[-1] if timestamps else datetime.now()
        for symbol in list(self.positions.keys()):
            if symbol in current_prices:
                self._close_position(symbol, current_prices[symbol], final_timestamp)
        
        # Calculate statistics
        stats = self._calculate_stats()
        logger.info(f"Backtest completed: {stats.total_trades} trades, "
                   f"${stats.total_pnl:.2f} P&L, {stats.win_rate:.1f}% win rate")
        
        return stats
    
    def _execute_signal(self, signal: TradeSignal, timestamp: datetime):
        """Execute a trading signal"""
        symbol = signal.symbol
        
        if signal.action == 'BUY':
            self._open_position(symbol, signal.price, timestamp)
        elif signal.action == 'SELL' and symbol in self.positions:
            self._close_position(symbol, signal.price, timestamp)
    
    def _open_position(self, symbol: str, price: float, timestamp: datetime):
        """Open a new position"""
        if symbol in self.positions:
            return  # Already have position
        
        if self.capital <= 0:
            return  # No capital
        
        # Use 50% of capital for each position (conservative)
        position_capital = self.capital * 0.5
        quantity = position_capital / price
        
        self.capital -= position_capital
        
        position = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            entry_time=timestamp,
            current_price=price
        )
        
        self.positions[symbol] = position
        
        order = BacktestOrder(
            symbol=symbol,
            action='BUY',
            quantity=quantity,
            price=price,
            timestamp=timestamp
        )
        self.orders.append(order)
        
        logger.debug(f"BUY {quantity:.4f} {symbol} @ ${price:.2f}")
    
    def _close_position(self, symbol: str, price: float, timestamp: datetime):
        """Close an open position"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Record completed trade
        trade = Trade(
            symbol=symbol,
            entry_price=position.entry_price,
            exit_price=price,
            quantity=position.quantity,
            entry_time=position.entry_time,
            exit_time=timestamp
        )
        self.trades.append(trade)
        
        # Update capital
        self.capital += price * position.quantity
        
        order = BacktestOrder(
            symbol=symbol,
            action='SELL',
            quantity=position.quantity,
            price=price,
            timestamp=timestamp
        )
        self.orders.append(order)
        
        logger.debug(f"SELL {position.quantity:.4f} {symbol} @ ${price:.2f}, "
                    f"P&L: ${trade.pnl:.2f} ({trade.pnl_pct:.2f}%)")
        
        # Remove position
        del self.positions[symbol]
    
    def _calculate_stats(self) -> BacktestStats:
        """Calculate backtest statistics"""
        stats = BacktestStats()
        stats.trades = self.trades
        stats.total_trades = len(self.trades)
        
        if stats.total_trades == 0:
            return stats
        
        # Calculate P&L
        total_win = 0.0
        total_loss = 0.0
        max_win = 0.0
        max_loss = 0.0
        
        for trade in self.trades:
            stats.total_pnl += trade.pnl
            
            if trade.pnl > 0:
                stats.winning_trades += 1
                total_win += trade.pnl
                max_win = max(max_win, trade.pnl)
            elif trade.pnl < 0:
                stats.losing_trades += 1
                total_loss += abs(trade.pnl)
                max_loss = max(max_loss, abs(trade.pnl))
        
        stats.total_pnl_pct = (stats.total_pnl / self.initial_capital) * 100
        stats.win_rate = (stats.winning_trades / stats.total_trades) * 100 if stats.total_trades > 0 else 0
        stats.avg_win = total_win / stats.winning_trades if stats.winning_trades > 0 else 0
        stats.avg_loss = total_loss / stats.losing_trades if stats.losing_trades > 0 else 0
        stats.profit_factor = total_win / total_loss if total_loss > 0 else (1 if total_win > 0 else 0)
        
        # Calculate max drawdown
        stats.max_drawdown, stats.max_drawdown_pct = self._calculate_max_drawdown()
        
        # Calculate Sharpe ratio
        stats.sharpe_ratio = self._calculate_sharpe_ratio()
        
        return stats
    
    def _calculate_max_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum drawdown"""
        if not self.equity_curve:
            return 0.0, 0.0
        
        max_equity = self.initial_capital
        max_drawdown = 0.0
        max_drawdown_pct = 0.0
        
        for timestamp, equity in self.equity_curve:
            if equity > max_equity:
                max_equity = equity
            
            drawdown = max_equity - equity
            drawdown_pct = (drawdown / max_equity) * 100 if max_equity > 0 else 0
            
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct
        
        return max_drawdown, max_drawdown_pct
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(self.trades) < 2:
            return 0.0
        
        returns = [trade.pnl_pct for trade in self.trades]
        
        if not returns:
            return 0.0
        
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0.0
        
        # Annualized Sharpe ratio (assuming 252 trading days)
        sharpe = ((avg_return / 100) - (risk_free_rate / 252)) / (std_dev / 100) * (252 ** 0.5)
        
        return sharpe
    
    def get_summary(self) -> str:
        """Get summary of backtest"""
        if not self.equity_curve:
            return "No backtest data"
        
        final_equity = self.equity_curve[-1][1]
        stats = self._calculate_stats()
        
        summary = f"""
        ====== BACKTEST SUMMARY ======
        Initial Capital: ${self.initial_capital:,.2f}
        Final Equity: ${final_equity:,.2f}
        
        Total Return: ${stats.total_pnl:,.2f} ({stats.total_pnl_pct:.2f}%)
        
        Total Trades: {stats.total_trades}
        Winning Trades: {stats.winning_trades}
        Losing Trades: {stats.losing_trades}
        Win Rate: {stats.win_rate:.1f}%
        
        Avg Win: ${stats.avg_win:.2f}
        Avg Loss: ${stats.avg_loss:.2f}
        Profit Factor: {stats.profit_factor:.2f}
        
        Max Drawdown: ${stats.max_drawdown:,.2f} ({stats.max_drawdown_pct:.2f}%)
        Sharpe Ratio: {stats.sharpe_ratio:.2f}
        ==============================
        """
        return summary
