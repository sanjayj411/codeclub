import os
import json
import base64
import threading
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta, timezone
import requests
from pathlib import Path
from src.core.logger import logger

class SchwabBrokerAPI:
    """Integration with Charles Schwab broker API using OAuth 2.0 with automatic token management"""
    
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
        
        # Token management
        self.access_token = None
        self.refresh_token = None
        self.access_token_issued = datetime.min.replace(tzinfo=timezone.utc)
        self.refresh_token_issued = datetime.min.replace(tzinfo=timezone.utc)
        self.access_token_timeout = 1800  # 30 minutes in seconds
        self.refresh_token_timeout = 7 * 24 * 60 * 60  # 7 days in seconds
        
        # Load existing token or prompt for authorization
        if token:
            self.access_token = token
        else:
            self._load_tokens()
        
        self.session = requests.Session()
        self._update_headers()
    
    def _update_headers(self):
        """Update session headers with current token"""
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })
    
    def _load_tokens(self) -> None:
        """Load tokens from file if they exist and are valid"""
        token_file = Path(self.token_path)
        
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    data = json.load(f)
                
                token_dict = data.get("token_dictionary", {})
                self.access_token = token_dict.get("access_token")
                self.refresh_token = token_dict.get("refresh_token")
                
                # Load issued times
                at_issued_str = data.get("access_token_issued")
                rt_issued_str = data.get("refresh_token_issued")
                
                if at_issued_str:
                    self.access_token_issued = datetime.fromisoformat(at_issued_str).replace(tzinfo=timezone.utc)
                if rt_issued_str:
                    self.refresh_token_issued = datetime.fromisoformat(rt_issued_str).replace(tzinfo=timezone.utc)
                
                logger.info("Tokens loaded from file")
                
                # Check if refresh token needs updating
                rt_delta = self.refresh_token_timeout - (
                    datetime.now(timezone.utc) - self.refresh_token_issued
                ).total_seconds()
                
                if rt_delta < 1800:  # Less than 30 minutes remaining
                    logger.warning(f"Refresh token expiring soon! {rt_delta/3600:.1f} hours remaining")
                    
            except Exception as e:
                logger.error(f"Error loading token file: {str(e)}")
                self.access_token = None
                self.refresh_token = None
        
        if not self.access_token or not self.refresh_token:
            logger.warning(f"No valid tokens found. Please authorize at:")
            logger.warning(f"https://developer.schwab.com")
    
    def _post_oauth_token(self, grant_type: str, code: str) -> requests.Response:
        """
        Make OAuth token request using Basic auth (like Schwabdev)
        
        Args:
            grant_type: 'authorization_code' or 'refresh_token'
            code: Authorization code or refresh token
            
        Returns:
            Response from OAuth token endpoint
        """
        # Create Basic auth header with app_key:app_secret
        auth_string = f"{self.app_key}:{self.app_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        if grant_type == 'authorization_code':
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': 'https://127.0.0.1'
            }
        elif grant_type == 'refresh_token':
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': code
            }
        else:
            raise ValueError("Invalid grant type")
        
        return requests.post(self.oauth_url, headers=headers, data=data)
    
    def _set_tokens(self, token_dict: Dict) -> None:
        """
        Save tokens to file and update internal state
        
        Args:
            token_dict: Dictionary with access_token, refresh_token, etc.
        """
        try:
            now = datetime.now(timezone.utc)
            
            self.access_token = token_dict.get('access_token')
            self.refresh_token = token_dict.get('refresh_token')
            self.access_token_issued = now
            self.refresh_token_issued = now
            
            # Save to file
            token_file = Path(self.token_path)
            token_file.parent.mkdir(parents=True, exist_ok=True)
            
            token_data = {
                "access_token_issued": now.isoformat(),
                "refresh_token_issued": now.isoformat(),
                "token_dictionary": token_dict
            }
            
            with open(token_file, 'w') as f:
                json.dump(token_data, f, ensure_ascii=False, indent=4)
            
            logger.info("Tokens saved successfully")
            self._update_headers()
            
        except Exception as e:
            logger.error(f"Error saving tokens: {str(e)}")
    
    def update_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token
        
        Returns:
            True if successful, False otherwise
        """
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False
        
        try:
            response = self._post_oauth_token('refresh_token', self.refresh_token)
            
            if response.ok:
                token_dict = response.json()
                self._set_tokens(token_dict)
                logger.info("Access token updated successfully")
                return True
            else:
                logger.error(f"Failed to update access token: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating access token: {str(e)}")
            return False
    
    def update_tokens(self) -> bool:
        """
        Check if tokens need to be updated and update if necessary
        
        Returns:
            True if tokens were updated, False otherwise
        """
        # Calculate time deltas
        now = datetime.now(timezone.utc)
        at_delta = self.access_token_timeout - (now - self.access_token_issued).total_seconds()
        rt_delta = self.refresh_token_timeout - (now - self.refresh_token_issued).total_seconds()
        
        # Check if refresh token is expiring
        if 30 <= rt_delta <= 43300 and rt_delta % 900 <= 30:  # Notify every ~15 minutes
            hours_remaining = int(abs(rt_delta) / 3600)
            logger.warning(f"Refresh token expires in {hours_remaining} hours")
        
        # Refresh token has expired
        if rt_delta < 1800:
            logger.warning("Refresh token expired!")
            logger.warning("Please re-authorize at https://developer.schwab.com")
            return False
        
        # Access token has expired
        if at_delta < 61:
            logger.info("Access token expired, updating...")
            return self.update_access_token()
        
        return False
    
    def authorize_and_save_token(self, authorization_code: str) -> bool:
        """
        Exchange authorization code for access and refresh tokens
        
        Args:
            authorization_code: Authorization code from OAuth flow
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self._post_oauth_token('authorization_code', authorization_code)
            
            if response.ok:
                token_dict = response.json()
                self._set_tokens(token_dict)
                logger.info("Authorization successful and tokens saved")
                return True
            else:
                logger.error(f"Authorization failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error during authorization: {str(e)}")
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
