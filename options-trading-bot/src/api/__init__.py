from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from src.strategy import OptionsStrategy
from src.bot import EnhancedTradingBot
from src.quant import QuantitativeAnalysis
from src.core.db import init_db
from src.core.logger import logger

# Initialize
init_db()
strategy = OptionsStrategy(account_size=10000, max_risk_percent=0.10)
quant = QuantitativeAnalysis()

app = FastAPI(
    title="Options Trading Bot with Quantitative Analysis",
    description="AI-powered options trading bot with RSI, Bollinger Bands, and Schwab broker integration",
    version="2.0.0"
)

# Request models
class SignalRequest(BaseModel):
    prices: List[float]
    current_price: float
    atr: Optional[float] = None

class PositionUpdate(BaseModel):
    position_id: str
    current_price: float

class TradeValidation(BaseModel):
    entry_price: float
    stop_loss: float
    take_profit: float

class SchwabConfig(BaseModel):
    account_number: str
    app_key: Optional[str] = None
    app_secret: Optional[str] = None
    token_path: Optional[str] = None
    token: Optional[str] = None  # Legacy support
    account_size: float = 10000

class SymbolAnalysis(BaseModel):
    symbol: str
    days: int = 60

class ExecuteSignal(BaseModel):
    symbol: str
    signal: str
    entry: float
    stop_loss: float
    take_profit: float
    contracts: int = 1

# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "bot": "options_trading_bot"}

@app.post("/signal")
async def generate_signal(request: SignalRequest):
    """
    Generate trading signal based on technical indicators
    
    Args:
        prices: List of recent closing prices
        current_price: Current market price
        atr: Average True Range (optional)
    """
    try:
        if len(request.prices) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 prices")
        
        signal = strategy.generate_signal(
            request.prices,
            request.current_price,
            request.atr
        )
        
        logger.info(f"Signal generated: {signal['signal']}")
        return signal
    
    except Exception as e:
        logger.error(f"Error generating signal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate-trade")
async def validate_trade(request: TradeValidation):
    """
    Validate if a trade meets risk/reward criteria
    
    Args:
        entry_price: Entry price for the trade
        stop_loss: Stop loss price
        take_profit: Take profit price
    """
    try:
        validation = strategy.risk_manager.validate_trade(
            request.entry_price,
            request.stop_loss,
            request.take_profit
        )
        
        logger.info(f"Trade validation: valid={validation['valid']}")
        return validation
    
    except Exception as e:
        logger.error(f"Error validating trade: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/position-update")
async def update_position(request: PositionUpdate):
    """
    Update position with current price and check for exits
    
    Args:
        position_id: Unique position identifier
        current_price: Current market price
    """
    try:
        result = strategy.update_position(
            request.position_id,
            request.current_price
        )
        
        return result or {"status": "OPEN", "action": "HOLD"}
    
    except Exception as e:
        logger.error(f"Error updating position: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/indicators-info")
async def get_indicators_info():
    """Get information about technical indicators used"""
    return {
        "indicators": ["RSI", "Bollinger Bands"],
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "rsi_period": 14,
        "bollinger_period": 20,
        "bollinger_std_dev": 2,
        "buy_signals": [
            "RSI < 30 and price < lower band",
            "RSI < 40 and price < middle band"
        ],
        "sell_signals": [
            "RSI > 70 and price > upper band",
            "RSI > 60 and price > middle band"
        ]
    }

# New Quantitative Analysis Endpoints

@app.post("/quant/volatility")
async def calculate_volatility(prices: List[float], window: int = 20):
    """Calculate historical volatility"""
    try:
        vol = quant.calculate_volatility(prices, window)
        return {"volatility": vol, "volatility_percent": vol * 100}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/quant/sharpe")
