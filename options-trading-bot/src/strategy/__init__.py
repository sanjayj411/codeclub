from typing import Optional, Dict
from src.indicators import TechnicalIndicators
from src.risk import RiskManager
from src.core.logger import logger

# Import TradingStrategy if available (created for backtesting)
try:
    from .trading_strategy import TradingStrategy
except ImportError:
    TradingStrategy = None

class OptionsStrategy:
    """Options trading strategy using RSI and Bollinger Bands"""
    
    def __init__(self, account_size: float = 10000, max_risk_percent: float = 0.10):
        self.account_size = account_size
        self.risk_manager = RiskManager(account_size, max_risk_percent)
        self.indicators = TechnicalIndicators()
        self.open_positions = []
    
    def generate_signal(self, prices: list, current_price: float, atr: Optional[float] = None) -> Dict:
        """
        Generate trading signal based on technical indicators
        
        Args:
            prices: List of recent prices
            current_price: Current market price
            atr: Average True Range for dynamic stop loss (optional)
            
        Returns:
            Signal data with entry, stop loss, and take profit levels
        """
        if len(prices) < 21:
            return {'signal': 'WAIT', 'reason': 'Not enough price data'}
        
        analysis = self.indicators.analyze_signals(prices, current_price)
        
        if not analysis['buy_signal'] and not analysis['sell_signal']:
            return {'signal': 'HOLD', 'reason': 'No clear signal'}
        
        # Use ATR for stop loss or fixed percentage
        stop_loss_offset = atr if atr else current_price * 0.02  # 2% default
        
        if analysis['buy_signal']:
            entry = current_price
            stop_loss = entry - stop_loss_offset
            take_profit = entry + (stop_loss_offset * 2)  # 1:2 risk/reward
            
            # Validate trade
            validation = self.risk_manager.validate_trade(entry, stop_loss, take_profit)
            
            if not validation['valid']:
                return {
                    'signal': 'REJECT',
                    'reason': validation.get('error'),
                    'analysis': analysis
                }
            
            return {
                'signal': 'BUY',
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position': validation['position'],
                'risk_reward_ratio': validation['risk_reward_ratio'],
                'signal_strength': analysis['signal_strength'],
                'analysis': analysis
            }
        
        elif analysis['sell_signal']:
            entry = current_price
            stop_loss = entry + stop_loss_offset
            take_profit = entry - (stop_loss_offset * 2)  # 1:2 risk/reward
            
            validation = self.risk_manager.validate_trade(entry, stop_loss, take_profit)
            
            if not validation['valid']:
                return {
                    'signal': 'REJECT',
                    'reason': validation.get('error'),
                    'analysis': analysis
                }
            
            return {
                'signal': 'SELL',
                'entry': entry,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position': validation['position'],
                'risk_reward_ratio': validation['risk_reward_ratio'],
                'signal_strength': analysis['signal_strength'],
                'analysis': analysis
            }
    
    def update_position(self, position_id: str, current_price: float) -> Optional[Dict]:
        """
        Update position and check for exit signals
        
        Returns exit signal if take profit or stop loss is hit
        """
        for pos in self.open_positions:
            if pos['id'] == position_id:
                if pos['direction'] == 'LONG':
                    if current_price >= pos['take_profit']:
                        return {'action': 'CLOSE', 'reason': 'Take profit hit', 'pnl': 'positive'}
                    elif current_price <= pos['stop_loss']:
                        return {'action': 'CLOSE', 'reason': 'Stop loss hit', 'pnl': 'negative'}
                
                elif pos['direction'] == 'SHORT':
                    if current_price <= pos['take_profit']:
                        return {'action': 'CLOSE', 'reason': 'Take profit hit', 'pnl': 'positive'}
                    elif current_price >= pos['stop_loss']:
                        return {'action': 'CLOSE', 'reason': 'Stop loss hit', 'pnl': 'negative'}
        
        return None
