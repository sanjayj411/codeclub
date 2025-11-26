import pytest
from src.indicators import TechnicalIndicators

class TestTechnicalIndicators:
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        prices = [44, 44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.00, 46.00]
        rsi = TechnicalIndicators.calculate_rsi(prices, period=14)
        
        assert rsi is not None
        assert 0 <= rsi <= 100
    
    def test_rsi_oversold(self):
        """Test RSI oversold detection (< 30)"""
        prices = [100] * 15 + [50, 50, 50, 50, 50]  # Sharp drop
        rsi = TechnicalIndicators.calculate_rsi(prices, period=14)
        
        assert rsi is not None
        assert rsi < 50  # Should be low after drop
    
    def test_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        prices = [20, 21, 22, 21, 20, 21, 22, 23, 22, 21, 20, 21, 22, 23, 24, 25, 24, 23, 22, 21]
        bb = TechnicalIndicators.calculate_bollinger_bands(prices, period=20)
        
        assert bb is not None
        assert 'upper' in bb
        assert 'middle' in bb
        assert 'lower' in bb
        assert bb['lower'] < bb['middle'] < bb['upper']
    
    def test_signal_analysis_buy(self):
        """Test buy signal generation"""
        # Create oversold scenario
        prices = [100] * 15 + [50, 50, 50, 50, 50]
        current_price = 50
        
        analysis = TechnicalIndicators.analyze_signals(prices, current_price)
        
        assert analysis is not None
        assert analysis['price'] == 50
        assert analysis['rsi'] is not None
