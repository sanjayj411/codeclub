"""
Monte Carlo Simulation for Options Pricing and Risk Analysis

Uses geometric Brownian motion to simulate price paths and estimate:
- Option prices at expiration
- Probability of reaching strike prices
- Value-at-Risk (VaR)
- Expected shortfall (CVaR)
- Path-dependent option pricing (Asian, Barrier, etc.)
"""

import random
import math
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class MonteCarloSimulator:
    """Monte Carlo simulation for options and risk analysis"""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize Monte Carlo simulator
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        self.simulation_results = None
    
    @staticmethod
    def simulate_price_paths(
        spot_price: float,
        volatility: float,
        risk_free_rate: float,
        time_steps: int,
        num_simulations: int,
        days_to_expiry: int
    ) -> List[List[float]]:
        """
        Simulate stock price paths using geometric Brownian motion
        
        GBM formula: dS = μS*dt + σS*dW
        where:
            - μ = risk-free rate (drift)
            - σ = volatility
            - dW = random normal increment
            - dt = time step
        
        Args:
            spot_price: Current stock price
            volatility: Annual volatility (0.0-1.0)
            risk_free_rate: Annual risk-free rate (0.0-1.0)
            time_steps: Number of time steps to simulate
            num_simulations: Number of price paths to generate
            days_to_expiry: Days until expiration
            
        Returns:
            List of price paths, each path is a list of prices
        """
        dt = days_to_expiry / (365 * time_steps)  # Time step in years
        
        paths = []
        
        for _ in range(num_simulations):
            path = [spot_price]
            current_price = spot_price
            
            for _ in range(time_steps):
                # Random normal variable
                random_normal = random.gauss(0, 1)
                
                # GBM step
                drift = (risk_free_rate - 0.5 * volatility ** 2) * dt
                diffusion = volatility * math.sqrt(dt) * random_normal
                
                # New price
                current_price = current_price * math.exp(drift + diffusion)
                path.append(current_price)
            
            paths.append(path)
        
        return paths
    
    @staticmethod
    def price_european_option(
        spot_price: float,
        strike_price: float,
        volatility: float,
        risk_free_rate: float,
        days_to_expiry: int,
        option_type: str = 'call',
        num_simulations: int = 10000,
        time_steps: int = 252
    ) -> Dict[str, float]:
        """
        Price European option using Monte Carlo
        
        Args:
            spot_price: Current stock price
            strike_price: Option strike price
            volatility: Annual volatility
            risk_free_rate: Annual risk-free rate
            days_to_expiry: Days until expiration
            option_type: 'call' or 'put'
            num_simulations: Number of simulations
            time_steps: Time steps per simulation
            
        Returns:
            Dictionary with price, std_error, 95% confidence interval
        """
        paths = MonteCarloSimulator.simulate_price_paths(
            spot_price, volatility, risk_free_rate, time_steps, num_simulations, days_to_expiry
        )
        
        # Get final prices
        final_prices = [path[-1] for path in paths]
        
        # Calculate payoffs
        if option_type.lower() == 'call':
            payoffs = [max(price - strike_price, 0) for price in final_prices]
        else:  # put
            payoffs = [max(strike_price - price, 0) for price in final_prices]
        
        # Discount to present value
        discount_factor = math.exp(-risk_free_rate * (days_to_expiry / 365))
        discounted_payoffs = [payoff * discount_factor for payoff in payoffs]
        
        # Calculate statistics
        mean_price = sum(discounted_payoffs) / len(discounted_payoffs)
        
        # Standard error
        variance = sum((p - mean_price) ** 2 for p in discounted_payoffs) / len(discounted_payoffs)
        std_dev = math.sqrt(variance)
        std_error = std_dev / math.sqrt(num_simulations)
        
        # 95% confidence interval
        ci_lower = mean_price - 1.96 * std_error
        ci_upper = mean_price + 1.96 * std_error
        
        return {
            'option_price': mean_price,
            'std_error': std_error,
            'std_dev': std_dev,
            'ci_lower': max(0, ci_lower),
            'ci_upper': ci_upper,
            'num_simulations': num_simulations,
            'final_prices': final_prices,
            'payoffs': payoffs
        }
    
    @staticmethod
    def calculate_probability_itm(
        spot_price: float,
        strike_price: float,
        volatility: float,
        risk_free_rate: float,
        days_to_expiry: int,
        option_type: str = 'call',
        num_simulations: int = 10000,
        time_steps: int = 252
    ) -> Dict[str, float]:
        """
        Calculate probability of option finishing in-the-money (ITM)
        
        Args:
            spot_price: Current stock price
            strike_price: Option strike price
            volatility: Annual volatility
            risk_free_rate: Annual risk-free rate
            days_to_expiry: Days until expiration
            option_type: 'call' or 'put'
            num_simulations: Number of simulations
            time_steps: Time steps per simulation
            
        Returns:
            Dictionary with ITM probability and max price reached
        """
        paths = MonteCarloSimulator.simulate_price_paths(
            spot_price, volatility, risk_free_rate, time_steps, num_simulations, days_to_expiry
        )
        
        # Get final prices and max prices
        final_prices = [path[-1] for path in paths]
        max_prices = [max(path) for path in paths]
        
        # Calculate ITM outcomes
        if option_type.lower() == 'call':
            itm_count = sum(1 for p in final_prices if p > strike_price)
            max_price_at_strike = sum(1 for p in max_prices if p > strike_price)
        else:  # put
            itm_count = sum(1 for p in final_prices if p < strike_price)
            max_price_at_strike = sum(1 for p in max_prices if p < strike_price)
        
        prob_itm = itm_count / num_simulations
        prob_touch = max_price_at_strike / num_simulations
        
        return {
            'prob_itm_at_expiry': prob_itm,
            'prob_touch_strike': prob_touch,
            'min_final_price': min(final_prices),
            'max_final_price': max(final_prices),
            'avg_final_price': sum(final_prices) / len(final_prices),
            'num_simulations': num_simulations
        }
    
    @staticmethod
    def calculate_var_cvar(
        spot_price: float,
        strike_price: float,
        position_size: int,
        option_type: str = 'call',
        volatility: float = 0.20,
        risk_free_rate: float = 0.05,
        days_to_expiry: int = 30,
        confidence_level: float = 0.95,
        num_simulations: int = 10000,
        time_steps: int = 252
    ) -> Dict[str, float]:
        """
        Calculate Value-at-Risk (VaR) and Conditional VaR (CVaR) for options position
        
        VaR: Maximum expected loss with confidence level
        CVaR: Expected loss given that loss exceeds VaR
        
        Args:
            spot_price: Current stock price
            strike_price: Option strike price
            position_size: Number of option contracts
            option_type: 'call' or 'put'
            volatility: Annual volatility
            risk_free_rate: Annual risk-free rate
            days_to_expiry: Days until expiration
            confidence_level: Confidence level (0.90, 0.95, 0.99)
            num_simulations: Number of simulations
            time_steps: Time steps per simulation
            
        Returns:
            Dictionary with VaR, CVaR, and percentiles
        """
        paths = MonteCarloSimulator.simulate_price_paths(
            spot_price, volatility, risk_free_rate, time_steps, num_simulations, days_to_expiry
        )
        
        # Calculate P&L for each path
        pnl_list = []
        
        for path in paths:
            final_price = path[-1]
            
            if option_type.lower() == 'call':
                payoff = max(final_price - strike_price, 0)
                # Assume bought at ATM
                premium = 0.05 * spot_price  # Rough estimate
            else:  # put
                payoff = max(strike_price - final_price, 0)
                premium = 0.05 * spot_price
            
            # PnL per contract
            pnl_per_contract = payoff - premium
            
            # Total PnL for position
            total_pnl = pnl_per_contract * position_size
            pnl_list.append(total_pnl)
        
        # Sort P&L (worst to best)
        pnl_list.sort()
        
        # Calculate percentiles
        percentile_5 = int(num_simulations * (1 - confidence_level))
        percentile_10 = int(num_simulations * 0.10)
        
        var = -pnl_list[percentile_5]  # Negative because loss
        cvar = -sum(pnl_list[:percentile_5]) / percentile_5 if percentile_5 > 0 else var
        
        return {
            'var_95': var,
            'cvar_95': cvar,
            'worst_loss': -pnl_list[0],
            'best_gain': pnl_list[-1],
            'median_pnl': pnl_list[num_simulations // 2],
            'percentile_10': pnl_list[percentile_10],
            'percentile_90': pnl_list[-percentile_10],
            'num_simulations': num_simulations
        }
    
    @staticmethod
    def price_asian_option(
        spot_price: float,
        strike_price: float,
        volatility: float,
        risk_free_rate: float,
        days_to_expiry: int,
        option_type: str = 'call',
        num_simulations: int = 10000,
        time_steps: int = 252
    ) -> Dict[str, float]:
        """
        Price Asian option (arithmetic average) using Monte Carlo
        
        Asian options use average price over life of option, which reduces volatility
        compared to European options.
        
        Args:
            spot_price: Current stock price
            strike_price: Option strike price
            volatility: Annual volatility
            risk_free_rate: Annual risk-free rate
            days_to_expiry: Days until expiration
            option_type: 'call' or 'put'
            num_simulations: Number of simulations
            time_steps: Time steps per simulation
            
        Returns:
            Dictionary with option price and statistics
        """
        paths = MonteCarloSimulator.simulate_price_paths(
            spot_price, volatility, risk_free_rate, time_steps, num_simulations, days_to_expiry
        )
        
        # Calculate average price for each path
        average_prices = [sum(path) / len(path) for path in paths]
        
        # Calculate payoffs using average
        if option_type.lower() == 'call':
            payoffs = [max(avg - strike_price, 0) for avg in average_prices]
        else:  # put
            payoffs = [max(strike_price - avg, 0) for avg in average_prices]
        
        # Discount to present value
        discount_factor = math.exp(-risk_free_rate * (days_to_expiry / 365))
        discounted_payoffs = [payoff * discount_factor for payoff in payoffs]
        
        # Calculate statistics
        mean_price = sum(discounted_payoffs) / len(discounted_payoffs)
        variance = sum((p - mean_price) ** 2 for p in discounted_payoffs) / len(discounted_payoffs)
        std_dev = math.sqrt(variance)
        std_error = std_dev / math.sqrt(num_simulations)
        
        return {
            'option_price': mean_price,
            'std_error': std_error,
            'std_dev': std_dev,
            'ci_lower': max(0, mean_price - 1.96 * std_error),
            'ci_upper': mean_price + 1.96 * std_error,
            'num_simulations': num_simulations
        }
    
    @staticmethod
    def analyze_option_path_statistics(
        spot_price: float,
        volatility: float,
        risk_free_rate: float,
        days_to_expiry: int,
        num_simulations: int = 10000,
        time_steps: int = 252
    ) -> Dict[str, float]:
        """
        Analyze stock price path statistics for risk assessment
        
        Returns statistics about price movements across all simulations
        """
        paths = MonteCarloSimulator.simulate_price_paths(
            spot_price, volatility, risk_free_rate, time_steps, num_simulations, days_to_expiry
        )
        
        final_prices = [path[-1] for path in paths]
        max_prices = [max(path) for path in paths]
        min_prices = [min(path) for path in paths]
        
        # Calculate max drawdown for each path
        drawdowns = []
        for path in paths:
            running_max = path[0]
            max_dd = 0
            for price in path[1:]:
                if price > running_max:
                    running_max = price
                dd = (running_max - price) / running_max
                max_dd = max(max_dd, dd)
            drawdowns.append(max_dd)
        
        return {
            'final_price_mean': sum(final_prices) / len(final_prices),
            'final_price_std': math.sqrt(sum((p - sum(final_prices)/len(final_prices))**2 for p in final_prices) / len(final_prices)),
            'final_price_min': min(final_prices),
            'final_price_max': max(final_prices),
            'max_price_mean': sum(max_prices) / len(max_prices),
            'min_price_mean': sum(min_prices) / len(min_prices),
            'avg_max_drawdown': sum(drawdowns) / len(drawdowns),
            'worst_case_drawdown': max(drawdowns),
            'prob_positive_return': sum(1 for p in final_prices if p > spot_price) / len(final_prices),
            'num_simulations': num_simulations
        }


def estimate_implied_volatility_newton_raphson(
    option_price: float,
    spot_price: float,
    strike_price: float,
    days_to_expiry: int,
    option_type: str = 'call',
    risk_free_rate: float = 0.05,
    max_iterations: int = 100,
    tolerance: float = 0.001
) -> Optional[float]:
    """
    Estimate implied volatility using Newton-Raphson method
    
    Used to back out market's expectation of volatility from option prices
    
    Args:
        option_price: Market price of option
        spot_price: Current stock price
        strike_price: Strike price
        days_to_expiry: Days until expiration
        option_type: 'call' or 'put'
        risk_free_rate: Risk-free rate
        max_iterations: Maximum iterations
        tolerance: Convergence tolerance
        
    Returns:
        Implied volatility or None if failed to converge
    """
    from src.quant.black_scholes import BlackScholesModel
    
    # Initial guess
    iv = 0.20
    time_to_expiry = days_to_expiry / 365.0
    
    for i in range(max_iterations):
        # Black-Scholes price at current IV
        pricer = BlackScholesModel.call_price if option_type.lower() == 'call' else BlackScholesModel.put_price
        bs_price = pricer(spot_price, strike_price, time_to_expiry, iv, risk_free_rate)
        
        # Vega for Newton-Raphson step
        vega = BlackScholesModel.vega(spot_price, strike_price, time_to_expiry, iv, risk_free_rate)
        
        if vega < 1e-10:
            return None
        
        # Newton-Raphson step
        iv_new = iv + (option_price - bs_price) / vega
        
        # Check convergence
        if abs(iv_new - iv) < tolerance:
            return iv_new
        
        iv = iv_new
    
    return None
