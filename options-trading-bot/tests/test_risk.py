import pytest
from src.risk import RiskManager

class TestRiskManager:
    
    def test_position_size_calculation(self):
        """Test position sizing with 10% max risk"""
        rm = RiskManager(account_size=10000, max_risk_percent=0.10)
        
        result = rm.calculate_position_size(entry_price=100, stop_loss_price=95)
        
        assert result['contracts'] > 0
        assert result['risk_amount'] <= 1000  # 10% of 10000
        assert result['risk_percent'] <= 10.0
    
    def test_max_risk_limit(self):
        """Test that position sizing respects 10% max risk"""
        rm = RiskManager(account_size=10000, max_risk_percent=0.10)
        
        # Small stop loss = large contracts
        result = rm.calculate_position_size(entry_price=100, stop_loss_price=99)
        
        assert result['risk_percent'] <= 10.0
    
    def test_trade_validation_long(self):
        """Test validation of a long trade"""
        rm = RiskManager(account_size=10000, max_risk_percent=0.10)
        
        validation = rm.validate_trade(
            entry_price=100,
            stop_loss=95,
            take_profit=110
        )
        
        assert validation['valid'] is True
        assert validation['direction'] == 'LONG'
        assert validation['risk_reward_ratio'] == 2.0  # 10 risk, 20 reward
    
    def test_trade_validation_short(self):
        """Test validation of a short trade"""
        rm = RiskManager(account_size=10000, max_risk_percent=0.10)
        
        validation = rm.validate_trade(
            entry_price=100,
            stop_loss=105,
            take_profit=90
        )
        
        assert validation['valid'] is True
        assert validation['direction'] == 'SHORT'
    
    def test_invalid_trade_same_price(self):
        """Test rejection of invalid trade (entry == stop loss)"""
        rm = RiskManager(account_size=10000, max_risk_percent=0.10)
        
        validation = rm.validate_trade(
            entry_price=100,
            stop_loss=100,
            take_profit=110
        )
        
        assert validation['valid'] is False