async def calculate_sharpe(prices: List[float], risk_free_rate: float = 0.02):
    """Calculate Sharpe ratio"""
    try:
        returns = quant.calculate_returns(prices)
        sharpe = quant.calculate_sharpe_ratio(returns, risk_free_rate)
        return {"sharpe_ratio": sharpe, "interpretation": "Higher is better"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/quant/drawdown")
async def calculate_drawdown(prices: List[float]):
    """Calculate maximum drawdown"""
    try:
        max_dd = quant.calculate_max_drawdown(prices)
        return {"max_drawdown_percent": max_dd}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/quant/regression")
async def get_regression(prices: List[float]):
    """Perform linear regression analysis"""
    try:
        regression = quant.regression_analysis(prices)
        return regression
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/quant/monte-carlo")
async def run_monte_carlo(
    current_price: float,
    returns_mean: float,
    returns_std: float,
    days: int = 20,
    simulations: int = 1000
):
    """Run Monte Carlo simulation for price projection"""
    try:
        mc = quant.monte_carlo_simulation(current_price, returns_mean, returns_std, days, simulations)
        return mc
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Schwab Broker Integration Endpoints

@app.get("/schwab/test")
async def test_schwab_connection(
    account_number: str,
    app_key: Optional[str] = None,
    app_secret: Optional[str] = None,
    token_path: Optional[str] = None,
    token: Optional[str] = None
):
    """
    Test Schwab API connection without errors
    
    Args:
        account_number: Schwab account number
        app_key: Schwab API App Key (or env var SCHWAB_APP_KEY)
        app_secret: Schwab API App Secret (or env var SCHWAB_SECRET)
        token_path: Path to token file (or env var SCHWAB_TOKEN)
        token: Direct OAuth token (legacy)
        
    Returns:
        Connection status and account info
    """
    try:
        broker = SchwabBrokerAPI(
            account_number,
            app_key=app_key,
            app_secret=app_secret,
            token_path=token_path,
            token=token
        )
        
        # Test 1: Get account info
        account = broker.get_account_info()
        if not account:
            return {
                "status": "FAILED",
                "test": "account_info",
                "error": "Could not retrieve account info",
                "troubleshooting": [
                    "Check if app_key and app_secret are valid",
                    "Verify account number is correct",
                    "Check if token is expired (use /schwab/authorize if needed)",
                    "Check API endpoint URL is accessible"
                ]
            }
        
        # Test 2: Get quote (for AAPL as test)
        quote = broker.get_quote("AAPL")
        if not quote:
            return {
                "status": "FAILED",
                "test": "quote",
                "error": "Could not retrieve quote for AAPL",
                "account": account.get('account_number'),
                "troubleshooting": [
                    "Check if quote API endpoint is accessible",
                    "Verify market is open (not after hours)",
                    "Try again during market hours"
                ]
            }
        
        # Test 3: Get price history (for AAPL as test)
        history = broker.get_price_history("AAPL", days=5)
        if not history:
            return {
                "status": "FAILED",
                "test": "price_history",
                "error": "Could not retrieve price history for AAPL",
                "account": account.get('account_number'),
                "quote": quote,
                "troubleshooting": [
                    "Check if pricehistory API endpoint is accessible",
                    "Verify API has proper scopes/permissions",
                    "Try with different time period",
                    "Check API rate limits"
                ]
            }
        
        return {
            "status": "SUCCESS",
            "account": account,
            "test_quote": quote,
            "price_history_candles": len(history),
            "message": "All tests passed. Your Schwab connection is working!"
        }
    
    except Exception as e:
        logger.error(f"Error testing Schwab connection: {str(e)}")
        return {
            "status": "ERROR",
            "error": str(e),
            "troubleshooting": [
                "Verify token format and validity",
                "Check account number format",
                "Ensure network connectivity",
                "Check Schwab API service status at https://developer.schwab.com"
            ]
        }

@app.post("/schwab/analyze")
async def analyze_with_schwab(request: SchwabConfig, symbol: str, days: int = 60):
    """
    Comprehensive analysis of a symbol using Schwab data
    
    Args:
        request: Schwab account configuration
        symbol: Stock symbol
        days: Days of historical data
    """
    try:
        bot = EnhancedTradingBot(
            request.account_number,
            app_key=request.app_key,
            app_secret=request.app_secret,
            token_path=request.token_path,
            token=request.token,
            account_size=request.account_size
        )
        analysis = bot.analyze_symbol(symbol, days)
        
        # If analysis has an error, return it with proper HTTP error code
        if 'error' in analysis:
            raise HTTPException(
                status_code=400,
                detail=analysis
            )
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Schwab analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "symbol": symbol,
                "troubleshooting": [
                    "Run GET /schwab/test first to diagnose connection",
                    "Verify symbol is valid",
                    "Check if market data is available for this symbol",
                    "Try with fewer days of history"
                ]
            }
        )

