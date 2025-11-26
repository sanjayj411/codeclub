import numpy as np
import pandas as pd
from typing import Dict, Tuple

class TechnicalIndicators:
    """Calculate RSI and Bollinger Bands indicators"""
    
    @staticmethod
    def calculate_rsi(prices: list, period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)
        RSI > 70: Overbought (Sell signal)
        RSI < 30: Oversold (Buy signal)
        """
        if len(prices) < period + 1:
            return None
        
        prices = np.array(prices[-period-1:])
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rs = up / down if down != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if down != 0 else 50
        
        return float(rsi)
    
    @staticmethod
    def calculate_bollinger_bands(prices: list, period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        """
        Calculate Bollinger Bands
        Returns: {
            'upper': upper band value,
            'middle': SMA (middle band),
            'lower': lower band value
        }
        """
        if len(prices) < period:
            return None
        
        prices = np.array(prices[-period:])
        sma = np.mean(prices)
        std = np.std(prices)
        
        return {
            'upper': float(sma + (std_dev * std)),
            'middle': float(sma),
            'lower': float(sma - (std_dev * std))
        }
    
    @staticmethod
    def analyze_signals(prices: list, current_price: float) -> Dict:
        """
        Analyze RSI and Bollinger Bands for trading signals
        Returns signal analysis data
        """
        rsi = TechnicalIndicators.calculate_rsi(prices)
        bb = TechnicalIndicators.calculate_bollinger_bands(prices)
        
        signals = {
            'rsi': rsi,
            'bollinger_bands': bb,
            'price': current_price,
            'buy_signal': False,
            'sell_signal': False,
            'signal_strength': 0.0
        }
        
        if rsi and bb:
            # Buy signals
            if rsi < 30 and current_price < bb['lower']:
                signals['buy_signal'] = True
                signals['signal_strength'] = (30 - rsi) / 30  # 0-1 strength
            elif rsi < 40 and current_price < bb['middle']:
                signals['buy_signal'] = True
                signals['signal_strength'] = (40 - rsi) / 40
            
            # Sell signals
            if rsi > 70 and current_price > bb['upper']:
                signals['sell_signal'] = True
                signals['signal_strength'] = (rsi - 70) / 30  # 0-1 strength
            elif rsi > 60 and current_price > bb['middle']:
                signals['sell_signal'] = True
                signals['signal_strength'] = (rsi - 60) / 40
        
        return signals
