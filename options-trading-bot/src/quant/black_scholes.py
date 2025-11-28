"""
Black-Scholes Options Pricing Model

Calculates theoretical option prices and Greeks (Delta, Gamma, Vega, Theta, Rho)
for European-style options. Useful for identifying mispriced options and managing
risk exposure in options positions.
"""

import math
from typing import Dict, Tuple, Optional
from scipy.stats import norm
from datetime import datetime, timedelta


class BlackScholesModel:
    """Black-Scholes options pricing calculator"""
    
    # Risk-free rate (default to 5% annual)
    RISK_FREE_RATE = 0.05
    
    @staticmethod
    def calculate_time_to_expiration(expiration_date: datetime, current_date: Optional[datetime] = None) -> float:
        """
        Calculate time to expiration in years
        
        Args:
            expiration_date: Option expiration date
            current_date: Current date (default to today)
            
        Returns:
            Time to expiration in years (minimum 1/365 for same-day expiry)
        """
        if current_date is None:
            current_date = datetime.now()
        
        days_remaining = (expiration_date.date() - current_date.date()).days
        # Ensure at least 1 day
        days_remaining = max(1, days_remaining)
        return days_remaining / 365.0
    
    @staticmethod
    def calculate_d1_d2(
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float = RISK_FREE_RATE
    ) -> Tuple[float, float]:
        """
        Calculate d1 and d2 components of Black-Scholes formula
        
        Args:
            spot_price: Current stock price
            strike_price: Option strike price
            time_to_expiry: Time to expiration in years
            volatility: Historical or implied volatility (0.0-1.0)
            risk_free_rate: Risk-free interest rate
            
        Returns:
            Tuple of (d1, d2)
        """
        if time_to_expiry <= 0 or volatility <= 0 or spot_price <= 0:
            return 0.0, 0.0
        
        d1 = (
            math.log(spot_price / strike_price) +
            (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry
        ) / (volatility * math.sqrt(time_to_expiry))
        
        d2 = d1 - volatility * math.sqrt(time_to_expiry)
        
        return d1, d2
    
    @staticmethod
    def call_price(
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float = RISK_FREE_RATE
    ) -> float:
        """
        Calculate European call option price
        
        Args:
            spot_price: Current stock price
            strike_price: Option strike price
            time_to_expiry: Time to expiration in years
            volatility: Volatility (annual, 0.0-1.0)
            risk_free_rate: Risk-free rate (annual)
            
        Returns:
            Call option price
        """
        d1, d2 = BlackScholesModel.calculate_d1_d2(
            spot_price, strike_price, time_to_expiry, volatility, risk_free_rate
        )
        
        call = (
            spot_price * norm.cdf(d1) -
            strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
        )
        
        return max(0, call)
    
    @staticmethod
    def put_price(
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float = RISK_FREE_RATE
    ) -> float:
        """
        Calculate European put option price
        
        Args:
            spot_price: Current stock price
            strike_price: Option strike price
            time_to_expiry: Time to expiration in years
            volatility: Volatility (annual, 0.0-1.0)
            risk_free_rate: Risk-free rate (annual)
            
        Returns:
            Put option price
        """
        d1, d2 = BlackScholesModel.calculate_d1_d2(
            spot_price, strike_price, time_to_expiry, volatility, risk_free_rate
        )
        
        put = (
            strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) -
            spot_price * norm.cdf(-d1)
        )
        
        return max(0, put)
    
    @staticmethod
    def delta(
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        option_type: str = 'call',
        risk_free_rate: float = RISK_FREE_RATE
    ) -> float:
        """
        Calculate option Delta (price sensitivity to stock price changes)
        
        Interpretation:
            - Call Delta: 0 to 1 (positive = bullish)
            - Put Delta: -1 to 0 (negative = bearish)
            - Delta of 0.5 = 50% probability ITM at expiration
        """
        d1, _ = BlackScholesModel.calculate_d1_d2(
            spot_price, strike_price, time_to_expiry, volatility, risk_free_rate
        )
        
        if option_type.lower() == 'call':
            return norm.cdf(d1)
        else:  # put
            return norm.cdf(d1) - 1
    
    @staticmethod
    def gamma(
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float = RISK_FREE_RATE
    ) -> float:
        """
        Calculate option Gamma (rate of change of Delta)
        
        Interpretation:
            - Higher Gamma = Delta changes faster
            - ATM options have highest Gamma
            - Gamma risk increases as expiration approaches
        """
        d1, _ = BlackScholesModel.calculate_d1_d2(
            spot_price, strike_price, time_to_expiry, volatility, risk_free_rate
        )
        
        gamma = norm.pdf(d1) / (spot_price * volatility * math.sqrt(time_to_expiry))
        return gamma
    
    @staticmethod
    def vega(
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float = RISK_FREE_RATE
    ) -> float:
        """
        Calculate option Vega (volatility sensitivity)
        
        Interpretation:
            - Vega = price change per 1% change in volatility
            - Long options benefit from IV increase
            - Higher Vega = more sensitive to volatility
            - Vega peaks at ATM, decreases toward expiration
        """
        d1, _ = BlackScholesModel.calculate_d1_d2(
            spot_price, strike_price, time_to_expiry, volatility, risk_free_rate
        )
        
        vega = spot_price * norm.pdf(d1) * math.sqrt(time_to_expiry) / 100
        return vega
    
    @staticmethod
    def theta(
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        option_type: str = 'call',
        risk_free_rate: float = RISK_FREE_RATE
    ) -> float:
        """
        Calculate option Theta (time decay)
        
        Interpretation:
            - Theta = daily price decay (option loses value as time passes)
            - Call Theta typically negative (loses value)
            - Put Theta can be positive or negative
            - Theta accelerates as expiration approaches
            - Theta is positive for short positions
        """
        d1, d2 = BlackScholesModel.calculate_d1_d2(
            spot_price, strike_price, time_to_expiry, volatility, risk_free_rate
        )
        
        if option_type.lower() == 'call':
            theta = (
                -spot_price * norm.pdf(d1) * volatility / (2 * math.sqrt(time_to_expiry)) -
                risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
            ) / 365
        else:  # put
            theta = (
                -spot_price * norm.pdf(d1) * volatility / (2 * math.sqrt(time_to_expiry)) +
                risk_free_rate * strike_price * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2)
            ) / 365
        
        return theta
    
    @staticmethod
    def rho(
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        option_type: str = 'call',
        risk_free_rate: float = RISK_FREE_RATE
    ) -> float:
        """
        Calculate option Rho (interest rate sensitivity)
        
        Interpretation:
            - Rho = price change per 1% change in interest rates
            - Call Rho positive (benefit from rising rates)
            - Put Rho negative (hurt by rising rates)
            - Rho significance increases with time to expiration
        """
        _, d2 = BlackScholesModel.calculate_d1_d2(
            spot_price, strike_price, time_to_expiry, volatility, risk_free_rate
        )
        
        if option_type.lower() == 'call':
            rho = strike_price * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2) / 100
        else:  # put
            rho = -strike_price * time_to_expiry * math.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) / 100
        
        return rho
    
    @staticmethod
    def price_option_chain(
        spot_price: float,
        strikes: list,
        time_to_expiry: float,
        volatility: float,
        option_type: str = 'call',
        risk_free_rate: float = RISK_FREE_RATE
    ) -> Dict[float, float]:
        """
        Price multiple option strikes (option chain)
        
        Args:
            spot_price: Current stock price
            strikes: List of strike prices
            time_to_expiry: Time to expiration in years
            volatility: Volatility
            option_type: 'call' or 'put'
            risk_free_rate: Risk-free rate
            
        Returns:
            Dictionary mapping strike to price
        """
        chain = {}
        pricer = BlackScholesModel.call_price if option_type.lower() == 'call' else BlackScholesModel.put_price
        
        for strike in strikes:
            price = pricer(spot_price, strike, time_to_expiry, volatility, risk_free_rate)
            chain[strike] = price
        
        return chain
    
    @staticmethod
    def calculate_greeks(
        spot_price: float,
        strike_price: float,
        time_to_expiry: float,
        volatility: float,
        option_type: str = 'call',
        risk_free_rate: float = RISK_FREE_RATE
    ) -> Dict[str, float]:
        """
        Calculate all Greeks for an option
        
        Returns:
            Dictionary with keys: delta, gamma, vega, theta, rho, price
        """
        call_price = BlackScholesModel.call_price(
            spot_price, strike_price, time_to_expiry, volatility, risk_free_rate
        )
        put_price = BlackScholesModel.put_price(
            spot_price, strike_price, time_to_expiry, volatility, risk_free_rate
        )
        
        return {
            'spot_price': spot_price,
            'strike_price': strike_price,
            'time_to_expiry_years': time_to_expiry,
            'volatility': volatility,
            'option_type': option_type,
            'price': call_price if option_type.lower() == 'call' else put_price,
            'delta': BlackScholesModel.delta(spot_price, strike_price, time_to_expiry, volatility, option_type, risk_free_rate),
            'gamma': BlackScholesModel.gamma(spot_price, strike_price, time_to_expiry, volatility, risk_free_rate),
            'vega': BlackScholesModel.vega(spot_price, strike_price, time_to_expiry, volatility, risk_free_rate),
            'theta': BlackScholesModel.theta(spot_price, strike_price, time_to_expiry, volatility, option_type, risk_free_rate),
            'rho': BlackScholesModel.rho(spot_price, strike_price, time_to_expiry, volatility, option_type, risk_free_rate),
        }


def estimate_volatility_from_prices(prices: list, window: int = 20) -> float:
    """
    Estimate annualized volatility from historical prices
    
    Args:
        prices: List of closing prices
        window: Number of periods to use (default 20 days)
        
    Returns:
        Annualized volatility as decimal (0.0-1.0)
    """
    if len(prices) < 2:
        return 0.20  # Default 20% if insufficient data
    
    # Use most recent window
    recent_prices = prices[-window:] if len(prices) >= window else prices
    
    # Calculate daily returns
    returns = []
    for i in range(1, len(recent_prices)):
        daily_return = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
        returns.append(daily_return)
    
    if not returns:
        return 0.20
    
    # Calculate standard deviation of returns
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    daily_volatility = math.sqrt(variance)
    
    # Annualize (252 trading days per year)
    annual_volatility = daily_volatility * math.sqrt(252)
    
    return min(2.0, max(0.05, annual_volatility))  # Clamp between 5% and 200%
