import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
from pathlib import Path
from src.core.logger import logger

class SchwabBrokerAPI:
    """Integration with Charles Schwab broker API for real trading"""
    
    def __init__(
        self,
        account_number: str,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        token_path: Optional[str] = None,
        token: Optional[str] = None
    ):
        """
        Initialize Schwab API connection using OAuth 2.0
        
        Args:
            account_number: Your Schwab account number
            app_key: Schwab API App Key (or set SCHWAB_APP_KEY env var)
            app_secret: Schwab API App Secret (or set SCHWAB_SECRET env var)
            token_path: Path to store/load OAuth tokens (or set SCHWAB_TOKEN env var)
            token: Direct OAuth token (legacy, overrides token_path)
        """
        self.account_number = account_number
        self.app_key = app_key or os.getenv("SCHWAB_APP_KEY")
        self.app_secret = app_secret or os.getenv("SCHWAB_SECRET")
        self.token_path = token_path or os.getenv("SCHWAB_TOKEN", "./tokens/schwabToken.json")
        self.base_url = "https://api.schwabapi.com/trader/v1"
        self.oauth_url = "https://api.schwabapi.com/v1/oauth/token"
        
        # Direct token takes precedence
        if token:
            self.token = token
        else:
            # Try to load from token file
            self.token = self._load_or_refresh_token()
        
        self.session = requests.Session()
        self._update_headers()
    
    def _update_headers(self):
        """Update session headers with current token"""
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })
    
    def _load_or_refresh_token(self) -> str:
        """
        Load token from file or refresh if expired
        
        Returns:
            Valid OAuth token
        """
        token_file = Path(self.token_path)
        
        # Try to load existing token
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                
                # Check if token is expired
                expires_at = token_data.get('expires_at')
                if expires_at and datetime.fromisoformat(expires_at) > datetime.now():
                    logger.info("Loaded valid token from file")
                    return token_data.get('access_token')
                
                # Token expired, try to refresh
                refresh_token = token_data.get('refresh_token')
                if refresh_token:
                    logger.info("Token expired, refreshing...")
                    return self._refresh_token(refresh_token)
            except Exception as e:
                logger.error(f"Error loading token file: {str(e)}")
        
        # No valid token found, need to request new one
        logger.warning(f"No valid token found at {self.token_path}")
        logger.warning("Please obtain a new OAuth token from https://developer.schwab.com")
        return ""
    
    def _refresh_token(self, refresh_token: str) -> str:
        """
        Refresh OAuth token using refresh token
        
        Args:
            refresh_token: Refresh token from previous authorization
            
        Returns:
            New access token
        """
        try:
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.app_key,
                "client_secret": self.app_secret
            }
            
            response = requests.post(self.oauth_url, data=payload)
            response.raise_for_status()
            
            token_data = response.json()
            token_data['expires_at'] = (
                datetime.now() + timedelta(seconds=token_data.get('expires_in', 1800))
            ).isoformat()
            
            # Save new token
            self._save_token(token_data)
            logger.info("Token refreshed successfully")
            
            return token_data.get('access_token')
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return ""
    
    def _save_token(self, token_data: Dict):
        """
        Save token data to file
        
        Args:
            token_data: Token data dictionary with access_token, refresh_token, etc.
        """
        try:
            token_file = Path(self.token_path)
            token_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            logger.info(f"Token saved to {self.token_path}")
        except Exception as e:
            logger.error(f"Error saving token: {str(e)}")
    
    def authorize_and_save_token(self, authorization_code: str) -> bool:
        """
        Exchange authorization code for access token (OAuth 2.0 flow)
        
        Args:
            authorization_code: Authorization code from OAuth callback
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "client_id": self.app_key,
                "client_secret": self.app_secret,
                "redirect_uri": "http://localhost:8000/callback"
            }
            
            response = requests.post(self.oauth_url, data=payload)
            response.raise_for_status()
            
            token_data = response.json()
            token_data['expires_at'] = (
                datetime.now() + timedelta(seconds=token_data.get('expires_in', 1800))
            ).isoformat()
            
            self._save_token(token_data)
            self.token = token_data.get('access_token')
            self._update_headers()
            
            logger.info("Token obtained and saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error obtaining token: {str(e)}")
            return False
    
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