@app.post("/schwab/execute")
async def execute_on_schwab(request: SchwabConfig, order_data: ExecuteSignal):
    """
    Execute a trade on Schwab broker
    
    Args:
        request: Schwab account configuration
        order_data: Trade execution details
    """
    try:
        bot = EnhancedTradingBot(
            request.account_number,
            app_key=request.app_key,
            app_secret=request.app_secret,
            token_path=request.token_path,
            token=request.token,
            account_size=request.account_size
        )
        result = bot.execute_signal(order_data.symbol, {
            'signal': order_data.signal,
            'entry': order_data.entry,
            'stop_loss': order_data.stop_loss,
            'take_profit': order_data.take_profit,
            'position': {
                'contracts': order_data.contracts
            }
        })
        return result
    except Exception as e:
        logger.error(f"Error executing on Schwab: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schwab/monitor")
async def monitor_schwab_positions(request: SchwabConfig):
    """Monitor all open positions on Schwab"""
    try:
        bot = EnhancedTradingBot(
            request.account_number,
            app_key=request.app_key,
            app_secret=request.app_secret,
            token_path=request.token_path,
            token=request.token,
            account_size=request.account_size
        )
        positions = bot.monitor_positions()
        return {"positions": positions}
    except Exception as e:
        logger.error(f"Error monitoring positions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schwab/authorize")
async def authorize_schwab(
    account_number: str,
    authorization_code: str,
    app_key: Optional[str] = None,
    app_secret: Optional[str] = None,
    token_path: Optional[str] = None
):
    """
    Exchange Schwab authorization code for OAuth token
    
    Args:
        account_number: Schwab account number
        authorization_code: Authorization code from OAuth callback
        app_key: Schwab API App Key (or env var SCHWAB_APP_KEY)
        app_secret: Schwab API App Secret (or env var SCHWAB_SECRET)
        token_path: Path to store token (or env var SCHWAB_TOKEN)
        
    Returns:
        Authorization status
    """
    try:
        broker = SchwabBrokerAPI(
            account_number,
            app_key=app_key,
            app_secret=app_secret,
            token_path=token_path
        )
        
        success = broker.authorize_and_save_token(authorization_code)
        
        if success:
            return {
                "status": "SUCCESS",
                "message": "Token obtained and saved successfully",
                "token_path": broker.token_path,
                "account_number": account_number
            }
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "FAILED",
                    "error": "Failed to obtain token",
                    "troubleshooting": [
                        "Verify authorization_code is valid",
                        "Check if app_key and app_secret are correct",
                        "Ensure redirect_uri matches in Schwab developer settings"
                    ]
                }
            )
    except Exception as e:
        logger.error(f"Error authorizing Schwab: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/features")
async def get_features():
    """Get list of all features"""
    return {
        "technical_indicators": ["RSI", "Bollinger Bands"],
        "quantitative_analysis": [
            "Volatility", "Sharpe Ratio", "Maximum Drawdown", 
            "Regression Analysis", "Monte Carlo Simulation",
            "Correlation", "Value at Risk", "Beta", "Alpha"
        ],
        "broker_integration": ["Charles Schwab"],
        "risk_management": [
            "10% max risk per trade",
            "Automatic position sizing",
            "Risk/reward validation",
            "Stop loss and take profit"
        ]
    }

