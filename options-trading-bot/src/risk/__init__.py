from typing import Dict, Optional
from src.core.logger import logger

class RiskManager:
    """Manage position sizing and risk with max 10% portfolio risk"""
    
    def __init__(self, account_size: float, max_risk_percent: float = 0.10):
        """
        Initialize risk manager
        
        Args:
            account_size: Total account balance
            max_risk_percent: Maximum risk per trade (default 10%)
        """
        self.account_size = account_size
        self.max_risk_percent = max_risk_percent
        self.max_risk_amount = account_size * max_risk_percent
    
    def calculate_position_size(self, entry_price: float, stop_loss_price: float) -> Dict:
        """
        Calculate safe position size based on risk/reward
        
        Args:
            entry_price: Price at which we're entering
            stop_loss_price: Stop loss price
            
        Returns:
            {
                'contracts': number of contracts to buy,
                'risk_amount': amount at risk,
                'position_size': total notional value
            }
        """
        if entry_price == stop_loss_price:
            return {
                'contracts': 0,
                'risk_amount': 0,
                'position_size': 0,
                'error': 'Entry and stop loss prices are the same'
            }
        
        price_diff = abs(entry_price - stop_loss_price)
        risk_amount = self.max_risk_amount
        
        # For options, each contract typically controls 100 shares
        contracts = int(risk_amount / (price_diff * 100))
        
        if contracts <= 0:
            contracts = 1
        
        position_size = contracts * 100 * entry_price
        actual_risk = contracts * 100 * price_diff
        
        return {
            'contracts': contracts,
            'risk_amount': actual_risk,
            'position_size': position_size,
            'risk_percent': (actual_risk / self.account_size) * 100
        }
    
    def validate_trade(self, entry_price: float, stop_loss: float, take_profit: float) -> Dict:
        """
        Validate if a trade meets risk/reward criteria
        
        Returns validation results and position details
        """
        if entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
            return {'valid': False, 'error': 'Prices must be positive'}
        
        if entry_price == stop_loss:
            return {'valid': False, 'error': 'Stop loss equals entry price'}
        
        # Ensure take profit is in right direction
        is_long = take_profit > entry_price
        is_short = take_profit < entry_price
        
        if is_long and stop_loss > entry_price:
            return {'valid': False, 'error': 'Long trade: stop loss should be below entry'}
        
        if is_short and stop_loss < entry_price:
            return {'valid': False, 'error': 'Short trade: stop loss should be above entry'}
        
        position = self.calculate_position_size(entry_price, stop_loss)
        
        if position['risk_percent'] > (self.max_risk_percent * 100):
            return {
                'valid': False,
                'error': f"Risk exceeds max {self.max_risk_percent*100}%",
                'position': position
            }
        
        # Calculate risk/reward ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        risk_reward_ratio = reward / risk if risk > 0 else 0
        
        return {
            'valid': True,
            'position': position,
            'risk_reward_ratio': risk_reward_ratio,
            'direction': 'LONG' if is_long else 'SHORT'
        }
