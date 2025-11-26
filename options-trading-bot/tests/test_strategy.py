import pytest
from src.strategy import OptionsStrategy

class TestOptionsStrategy:
    
    def test_strategy_initialization(self):
        """Test strategy initialization"""
        strategy = OptionsStrategy(account_size=10000, max_risk_percent=0.10)
        
        assert strategy.account_size == 10000
        assert strategy.risk_manager is not None
    
    def test_insufficient_data(self):
        """Test signal generation with insufficient data"""
        strategy = OptionsStrategy()
        
        signal = strategy.generate_signal(prices=[100, 101], current_price=101)
        
        assert signal['signal'] == 'WAIT'
        assert 'reason' in signal
    
    def test_buy_signal_generation(self):
        """Test buy signal generation"""
        strategy = OptionsStrategy(account_size=10000)
        
        # Create strong downtrend (oversold)
        prices = list(range(100, 50, -2)) + [50] * 10
        current_price = 50
        
        signal = strategy.generate_signal(prices, current_price)
        
        # Should generate either BUY or HOLD based on RSI/BB
        assert signal['signal'] in ['BUY', 'HOLD', 'REJECT']
    
    def test_position_update_take_profit(self):
        """Test position update with take profit"""
        strategy = OptionsStrategy()
        
        position = {
            'id': 'pos_1',
            'direction': 'LONG',
            'stop_loss': 95,
            'take_profit': 110
        }
        strategy.open_positions.append(position)
        
        result = strategy.update_position('pos_1', current_price=115)
        
        assert result is not None
        assert result['action'] == 'CLOSE'
        assert result['reason'] == 'Take profit hit'
    
    def test_position_update_stop_loss(self):
        """Test position update with stop loss"""
        strategy = OptionsStrategy()
        
        position = {
            'id': 'pos_1',
            'direction': 'LONG',
            'stop_loss': 90,
            'take_profit': 110
        }
        strategy.open_positions.append(position)
        
        result = strategy.update_position('pos_1', current_price=85)
        
        assert result is not None
        assert result['action'] == 'CLOSE'
        assert result['reason'] == 'Stop loss hit'
