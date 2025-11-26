import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
from src.core.logger import logger

class SchwabBrokerAPI:
    """Integration with Charles Schwab broker API for real trading"""
    
    def __init__(self, account_number: str, token: Optional[str] = None):
        """
        Initialize Schwab API connection
        
        Args:
            account_number: Your Schwab account number
            token: OAuth token (or set SCHWAB_TOKEN env var)
        """
        self.account_number = account_number
        self.token = token or os.getenv("SCHWAB_TOKEN")
        self.base_url = "https://api.schwabapi.com/trader/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_account_info(self) -> Dict:
        """Get account information and balances"""
        try:
            url = f"{self.base_url}/accounts/{self.account_number}"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Account info retrieved for {self.account_number}")
            
            return {
                'account_number': self.account_number,
                'buying_power': data.get('securitiesAccount', {}).get('buyingPower'),
                'cash_balance': data.get('securitiesAccount', {}).get('cashBalance'),
                'margin_available': data.get('securitiesAccount', {}).get('marginBalance'),
                'positions': data.get('securitiesAccount', {}).get('positions', [])
            }
        except Exception as e:
            logger.error(f"Error fetching account info: {str(e)}")
            return {}
    
    def get_quote(self, symbol: str) -> Dict:
        """Get real-time quote for a symbol"""
        try:
            url = f"{self.base_url}/marketdata/{symbol}/quotes"
            response = self.session.get(url)
            response.raise_for_status()
            
            quote = response.json()
            logger.info(f"Quote received for {symbol}: ${quote.get('lastPrice')}")
            
            return {
                'symbol': symbol,
                'price': quote.get('lastPrice'),
                'bid': quote.get('bidPrice'),
                'ask': quote.get('askPrice'),
                'volume': quote.get('totalVolume'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return {}
    
    def get_price_history(self, symbol: str, days: int = 60) -> List[Dict]:
        """
        Get historical price data for analysis
        
        Args:
            symbol: Stock symbol
            days: Number of days of history to fetch
            
        Returns:
            List of OHLC data
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            params = {
                'periodType': 'day',
                'frequencyType': 'daily',
                'frequency': 1,
                'startDate': int(start_date.timestamp() * 1000),
                'endDate': int(end_date.timestamp() * 1000)
            }
            
            url = f"{self.base_url}/marketdata/{symbol}/pricehistory"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            candles = data.get('candles', [])
            
            logger.info(f"Retrieved {len(candles)} candles for {symbol}")
            
            return [
                {
                    'timestamp': candle.get('datetime'),
                    'open': candle.get('open'),
                    'high': candle.get('high'),
                    'low': candle.get('low'),
                    'close': candle.get('close'),
                    'volume': candle.get('volume')
                }
                for candle in candles
            ]
        except Exception as e:
            logger.error(f"Error fetching price history for {symbol}: {str(e)}")
            return []
    
    def place_order(self, order: Dict) -> Dict:
        """
        Place an order on Schwab
        
        Args:
            order: Order dict with:
                - symbol: Stock symbol
                - quantity: Number of shares
                - instruction: BUY or SELL
                - orderType: MARKET or LIMIT
                - price: (optional) limit price
                
        Returns:
            Order confirmation
        """
        try:
            payload = {
                'orderType': order.get('orderType', 'MARKET'),
                'session': 'NORMAL',
                'duration': 'DAY',
                'orderStrategyType': 'SINGLE',
                'orderLegCollection': [
                    {
                        'instruction': order['instruction'],
                        'quantity': order['quantity'],
                        'instrument': {
                            'symbol': order['symbol'],
                            'assetType': 'EQUITY'
                        }
                    }
                ]
            }
            
            if order.get('orderType') == 'LIMIT':
                payload['price'] = order.get('price')
            
            url = f"{self.base_url}/accounts/{self.account_number}/orders"
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            order_id = response.headers.get('Location', '').split('/')[-1]
            logger.info(f"Order placed: {order['instruction']} {order['quantity']} {order['symbol']}")
            
            return {
                'status': 'PLACED',
                'order_id': order_id,
                'symbol': order['symbol'],
                'quantity': order['quantity'],
                'instruction': order['instruction']
            }
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def place_options_order(self, option: Dict) -> Dict:
        """
        Place an options order
        
        Args:
            option: Options order dict with:
                - symbol: Option symbol (e.g., "AAPL_011524C00150000")
                - quantity: Number of contracts
                - instruction: BUY_TO_OPEN, BUY_TO_CLOSE, SELL_TO_OPEN, SELL_TO_CLOSE
                - price: Limit price
                
        Returns:
            Order confirmation
        """
        try:
            payload = {
                'orderType': 'LIMIT',
                'session': 'NORMAL',
                'duration': 'DAY',
                'orderStrategyType': 'SINGLE',
                'price': option.get('price'),
                'orderLegCollection': [
                    {
                        'instruction': option['instruction'],
                        'quantity': option['quantity'],
                        'instrument': {
                            'symbol': option['symbol'],
                            'assetType': 'OPTION'
                        }
                    }
                ]
            }
            
            url = f"{self.base_url}/accounts/{self.account_number}/orders"
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            order_id = response.headers.get('Location', '').split('/')[-1]
            logger.info(f"Options order placed: {option['instruction']} {option['quantity']} {option['symbol']}")
            
            return {
                'status': 'PLACED',
                'order_id': order_id,
                'symbol': option['symbol'],
                'quantity': option['quantity'],
                'instruction': option['instruction']
            }
        except Exception as e:
            logger.error(f"Error placing options order: {str(e)}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get status of an order"""
        try:
            url = f"{self.base_url}/accounts/{self.account_number}/orders/{order_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            order = response.json()
            return {
                'order_id': order_id,
                'status': order.get('status'),
                'symbol': order.get('orderLegCollection', [{}])[0].get('instrument', {}).get('symbol'),
                'quantity': order.get('orderLegCollection', [{}])[0].get('quantity'),
                'filled_quantity': order.get('filledQuantity')
            }
        except Exception as e:
            logger.error(f"Error fetching order status: {str(e)}")
            return {}
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order"""
        try:
            url = f"{self.base_url}/accounts/{self.account_number}/orders/{order_id}"
            response = self.session.delete(url)
            response.raise_for_status()
            
            logger.info(f"Order {order_id} cancelled")
            return {'status': 'CANCELLED', 'order_id': order_id}
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return {'status': 'ERROR', 'error': str(e)}
