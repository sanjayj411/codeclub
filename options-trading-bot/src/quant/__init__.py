import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from scipy import stats
from src.core.logger import logger

class QuantitativeAnalysis:
    """Advanced quantitative analysis for trading decisions"""
    
    @staticmethod
    def calculate_returns(prices: List[float]) -> np.ndarray:
        """Calculate daily returns"""
        prices = np.array(prices)
        returns = np.diff(prices) / prices[:-1]
        return returns
    
    @staticmethod
    def calculate_volatility(prices: List[float], window: int = 20) -> float:
        """
        Calculate historical volatility
        
        Args:
            prices: List of prices
            window: Period for volatility calculation
            
        Returns:
            Annualized volatility
        """
        if len(prices) < window:
            return 0.0
        
        returns = QuantitativeAnalysis.calculate_returns(prices[-window:])
        volatility = np.std(returns)
        annualized_vol = volatility * np.sqrt(252)  # 252 trading days
        
        return float(annualized_vol)
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe Ratio
        
        Args:
            returns: List of returns
            risk_free_rate: Annual risk-free rate (default 2%)
            
        Returns:
            Sharpe ratio
        """
        returns = np.array(returns)
        excess_returns = returns - (risk_free_rate / 252)
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return float(sharpe)
    
    @staticmethod
    def calculate_max_drawdown(prices: List[float]) -> float:
        """
        Calculate maximum drawdown
        
        Args:
            prices: List of prices
            
        Returns:
            Max drawdown as percentage
        """
        prices = np.array(prices)
        cummax = np.maximum.accumulate(prices)
        drawdown = (prices - cummax) / cummax
        max_dd = np.min(drawdown)
        
        return float(max_dd * 100)
    
    @staticmethod
    def calculate_correlation(prices1: List[float], prices2: List[float]) -> float:
        """
        Calculate correlation between two assets
        
        Args:
            prices1: First price series
            prices2: Second price series
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(prices1) != len(prices2):
            min_len = min(len(prices1), len(prices2))
            prices1 = prices1[-min_len:]
            prices2 = prices2[-min_len:]
        
        returns1 = QuantitativeAnalysis.calculate_returns(prices1)
        returns2 = QuantitativeAnalysis.calculate_returns(prices2)
        
        correlation = np.corrcoef(returns1, returns2)[0, 1]
        return float(correlation)
    
    @staticmethod
    def calculate_value_at_risk(returns: List[float], confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR)
        
        Args:
            returns: List of returns
            confidence: Confidence level (default 95%)
            
        Returns:
            VaR value
        """
        var = np.percentile(returns, (1 - confidence) * 100)
        return float(var)
    
    @staticmethod
    def calculate_beta(asset_returns: List[float], market_returns: List[float]) -> float:
        """
        Calculate Beta (systematic risk)
        
        Args:
            asset_returns: Asset return series
            market_returns: Market return series
            
        Returns:
            Beta coefficient
        """
        if len(asset_returns) != len(market_returns):
            min_len = min(len(asset_returns), len(market_returns))
            asset_returns = asset_returns[-min_len:]
            market_returns = market_returns[-min_len:]
        
        asset_returns = np.array(asset_returns)
        market_returns = np.array(market_returns)
        
        covariance = np.cov(asset_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        
        if market_variance == 0:
            return 0.0
        
        beta = covariance / market_variance
        return float(beta)
    
    @staticmethod
    def calculate_alpha(returns: List[float], market_returns: List[float], 
                       risk_free_rate: float = 0.02) -> float:
        """
        Calculate Jensen's Alpha (excess return)
        
        Args:
            returns: Asset returns
            market_returns: Market returns
            risk_free_rate: Risk-free rate
            
        Returns:
            Alpha value
        """
        beta = QuantitativeAnalysis.calculate_beta(returns, market_returns)
        asset_return = np.mean(returns) * 252  # Annualized
        market_return = np.mean(market_returns) * 252
        
        expected_return = risk_free_rate + beta * (market_return - risk_free_rate)
        alpha = asset_return - expected_return
        
        return float(alpha * 100)
    
    @staticmethod
    def regression_analysis(prices: List[float]) -> Dict:
        """
        Perform linear regression on price data
        
        Args:
            prices: List of prices
            
        Returns:
            Regression stats including slope, intercept, R²
        """
        prices = np.array(prices)
        x = np.arange(len(prices))
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, prices)
        
        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_value ** 2),
            'p_value': float(p_value),
            'std_err': float(std_err),
            'trend': 'UP' if slope > 0 else 'DOWN'
        }
    
    @staticmethod
    def monte_carlo_simulation(current_price: float, returns_mean: float, 
                               returns_std: float, days: int = 20, 
                               simulations: int = 1000) -> Dict:
        """
        Run Monte Carlo simulation for price projection
        
        Args:
            current_price: Current price
            returns_mean: Mean daily return
            returns_std: Daily return standard deviation
            days: Number of days to simulate
            simulations: Number of simulations
            
        Returns:
            Probability distribution of future prices
        """
        results = []
        
        for _ in range(simulations):
            price = current_price
            for _ in range(days):
                daily_return = np.random.normal(returns_mean, returns_std)
                price = price * (1 + daily_return)
            results.append(price)
        
        results = np.array(results)
        
        return {
            'mean_price': float(np.mean(results)),
            'std_dev': float(np.std(results)),
            'min_price': float(np.min(results)),
            'max_price': float(np.max(results)),
            'percentile_5': float(np.percentile(results, 5)),
            'percentile_25': float(np.percentile(results, 25)),
            'percentile_75': float(np.percentile(results, 75)),
            'percentile_95': float(np.percentile(results, 95)),
            'prob_up': float(np.sum(results > current_price) / simulations),
            'prob_down': float(np.sum(results < current_price) / simulations)
        }
    
    @staticmethod
    def portfolio_optimization(asset_prices: List[List[float]], 
                              target_return: float = 0.10) -> Dict:
        """
        Optimize portfolio weights using mean-variance optimization
        
        Args:
            asset_prices: List of price series for each asset
            target_return: Target portfolio return
            
        Returns:
            Optimal weights and metrics
        """
        returns_list = [QuantitativeAnalysis.calculate_returns(prices) 
                       for prices in asset_prices]
        returns_array = np.array(returns_list)
        
        mean_returns = np.mean(returns_array, axis=1) * 252
        cov_matrix = np.cov(returns_array) * 252
        
        n_assets = len(asset_prices)
        
        # Equal weight portfolio
        weights = np.array([1/n_assets] * n_assets)
        
        portfolio_return = np.sum(mean_returns * weights)
        portfolio_volatility = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        sharpe_ratio = portfolio_return / portfolio_volatility
        
        return {
            'weights': [float(w) for w in weights],
            'expected_return': float(portfolio_return),
            'volatility': float(portfolio_volatility),
            'sharpe_ratio': float(sharpe_ratio)
        }
