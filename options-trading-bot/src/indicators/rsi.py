"""
RSI (Relative Strength Index) indicator calculation
"""
import numpy as np
from typing import List, Optional


class RSIIndicator:
    """Calculates RSI using Wilder's smoothing method"""
    
    def __init__(self, period: int = 14):
        """
        Initialize RSI indicator
        
        Args:
            period: RSI period (default 14)
        """
        self.period = period
        self.gains = []
        self.losses = []
        self.avg_gain = None
        self.avg_loss = None
    
    def calculate(self, closes: List[float], period: Optional[int] = None) -> Optional[float]:
        """
        Calculate RSI for a series of closes
        
        Args:
            closes: List of closing prices
            period: Override period if needed
            
        Returns:
            RSI value (0-100) or None if insufficient data
        """
        if period:
            self.period = period
            
        if len(closes) < self.period + 1:
            return None
        
        # Calculate price changes
        deltas = np.diff(closes[-self.period-1:])
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate initial average gain and loss (Wilder's method)
        if self.avg_gain is None:
            self.avg_gain = np.mean(gains)
            self.avg_loss = np.mean(losses)
        else:
            # Smooth using Wilder's method
            self.avg_gain = (self.avg_gain * (self.period - 1) + gains[-1]) / self.period
            self.avg_loss = (self.avg_loss * (self.period - 1) + losses[-1]) / self.period
        
        # Calculate RS and RSI
        if self.avg_loss == 0:
            return 100.0 if self.avg_gain > 0 else 50.0
        
        rs = self.avg_gain / self.avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_bulk(self, closes: List[float]) -> List[Optional[float]]:
        """
        Calculate RSI for entire series (for backtesting)
        
        Args:
            closes: List of closing prices
            
        Returns:
            List of RSI values
        """
        rsi_values = []
        deltas = np.diff(closes)
        
        for i in range(len(closes)):
            if i < self.period:
                rsi_values.append(None)
                continue
            
            period_deltas = deltas[i-self.period:i]
            gains = np.where(period_deltas > 0, period_deltas, 0)
            losses = np.where(period_deltas < 0, -period_deltas, 0)
            
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            
            if avg_loss == 0:
                rsi_values.append(100.0 if avg_gain > 0 else 50.0)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
        
        return rsi_values
    
    def is_oversold(self, rsi: Optional[float], threshold: float = 30) -> bool:
        """Check if RSI is in oversold territory"""
        return rsi is not None and rsi < threshold
    
    def is_overbought(self, rsi: Optional[float], threshold: float = 70) -> bool:
        """Check if RSI is in overbought territory"""
        return rsi is not None and rsi > threshold
    
    def reset(self):
        """Reset internal state for new symbol"""
        self.gains = []
        self.losses = []
        self.avg_gain = None
        self.avg_loss = None
