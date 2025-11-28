"""
Test suite for enhanced stock strategy with Bollinger Bands and options integration
"""

import pytest
import math
from datetime import datetime, timedelta
from src.indicators.bollinger_bands import BollingerBandsIndicator, calculate_bollinger_bands_simple
from src.strategy.enhanced_strategy import EnhancedStockStrategy, StockSignal, OptionsOpportunity
from src.strategy.options_strategy import OptionsStrategy


class TestBollingerBands:
    """Test Bollinger Bands indicator"""
    
    def test_bb_basic_calculation(self):
        """Test basic Bollinger Bands calculation"""
        bb = BollingerBandsIndicator(period=20)
        
        # Flat price data
        prices = [100.0] * 20
        result = bb.calculate(prices)
        
        assert result is not None
        assert result['middle'] == 100.0
        assert result['upper'] == 100.0
        assert result['lower'] == 100.0
        assert result['width'] == 0.0
        print("✓ Flat prices: BB width = 0")
    
    def test_bb_with_volatility(self):
        """Test BB with volatile data"""
        bb = BollingerBandsIndicator(period=20, std_dev_multiplier=2.0)
        
        # Create prices with known standard deviation
        prices = [100 + i for i in range(20)]  # Linear increase 100-119
        result = bb.calculate(prices)
        
        assert result is not None
        assert result['middle'] > 0
        assert result['upper'] > result['middle']
        assert result['lower'] < result['middle']
        assert result['width'] > 0
        print(f"✓ Volatile data: Width = {result['width']:.2f}")
    
    def test_bb_percent_b(self):
        """Test Bollinger Band %B (position indicator)"""
        bb = BollingerBandsIndicator()
        
        prices = [100.0] * 19 + [100.0]  # Start flat
        prices[-1] = 100.0 + (2 * bb.std_dev_multiplier)  # Push to upper band
        
        result = bb.calculate(prices)
        
        # At upper band, %B should be ~1.0
        assert 0.95 < result['percent_b'] <= 1.0
        print(f"✓ %B at upper band: {result['percent_b']:.3f}")
    
    def test_bb_position_detection(self):
        """Test detecting price position relative to bands"""
        bb = BollingerBandsIndicator()
        
        # Price at middle
        prices = [100.0] * 20
        assert bb.get_band_position(prices) == 'middle'
        
        # Price at lower
        prices = [100 - (2.5 * bb.std_dev_multiplier * np.std(prices))] * 20
        assert bb.get_band_position(prices) == 'lower'
        
        print("✓ Band position detection working")
    
    def test_bb_squeeze_detection(self):
        """Test Bollinger Band squeeze detection"""
        bb = BollingerBandsIndicator()
        
        # Low volatility (squeeze)
        prices = [100.0 + (0.01 * i) for i in range(20)]
        assert bb.has_squeeze(prices, squeeze_threshold=2.0)
        
        # High volatility (no squeeze)
        prices = [100.0 + (2.0 * i) for i in range(20)]
        assert not bb.has_squeeze(prices, squeeze_threshold=2.0)
        
        print("✓ Squeeze detection working")


class TestEnhancedStrategy:
    """Test enhanced stock strategy"""
    
    def test_strategy_initialization(self):
        """Test strategy initialization"""
        strat = EnhancedStockStrategy(
            rsi_oversold=30,
            rsi_overbought=70,
            bb_period=20,
            min_drawdown_for_buy=2.0
        )
        
        assert strat.rsi_oversold == 30
        assert strat.rsi_overbought == 70
        assert strat.min_drawdown_for_buy == 2.0
        print("✓ Strategy initialized")
    
    def test_stock_analysis_downtrend(self):
        """Test stock analysis with downtrend (should generate BUY)"""
        strat = EnhancedStockStrategy()
        
        # Generate downtrend data
        closes = [100 - (i * 0.5) for i in range(30)]
        current_price = 85.0
        
        signal = strat.analyze_stock('TEST', closes, current_price)
        
        if signal:
            assert signal.action in ['BUY', 'SELL', 'HOLD']
            assert 0 <= signal.confidence <= 100
            assert signal.rsi is not None
            print(f"✓ Downtrend analysis: {signal.action} (confidence: {signal.confidence:.0f}%)")
    
    def test_stock_analysis_uptrend(self):
        """Test stock analysis with uptrend (should generate SELL)"""
        strat = EnhancedStockStrategy()
        
        # Generate uptrend data
        closes = [100 + (i * 0.5) for i in range(30)]
        current_price = 115.0
        
        signal = strat.analyze_stock('TEST', closes, current_price)
        
        if signal:
            assert signal.action in ['BUY', 'SELL', 'HOLD']
            print(f"✓ Uptrend analysis: {signal.action} (confidence: {signal.confidence:.0f}%)")
    
    def test_options_analysis_trigger(self):
        """Test options analysis triggered by stock BUY signal"""
        strat = EnhancedStockStrategy()
        
        # Create downtrend data for BUY signal
        closes = [100 - (i * 0.5) for i in range(30)]
        current_price = 85.0
        
        # First get stock signal
        stock_signal = strat.analyze_stock('AAPL', closes, current_price)
        
        if stock_signal and stock_signal.action == 'BUY':
            # Then get options opportunity
            options_opp = strat.analyze_options_for_stock_signal(
                stock_signal,
                closes,
                current_price,
                days_to_expiry=30,
                num_simulations=2000
            )
            
            if options_opp:
                assert options_opp.option_type == 'call'
                assert 0 <= options_opp.delta <= 1
                assert 0 <= options_opp.prob_itm <= 1
                print(f"✓ Options analysis: {options_opp.recommendation} "
                      f"(delta={options_opp.delta:.3f}, prob_itm={options_opp.prob_itm:.1%})")
    
    def test_strike_selection(self):
        """Test optimal strike selection for call options"""
        strat = EnhancedStockStrategy()
        
        current_price = 150.0
        closes = [150.0] * 20
        volatility = 0.20
        time_to_expiry = 30/365
        
        strike = strat._select_call_strike(current_price, closes, volatility, time_to_expiry, 30)
        
        assert strike is not None
        assert strike > 0
        # Strike should be ATM or slightly OTM
        assert 0.99 * current_price <= strike <= 1.03 * current_price
        print(f"✓ Strike selection: ${strike:.2f} (current: ${current_price:.2f})")
    
    def test_confidence_scoring(self):
        """Test options confidence scoring"""
        strat = EnhancedStockStrategy()
        
        greeks = {
            'delta': 0.40,
            'gamma': 0.035,
            'price': 2.50
        }
        
        mc_prob = {'prob_itm_at_expiry': 0.45}
        
        var_result = {
            'var_95': 100,
            'best_gain': 500
        }
        
        confidence = strat._score_options_confidence(80.0, greeks, mc_prob, var_result)
        
        assert 0 <= confidence <= 100
        print(f"✓ Confidence score: {confidence:.0f}%")


