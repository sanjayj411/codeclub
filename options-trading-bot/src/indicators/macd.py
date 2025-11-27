"""
MACD (Moving Average Convergence Divergence) indicator calculation
"""
import numpy as np
from typing import List, Optional, Tuple, Dict


class MACDIndicator:
    """Calculates MACD using exponential moving averages"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        Initialize MACD indicator
        
        Args:
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line EMA period (default 9)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        self.fast_ema = None
        self.slow_ema = None
        self.signal_ema = None
    
    def _calculate_ema(self, values: List[float], period: int) -> List[float]:
        """Calculate exponential moving average"""
        ema_values = []
        multiplier = 2.0 / (period + 1)
        
        # First EMA is SMA
        if len(values) >= period:
            ema = np.mean(values[:period])
        else:
            return []
        
        ema_values.append(ema)
        
        # Calculate subsequent EMAs
        for i in range(period, len(values)):
            ema = values[i] * multiplier + ema * (1 - multiplier)
            ema_values.append(ema)
        
        return ema_values
    
    def calculate(self, closes: List[float]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Calculate MACD line, signal line, and histogram
        
        Args:
            closes: List of closing prices
            
        Returns:
            Tuple of (MACD, Signal, Histogram) or (None, None, None) if insufficient data
        """
        if len(closes) < self.slow_period:
            return None, None, None
        
        # Calculate fast and slow EMAs
        fast_ema_values = self._calculate_ema(closes, self.fast_period)
        slow_ema_values = self._calculate_ema(closes, self.slow_period)
        
        if not fast_ema_values or not slow_ema_values:
            return None, None, None
        
        # MACD line = fast EMA - slow EMA (use aligned values)
        # We need to align them properly - both start from slow_period position
        start_idx = self.slow_period - self.fast_period
        macd_line = fast_ema_values[start_idx] - slow_ema_values[0]
        
        # Calculate signal line (EMA of MACD line)
        # For this simplified calculation, we need to build the MACD line series first
        macd_values = []
        for i in range(len(slow_ema_values)):
            macd_values.append(fast_ema_values[start_idx + i] - slow_ema_values[i])
        
        signal_values = self._calculate_ema(macd_values, self.signal_period)
        
        if not signal_values:
            return macd_line, None, None
        
        signal_line = signal_values[-1]
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def calculate_bulk(self, closes: List[float]) -> Dict[str, List]:
        """
        Calculate MACD for entire series (for backtesting)
        
        Args:
            closes: List of closing prices
            
        Returns:
            Dict with keys: macd, signal, histogram
        """
        result = {
            'macd': [],
            'signal': [],
            'histogram': []
        }
        
        if len(closes) < self.slow_period:
            return result
        
        # Calculate EMAs
        fast_ema_values = self._calculate_ema(closes, self.fast_period)
        slow_ema_values = self._calculate_ema(closes, self.slow_period)
        
        # Build MACD line
        start_idx = self.slow_period - self.fast_period
        macd_values = []
        
        for i in range(len(slow_ema_values)):
            macd_values.append(fast_ema_values[start_idx + i] - slow_ema_values[i])
        
        # Calculate signal line
        signal_values = self._calculate_ema(macd_values, self.signal_period)
        
        # Build output
        for i in range(len(closes)):
            if i < self.slow_period - 1:
                result['macd'].append(None)
                result['signal'].append(None)
                result['histogram'].append(None)
            else:
                macd_idx = i - (self.slow_period - 1)
                if macd_idx < len(macd_values):
                    result['macd'].append(macd_values[macd_idx])
                    
                    signal_idx = macd_idx - (self.signal_period - 1)
                    if signal_idx < len(signal_values):
                        signal = signal_values[signal_idx]
                        result['signal'].append(signal)
                        result['histogram'].append(macd_values[macd_idx] - signal)
                    else:
                        result['signal'].append(None)
                        result['histogram'].append(None)
                else:
                    result['macd'].append(None)
                    result['signal'].append(None)
                    result['histogram'].append(None)
        
        return result
    
    def is_bullish_crossover(self, prev_macd: Optional[float], curr_macd: Optional[float],
                            prev_signal: Optional[float], curr_signal: Optional[float]) -> bool:
        """Check if MACD just crossed above signal line (bullish)"""
        if any(v is None for v in [prev_macd, curr_macd, prev_signal, curr_signal]):
            return False
        return prev_macd < prev_signal and curr_macd > curr_signal
    
    def is_bearish_crossover(self, prev_macd: Optional[float], curr_macd: Optional[float],
                            prev_signal: Optional[float], curr_signal: Optional[float]) -> bool:
        """Check if MACD just crossed below signal line (bearish)"""
        if any(v is None for v in [prev_macd, curr_macd, prev_signal, curr_signal]):
            return False
        return prev_macd > prev_signal and curr_macd < curr_signal
    
    def reset(self):
        """Reset internal state"""
        self.fast_ema = None
        self.slow_ema = None
        self.signal_ema = None
