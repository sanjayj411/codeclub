from typing import Dict, Optional, List
from src.strategy import OptionsStrategy
from src.brokers import SchwabBrokerAPI
from src.quant import QuantitativeAnalysis
from src.core.logger import logger

class EnhancedTradingBot:
    """Enhanced trading bot with Schwab integration and quantitative analysis"""
    
    def __init__(self, account_number: str, schwab_token: str, account_size: float = 10000):
        """
        Initialize enhanced trading bot
        
        Args:
            account_number: Schwab account number
            schwab_token: Schwab OAuth token
            account_size: Account size for risk management
        """
        self.strategy = OptionsStrategy(account_size, max_risk_percent=0.10)
        self.broker = SchwabBrokerAPI(account_number, schwab_token)
        self.quant = QuantitativeAnalysis()
        self.account_size = account_size
        self.positions = []
    
    def analyze_symbol(self, symbol: str, days: int = 60) -> Dict:
        """
        Comprehensive analysis of a symbol
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data
            
        Returns:
            Complete analysis including technicals, quantitative metrics, and signal
        """
        try:
            # Get historical data from Schwab
            history = self.broker.get_price_history(symbol, days=days)
            
            if not history:
                logger.warning(f"No price history for {symbol}")
                return {
                    'error': f'No data for {symbol}',
                    'details': 'Failed to fetch price history from Schwab API. Check: 1) Token validity 2) Symbol spelling 3) API connectivity 4) Broker service status'
                }
            
            # Extract prices
            prices = [candle['close'] for candle in history]
            current_price = prices[-1]
            
            # Get current quote
            quote = self.broker.get_quote(symbol)
            
            # Technical analysis
            technical_signal = self.strategy.generate_signal(prices, current_price)
            
            # Quantitative analysis
            returns = self.quant.calculate_returns(prices)
            volatility = self.quant.calculate_volatility(prices)
            sharpe = self.quant.calculate_sharpe_ratio(returns)
            max_dd = self.quant.calculate_max_drawdown(prices)
            regression = self.quant.regression_analysis(prices)
            
            # Monte Carlo simulation
            returns_mean = returns.mean()
            returns_std = returns.std()
            mc_simulation = self.quant.monte_carlo_simulation(
                current_price, returns_mean, returns_std
            )
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'bid': quote.get('bid'),
                'ask': quote.get('ask'),
                'volume': quote.get('volume'),
                'technical': {
                    'signal': technical_signal.get('signal'),
                    'entry': technical_signal.get('entry'),
                    'stop_loss': technical_signal.get('stop_loss'),
                    'take_profit': technical_signal.get('take_profit'),
                    'signal_strength': technical_signal.get('signal_strength')
                },
                'quantitative': {
                    'volatility': volatility,
                    'sharpe_ratio': sharpe,
                    'max_drawdown': max_dd,
                    'trend': regression['trend'],
                    'slope': regression['slope']
                },
                'monte_carlo': mc_simulation,
                'recommendation': self._generate_recommendation(
                    technical_signal, volatility, sharpe, mc_simulation
                )
            }
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return {'error': str(e)}
    
    def execute_signal(self, symbol: str, signal_data: Dict) -> Dict:
        """
        Execute a trading signal on Schwab
        
        Args:
            symbol: Stock symbol
            signal_data: Signal data from analysis
            
        Returns:
            Execution result
        """
        try:
            if signal_data.get('signal') not in ['BUY', 'SELL']:
                return {'status': 'NO_SIGNAL', 'reason': f"Signal is {signal_data.get('signal')}"}
            
            position = signal_data.get('position', {})
            contracts = position.get('contracts', 1)
            quantity = contracts * 100  # 100 shares per contract
            
            # Place market order
            order = {
                'symbol': symbol,
                'quantity': quantity,
                'instruction': 'BUY' if signal_data['signal'] == 'BUY' else 'SELL',
                'orderType': 'MARKET'
            }
            
            result = self.broker.place_order(order)
            
            if result['status'] == 'PLACED':
                self.positions.append({
                    'order_id': result['order_id'],
                    'symbol': symbol,
                    'quantity': quantity,
                    'entry_price': signal_data.get('entry'),
                    'stop_loss': signal_data.get('stop_loss'),
                    'take_profit': signal_data.get('take_profit'),
                    'signal_strength': signal_data.get('signal_strength')
                })
                logger.info(f"Order executed: {order['instruction']} {quantity} {symbol}")
            
            return result
        except Exception as e:
            logger.error(f"Error executing signal: {str(e)}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def monitor_positions(self) -> List[Dict]:
        """Monitor all open positions and check for exits"""
        try:
            account_info = self.broker.get_account_info()
            current_positions = account_info.get('positions', [])
            
            updates = []
            for pos in self.positions:
                # Get current price
                quote = self.broker.get_quote(pos['symbol'])
                current_price = quote.get('price')
                
                if not current_price:
                    continue
                
                # Check stop loss
                if current_price <= pos['stop_loss']:
                    updates.append({
                        'symbol': pos['symbol'],
                        'action': 'CLOSE',
                        'reason': 'STOP_LOSS',
                        'price': current_price
                    })
                
                # Check take profit
                elif current_price >= pos['take_profit']:
                    updates.append({
                        'symbol': pos['symbol'],
                        'action': 'CLOSE',
                        'reason': 'TAKE_PROFIT',
                        'price': current_price
                    })
                
                # Update price
                else:
                    pnl_percent = ((current_price - pos['entry_price']) / pos['entry_price']) * 100
                    updates.append({
                        'symbol': pos['symbol'],
                        'status': 'OPEN',
                        'entry': pos['entry_price'],
                        'current': current_price,
                        'pnl_percent': pnl_percent
                    })
            
            return updates
        except Exception as e:
            logger.error(f"Error monitoring positions: {str(e)}")
            return []
    
    def _generate_recommendation(self, technical: Dict, volatility: float, 
                                sharpe: float, mc_sim: Dict) -> str:
        """Generate trading recommendation based on all analysis"""
        signal = technical.get('signal')
        prob_up = mc_sim.get('prob_up', 0.5)
        
        if signal not in ['BUY', 'SELL']:
            return 'HOLD'
        
        # Buy recommendation
        if signal == 'BUY':
            if sharpe > 1.0 and prob_up > 0.6:
                return 'STRONG_BUY'
            elif prob_up > 0.55:
                return 'BUY'
            else:
                return 'WEAK_BUY'
        
        # Sell recommendation
        if signal == 'SELL':
            if sharpe > 1.0 and prob_up < 0.4:
                return 'STRONG_SELL'
            elif prob_up < 0.45:
                return 'SELL'
            else:
                return 'WEAK_SELL'
        
        return 'HOLD'
