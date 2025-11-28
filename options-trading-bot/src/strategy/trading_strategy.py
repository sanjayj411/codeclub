"""
Trading strategy logic with RSI and MACD indicators
"""
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
from src.indicators.rsi import RSIIndicator
from src.indicators.macd import MACDIndicator
from src.core.logger import logger


@dataclass
class TradeSignal:
    """Represents a trading signal"""
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0-100
    price: float
    timestamp: datetime
    indicators: Dict  # RSI, MACD values that triggered signal
    reason: str


class TradingStrategy:
    """Combines RSI and MACD for trading signals with market condition filters"""
    
    def __init__(self,
                 rsi_period: int = 14,
                 rsi_oversold: float = 30,
                 rsi_overbought: float = 70,
                 macd_fast: int = 12,
                 macd_slow: int = 26,
                 macd_signal: int = 9,
                 min_drawdown_for_buy: float = 2.0):
        """
        Initialize trading strategy
        
        Args:
            rsi_period: RSI calculation period
            rsi_oversold: RSI oversold threshold
            rsi_overbought: RSI overbought threshold
            macd_fast, macd_slow, macd_signal: MACD periods
            min_drawdown_for_buy: Minimum % drawdown from recent high required for BUY signal (default 2%)
        """
        self.rsi = RSIIndicator(rsi_period)
        self.macd = MACDIndicator(macd_fast, macd_slow, macd_signal)
        
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.min_drawdown_for_buy = min_drawdown_for_buy
        
        # Track previous values for crossover detection
        self.prev_rsi = None
        self.prev_macd = None
        self.prev_signal = None
    
    def analyze(self, symbol: str, closes: List[float], current_price: float) -> TradeSignal:
        """
        Analyze price data and generate trading signal
        
        Args:
            symbol: Trading symbol
            closes: List of closing prices
            current_price: Current market price
            
        Returns:
            TradeSignal with action and confidence
        """
        if len(closes) < 30:
            return TradeSignal(
                symbol=symbol,
                action='HOLD',
                confidence=0,
                price=current_price,
                timestamp=datetime.now(),
                indicators={},
                reason='Insufficient data (need 30+ candles)'
            )
        
        # Calculate indicators
        rsi = self.rsi.calculate(closes)
        macd, signal, histogram = self.macd.calculate(closes)
        
        # Store for crossover detection
        curr_rsi = rsi
        curr_macd = macd
        curr_signal = signal
        
        # Determine signal
        action, confidence, reason = self._generate_signal(
            rsi, macd, signal, histogram,
            self.prev_rsi, self.prev_macd, self.prev_signal,
            closes
        )
        
        # Update previous values
        self.prev_rsi = curr_rsi
        self.prev_macd = curr_macd
        self.prev_signal = curr_signal
        
        return TradeSignal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            price=current_price,
            timestamp=datetime.now(),
            indicators={
                'rsi': rsi,
                'macd': macd,
                'signal': signal,
                'histogram': histogram
            },
            reason=reason
        )
    
    def _generate_signal(self,
                        rsi: Optional[float],
                        macd: Optional[float],
                        signal: Optional[float],
                        histogram: Optional[float],
                        prev_rsi: Optional[float],
                        prev_macd: Optional[float],
                        prev_signal: Optional[float],
                        closes: Optional[List[float]] = None) -> tuple:
        """
        Generate trading signal based on indicators
        
        Args:
            closes: Optional list of closing prices for drawdown analysis
        
        Returns:
            Tuple of (action, confidence, reason)
        """
        action = 'HOLD'
        confidence = 0.0
        reasons = []
        signal_count = 0
        buy_signals = 0
        sell_signals = 0
        
        # Check if current price is down 2%+ from recent high (for BUY filter)
        is_drawdown_met = True  # Default true if no price data
        if closes and len(closes) >= 2:
            recent_high = max(closes[-20:]) if len(closes) >= 20 else max(closes)
            current_price = closes[-1]
            drawdown_pct = ((recent_high - current_price) / recent_high) * 100
            is_drawdown_met = drawdown_pct >= self.min_drawdown_for_buy
        
        # RSI Analysis
        if rsi is not None:
            if rsi < self.rsi_oversold:
                # Only count as BUY if drawdown condition is met
                if is_drawdown_met:
                    buy_signals += 1
                    signal_count += 1
                    reasons.append(f"RSI oversold ({rsi:.1f})")
                else:
                    reasons.append(f"RSI oversold ({rsi:.1f}) but price not down 2%")
            elif rsi > self.rsi_overbought:
                sell_signals += 1
                signal_count += 1
                reasons.append(f"RSI overbought ({rsi:.1f})")
        
        # MACD Analysis
        if (macd is not None and signal is not None and 
            prev_macd is not None and prev_signal is not None):
            
            if self.macd.is_bullish_crossover(prev_macd, macd, prev_signal, signal):
                # Only count as BUY if drawdown condition is met
                if is_drawdown_met:
                    buy_signals += 1
                    signal_count += 1
                    reasons.append("MACD bullish crossover")
                else:
                    reasons.append("MACD bullish crossover but price not down 2%")
            elif self.macd.is_bearish_crossover(prev_macd, macd, prev_signal, signal):
                sell_signals += 1
                signal_count += 1
                reasons.append("MACD bearish crossover")
            
            # Additional MACD trend confirmation
            if histogram is not None:
                if histogram > 0 and macd > signal:
                    if is_drawdown_met:
                        buy_signals += 0.5
                        signal_count += 0.5
                elif histogram < 0 and macd < signal:
                    sell_signals += 0.5
                    signal_count += 0.5
        
        # Determine action and confidence
        if signal_count == 0:
            reason = "No clear signals" if is_drawdown_met else "No signals (price not down 2%)"
        elif buy_signals > sell_signals:
            action = 'BUY'
            confidence = min(100, (buy_signals / signal_count) * 100)
            reason = "; ".join(reasons) if reasons else "RSI/MACD buy signals"
        elif sell_signals > buy_signals:
            action = 'SELL'
            confidence = min(100, (sell_signals / signal_count) * 100)
            reason = "; ".join(reasons) if reasons else "RSI/MACD sell signals"
        else:
            reason = "; ".join(reasons) if reasons else "Mixed signals"
        
        return action, confidence, reason
    
    def reset(self):
        """Reset strategy state for new symbol"""
        self.rsi.reset()
        self.macd.reset()
        self.prev_rsi = None
        self.prev_macd = None
        self.prev_signal = None