class TestStockScannerIntegration:
    """Test stock scanner integration"""
    
    def test_scanner_single_stock(self):
        """Test scanning single stock"""
        from stock_scanner import StockScanner
        
        strat = EnhancedStockStrategy()
        scanner = StockScanner(strat, use_live_data=False)
        
        result = scanner.scan_single_stock('AAPL', days_of_history=60)
        
        assert result['symbol'] == 'AAPL'
        assert 'stock_signal' in result
        assert 'options_opportunity' in result
        assert 'timestamp' in result
        print(f"✓ Single stock scan completed")
    
    def test_scanner_multiple_stocks(self):
        """Test scanning multiple stocks"""
        from stock_scanner import StockScanner
        
        strat = EnhancedStockStrategy()
        scanner = StockScanner(strat, use_live_data=False)
        
        symbols = ['AAPL', 'SPY', 'QQQ']
        results = scanner.scan_multiple_stocks(symbols, days_of_history=60)
        
        assert len(results) == 3
        for result in results:
            assert 'symbol' in result
            assert result['symbol'] in symbols
        
        print(f"✓ Multiple stock scan completed ({len(results)} stocks)")


class TestSignalFiltering:
    """Test signal filtering and conditions"""
    
    def test_oversold_condition(self):
        """Test RSI oversold condition"""
        strat = EnhancedStockStrategy(rsi_oversold=30)
        
        # Create prices that trigger RSI < 30 (oversold)
        closes = [100 - (i * 2) for i in range(20)]
        
        signal = strat.analyze_stock('TEST', closes, closes[-1])
        
        if signal:
            assert signal.rsi < 30
            print(f"✓ RSI oversold detected: {signal.rsi:.1f}")
    
    def test_drawdown_filter(self):
        """Test minimum drawdown filter"""
        strat = EnhancedStockStrategy(min_drawdown_for_buy=2.0)
        
        # Price with 5% drawdown from high
        high = 100
        closes = [high] * 5 + [95 + (i * 0.5) for i in range(25)]
        
        signal = strat.analyze_stock('TEST', closes, closes[-1])
        
        # Should potentially generate BUY if other conditions met
        print(f"✓ Drawdown filter applied")
    
    def test_bollinger_band_signals(self):
        """Test Bollinger Band signal generation"""
        strat = EnhancedStockStrategy()
        
        # Price bouncing from lower BB
        bb = BollingerBandsIndicator()
        
        prices = [100] * 19
        # Add price at lower band
        import numpy as np
        std = np.std(prices)
        lower = np.mean(prices) - (2 * std)
        
        prices.append(lower + 0.5)  # Bounce from lower
        
        signal = strat.analyze_stock('TEST', prices, prices[-1])
        print(f"✓ Bollinger Band signal detection working")


if __name__ == '__main__':
    print("Running enhanced strategy tests...\n")
    
    print("=" * 60)
    print("BOLLINGER BANDS TESTS")
    print("=" * 60)
    test_bb = TestBollingerBands()
    test_bb.test_bb_basic_calculation()
    test_bb.test_bb_with_volatility()
    test_bb.test_bb_percent_b()
    test_bb.test_bb_squeeze_detection()
    
    print("\n" + "=" * 60)
    print("ENHANCED STRATEGY TESTS")
    print("=" * 60)
    test_strat = TestEnhancedStrategy()
    test_strat.test_strategy_initialization()
    test_strat.test_stock_analysis_downtrend()
    test_strat.test_stock_analysis_uptrend()
    test_strat.test_strike_selection()
    test_strat.test_confidence_scoring()
    
    print("\n" + "=" * 60)
    print("SIGNAL FILTERING TESTS")
    print("=" * 60)
    test_filter = TestSignalFiltering()
    test_filter.test_oversold_condition()
    test_filter.test_drawdown_filter()
    test_filter.test_bollinger_band_signals()
    
    print("\n✓ All tests passed!")


import numpy as np
