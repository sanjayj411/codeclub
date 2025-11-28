"""
Bollinger Bands indicator calculation
"""
import numpy as np
from typing import List, Optional, Dict


class BollingerBandsIndicator:
    """Calculates Bollinger Bands"""
    
    def __init__(self, period: int = 20, std_dev_multiplier: float = 2.0):
        """
        Initialize Bollinger Bands indicator
        
        Args:
            period: Period for SMA (default 20)
            std_dev_multiplier: Standard deviation multiplier (default 2.0)
        """
        self.period = period
        self.std_dev_multiplier = std_dev_multiplier
    
    def calculate(self, closes: List[float]) -> Optional[Dict[str, float]]:
        """
        Calculate Bollinger Bands
        
        Args:
            closes: List of closing prices
            
        Returns:
            Dictionary with upper, middle, lower bands, width, and %B
            or None if insufficient data
        """
        if len(closes) < self.period:
            return None
        
        closes_array = np.array(closes[-self.period:])
        
        # Calculate middle band (SMA)
        middle_band = np.mean(closes_array)
        
        # Calculate standard deviation
        std_dev = np.std(closes_array)
        
        # Calculate bands
        upper_band = middle_band + (self.std_dev_multiplier * std_dev)
        lower_band = middle_band - (self.std_dev_multiplier * std_dev)
        
        # Calculate band width (useful for volatility assessment)
        band_width = upper_band - lower_band
        
        # Calculate %B (Bollinger Band % B) - where price sits relative to bands
        # %B = (price - lower) / (upper - lower)
        current_price = closes_array[-1]
        percent_b = (current_price - lower_band) / band_width if band_width > 0 else 0.5
        
        return {
            'upper': float(upper_band),
            'middle': float(middle_band),
            'lower': float(lower_band),
            'width': float(band_width),
            'percent_b': float(percent_b),  # 0 = at lower band, 1 = at upper band, 0.5 = middle
            'std_dev': float(std_dev)
        }
    
    def is_price_at_lower_band(self, closes: List[float], threshold: float = 0.05) -> bool:
        """
        Check if price is near lower Bollinger Band
        
        Args:
            closes: List of closing prices
            threshold: How close to lower band (0.05 = 5%)
            
        Returns:
            True if price is within threshold of lower band
        """
        bb = self.calculate(closes)
        if not bb:
            return False
        
        current_price = closes[-1]
        distance_to_lower = current_price - bb['lower']
        distance_pct = distance_to_lower / bb['width'] if bb['width'] > 0 else 0
        
        return distance_pct <= threshold
    
    def is_price_at_upper_band(self, closes: List[float], threshold: float = 0.05) -> bool:
        """
        Check if price is near upper Bollinger Band
        
        Args:
            closes: List of closing prices
            threshold: How close to upper band (0.05 = 5%)
            
        Returns:
            True if price is within threshold of upper band
        """
        bb = self.calculate(closes)
        if not bb:
            return False
        
        current_price = closes[-1]
        distance_to_upper = bb['upper'] - current_price
        distance_pct = distance_to_upper / bb['width'] if bb['width'] > 0 else 0
        
        return distance_pct <= threshold
    
    def has_squeeze(self, closes: List[float], squeeze_threshold: float = 0.10) -> bool:
        """
        Detect Bollinger Band Squeeze (low volatility, breakout coming)
        
        Args:
            closes: List of closing prices
            squeeze_threshold: Percentage threshold for squeeze
            
        Returns:
            True if bands are squeezed (width < threshold)
        """
        bb = self.calculate(closes)
        if not bb:
            return False
        
        # Check if band width is below threshold
        middle = bb['middle']
        width_pct = (bb['width'] / middle) * 100 if middle > 0 else 100
        
        return width_pct < squeeze_threshold
    
    def get_band_position(self, closes: List[float]) -> str:
        """
        Get descriptive position of price relative to bands
        
        Returns:
            'upper', 'middle', or 'lower'
        """
        bb = self.calculate(closes)
        if not bb:
            return 'unknown'
        
        current_price = closes[-1]
        
        if bb['percent_b'] > 0.75:
            return 'upper'
        elif bb['percent_b'] < 0.25:
            return 'lower'
        else:
            return 'middle'


def calculate_bollinger_bands_simple(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> Optional[Dict[str, float]]:
    """
    Simple function to calculate Bollinger Bands without class
    
    Args:
        prices: List of prices
        period: SMA period
        std_dev: Standard deviation multiplier
        
    Returns:
        Dictionary with band values
    """
    if len(prices) < period:
        return None
    
    prices_array = np.array(prices[-period:])
    mean = np.mean(prices_array)
    std = np.std(prices_array)
    
    return {
        'upper': float(mean + std_dev * std),
        'middle': float(mean),
        'lower': float(mean - std_dev * std),
        'width': float(2 * std_dev * std),
        'percent_b': float((prices[-1] - (mean - std_dev * std)) / (2 * std_dev * std)) if std > 0 else 0.5
    }
