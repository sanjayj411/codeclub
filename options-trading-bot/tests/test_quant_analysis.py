import pytest
from src.quant import QuantitativeAnalysis
import numpy as np

class TestQuantAnalysis:
    
    def test_volatility_calculation(self):
        """Test volatility calculation"""
        prices = list(range(100, 120)) + list(range(120, 80, -1))
        vol = QuantitativeAnalysis.calculate_volatility(prices, window=20)
        
        assert vol >= 0
        assert vol < 2  # Reasonable volatility range
    
    def test_sharpe_ratio(self):
        """Test Sharpe ratio calculation"""
        prices = [100 + np.sin(x) * 5 for x in range(100)]
        returns = QuantitativeAnalysis.calculate_returns(prices)
        sharpe = QuantitativeAnalysis.calculate_sharpe_ratio(returns)
        
        assert isinstance(sharpe, float)
    
    def test_max_drawdown(self):
        """Test max drawdown calculation"""
        prices = [100, 110, 120, 90, 100, 110, 100]
        max_dd = QuantitativeAnalysis.calculate_max_drawdown(prices)
        
        assert max_dd < 0  # Drawdown should be negative
        assert max_dd > -100  # Should be percentage
    
    def test_correlation(self):
        """Test correlation calculation"""
        prices1 = [100, 101, 102, 101, 100, 99, 98, 97, 96, 95]
        prices2 = [50, 51, 52, 51, 50, 49, 48, 47, 46, 45]
        
        corr = QuantitativeAnalysis.calculate_correlation(prices1, prices2)
        
        assert -1 <= corr <= 1
        assert corr > 0.9  # Should be highly correlated
    
    def test_value_at_risk(self):
        """Test VaR calculation"""
        returns = np.random.normal(0.001, 0.02, 100).tolist()
        var = QuantitativeAnalysis.calculate_value_at_risk(returns, confidence=0.95)
        
        assert isinstance(var, float)
    
    def test_beta_calculation(self):
        """Test beta calculation"""
        asset_returns = [0.01, 0.02, -0.01, 0.015, 0.02]
        market_returns = [0.005, 0.01, -0.005, 0.01, 0.015]
        
        beta = QuantitativeAnalysis.calculate_beta(asset_returns, market_returns)
        
        assert isinstance(beta, float)
    
    def test_alpha_calculation(self):
        """Test alpha calculation"""
        returns = [0.01, 0.02, -0.01, 0.015, 0.02]
        market_returns = [0.005, 0.01, -0.005, 0.01, 0.015]
        
        alpha = QuantitativeAnalysis.calculate_alpha(returns, market_returns)
        
        assert isinstance(alpha, float)
    
    def test_regression_analysis(self):
        """Test regression analysis"""
        prices = [100, 101, 102, 103, 104, 105]
        regression = QuantitativeAnalysis.regression_analysis(prices)
        
        assert 'slope' in regression
        assert 'intercept' in regression
        assert 'r_squared' in regression
        assert regression['trend'] in ['UP', 'DOWN']
    
    def test_monte_carlo_simulation(self):
        """Test Monte Carlo simulation"""
        mc = QuantitativeAnalysis.monte_carlo_simulation(
            current_price=100,
            returns_mean=0.001,
            returns_std=0.02,
            days=20,
            simulations=100
        )
        
        assert 'mean_price' in mc
        assert 'std_dev' in mc
        assert 'prob_up' in mc
        assert 'prob_down' in mc
        assert mc['prob_up'] + mc['prob_down'] <= 1.01  # Allow small floating point error
    
    def test_portfolio_optimization(self):
        """Test portfolio optimization"""
        prices1 = [100 + np.sin(x/10) * 5 for x in range(50)]
        prices2 = [50 + np.cos(x/10) * 2 for x in range(50)]
        
        optimization = QuantitativeAnalysis.portfolio_optimization([prices1, prices2])
        
        assert 'weights' in optimization
        assert 'expected_return' in optimization
        assert 'volatility' in optimization
        assert len(optimization['weights']) == 2
        assert abs(sum(optimization['weights']) - 1.0) < 0.01
