"""
Test suite for Black-Scholes and Monte Carlo options pricing
"""

import pytest
from datetime import datetime, timedelta
import math
from src.quant.black_scholes import BlackScholesModel, estimate_volatility_from_prices
from src.quant.monte_carlo import MonteCarloSimulator
from src.strategy.options_strategy import OptionsStrategy, format_trade_report


class TestBlackScholes:
    """Test Black-Scholes pricing model"""
    
    def test_call_put_parity(self):
        """Verify put-call parity: C - P = S - K*e^(-rT)"""
        spot = 100
        strike = 100
        time = 0.25  # 3 months
        vol = 0.20
        rate = 0.05
        
        call = BlackScholesModel.call_price(spot, strike, time, vol, rate)
        put = BlackScholesModel.put_price(spot, strike, time, vol, rate)
        
        lhs = call - put
        rhs = spot - strike * math.exp(-rate * time)
        
        assert abs(lhs - rhs) < 0.01, "Put-call parity violated"
        print(f"✓ Put-call parity: {lhs:.4f} ≈ {rhs:.4f}")
    
    def test_atm_call_price(self):
        """Test ATM call pricing (should be reasonable)"""
        spot = 100
        strike = 100
        time = 0.25
        vol = 0.20
        
        price = BlackScholesModel.call_price(spot, strike, time, vol)
        
        # Rough estimate: ATM call ≈ 0.4 * spot * vol * sqrt(time)
        estimate = 0.4 * spot * vol * math.sqrt(time)
        
        assert 1.5 < price < 3.5, f"ATM call price {price} outside expected range"
        print(f"✓ ATM call price: ${price:.2f} (est: ${estimate:.2f})")
    
    def test_delta(self):
        """Test Delta values"""
        spot = 100
        strike = 100
        time = 0.25
        vol = 0.20
        
        call_delta = BlackScholesModel.delta(spot, strike, time, vol, 'call')
        put_delta = BlackScholesModel.delta(spot, strike, time, vol, 'put')
        
        # ATM call delta ≈ 0.5, ATM put delta ≈ -0.5
        assert 0.45 < call_delta < 0.55, f"Call delta {call_delta} not near 0.5"
        assert -0.55 < put_delta < -0.45, f"Put delta {put_delta} not near -0.5"
        
        # Delta sum for same strike should be approximately -1
        assert abs(call_delta - put_delta - 1.0) < 0.1
        print(f"✓ Delta: Call={call_delta:.3f}, Put={put_delta:.3f}")
    
    def test_gamma(self):
        """Test Gamma (all gamma should be positive)"""
        spot = 100
        strike = 100
        time = 0.25
        vol = 0.20
        
        gamma = BlackScholesModel.gamma(spot, strike, time, vol)
        
        assert gamma > 0, "Gamma must be positive"
        assert gamma < 0.1, "Gamma seems too high"
        print(f"✓ Gamma: {gamma:.4f}")
    
    def test_vega(self):
        """Test Vega (higher vol should increase option price)"""
        spot = 100
        strike = 100
        time = 0.25
        vol_low = 0.10
        vol_high = 0.30
        
        price_low = BlackScholesModel.call_price(spot, strike, time, vol_low)
        price_high = BlackScholesModel.call_price(spot, strike, time, vol_high)
        
        assert price_high > price_low, "Higher vol should increase option price"
        
        vega = BlackScholesModel.vega(spot, strike, time, vol_low)
        assert vega > 0, "Vega should be positive"
        print(f"✓ Vega: {vega:.3f}, Price difference: ${price_high-price_low:.2f}")
    
    def test_theta(self):
        """Test Theta (time decay)"""
        spot = 100
        strike = 100
        time_long = 0.25
        time_short = 0.05
        vol = 0.20
        
        price_long = BlackScholesModel.call_price(spot, strike, time_long, vol)
        price_short = BlackScholesModel.call_price(spot, strike, time_short, vol)
        
        # Less time should mean lower price for OTM call
        assert price_long > price_short, "Longer dated should be more valuable"
        
        theta = BlackScholesModel.theta(spot, strike, time_short, vol, 'call')
        print(f"✓ Theta (5 days to expiry): {theta:.4f} per day")


class TestMonteCarloSimulation:
    """Test Monte Carlo simulation"""
    
    def test_price_paths_generation(self):
        """Test price path generation"""
        paths = MonteCarloSimulator.simulate_price_paths(
            spot_price=100,
            volatility=0.20,
            risk_free_rate=0.05,
            time_steps=252,
            num_simulations=100,
            days_to_expiry=365
        )
        
        assert len(paths) == 100, "Should generate 100 paths"
        assert all(len(path) == 253 for path in paths), "Each path should have 253 steps"
        
        # Check that prices are reasonable
        all_final_prices = [path[-1] for path in paths]
        avg_final = sum(all_final_prices) / len(all_final_prices)
        
        # On average, should grow by ~5% (risk-free rate)
        expected_growth = 100 * math.exp(0.05 * 1.0)
        
        assert 80 < avg_final < 120, f"Final price {avg_final} outside expected range"
        print(f"✓ Path generation: {len(paths)} paths, avg final: ${avg_final:.2f}")
    
    def test_european_option_pricing(self):
        """Test European option pricing via Monte Carlo"""
        mc_result = MonteCarloSimulator.price_european_option(
            spot_price=100,
            strike_price=100,
            volatility=0.20,
            risk_free_rate=0.05,
            days_to_expiry=30,
            option_type='call',
            num_simulations=5000
        )
        
        assert 'option_price' in mc_result
        assert mc_result['option_price'] > 0, "Option price should be positive"
        assert mc_result['std_error'] > 0, "Std error should be positive"
        assert mc_result['ci_lower'] >= 0, "CI lower should be >= 0"
        assert mc_result['ci_upper'] > mc_result['ci_lower'], "CI should be valid"
        
        print(f"✓ MC option price: ${mc_result['option_price']:.2f} ± ${mc_result['std_error']:.2f}")
    
    def test_probability_itm(self):
        """Test ITM probability calculation"""
        result = MonteCarloSimulator.calculate_probability_itm(
            spot_price=100,
            strike_price=105,  # OTM call
            volatility=0.20,
            risk_free_rate=0.05,
            days_to_expiry=30,
            option_type='call',
            num_simulations=5000
        )
        
        assert 0 <= result['prob_itm_at_expiry'] <= 1, "Probability must be 0-1"
        assert result['prob_itm_at_expiry'] > 0, "OTM call has some ITM probability"
        assert result['prob_itm_at_expiry'] < 0.5, "OTM call should have <50% ITM prob"
        
        print(f"✓ Prob ITM: {result['prob_itm_at_expiry']:.1%}")
    
    def test_var_cvar(self):
        """Test VaR and CVaR calculations"""
        result = MonteCarloSimulator.calculate_var_cvar(
            spot_price=100,
            strike_price=100,
            position_size=5,
            option_type='call',
            volatility=0.20,
            risk_free_rate=0.05,
            days_to_expiry=30,
            num_simulations=5000
        )
        
        assert result['var_95'] >= 0, "VaR should be non-negative"
        assert result['cvar_95'] >= result['var_95'], "CVaR should be >= VaR"
        assert result['worst_loss'] >= result['var_95'], "Worst loss should be >= VaR"
        
        print(f"✓ Risk metrics - VaR: ${result['var_95']:.2f}, CVaR: ${result['cvar_95']:.2f}")
    
    def test_asian_option_vs_european(self):
        """Test Asian option (should have lower price than European)"""
        european = MonteCarloSimulator.price_european_option(
            spot_price=100,
            strike_price=100,
            volatility=0.20,
            risk_free_rate=0.05,
            days_to_expiry=30,
            option_type='call',
            num_simulations=5000
        )
        
        asian = MonteCarloSimulator.price_asian_option(
            spot_price=100,
            strike_price=100,
            volatility=0.20,
            risk_free_rate=0.05,
            days_to_expiry=30,
            option_type='call',
            num_simulations=5000
        )
        
        # Asian should be cheaper due to lower volatility of average
        assert asian['option_price'] <= european['option_price'], \
            "Asian option should be cheaper than European"
        
        print(f"✓ Asian (${asian['option_price']:.2f}) <= European (${european['option_price']:.2f})")


class TestOptionsStrategy:
    """Test integrated options strategy"""
    
    def test_strategy_initialization(self):
        """Test strategy initialization"""
        strat = OptionsStrategy(account_size=50000, max_risk_percent=0.02)
        
        assert strat.account_size == 50000
        assert strat.max_risk_percent == 0.02
        assert strat.max_risk_per_trade == 1000
        print("✓ Strategy initialized")
    
    def test_analyze_call_opportunity(self):
        """Test call option analysis"""
        strat = OptionsStrategy()
        
        # Generate synthetic price data (downtrend then bounce = RSI oversold)
        closes = [100 - i*0.5 for i in range(30)] + [95 + i*0.3 for i in range(10)]
        closes.reverse()  # Oldest to newest
        
        trade = strat.analyze(
            symbol='AAPL',
            closes=closes,
            current_price=99,
            strike_price=100,
            days_to_expiry=30,
            option_type='call',
            num_simulations=2000
        )
        
        if trade:
            assert trade.symbol == 'AAPL'
            assert trade.option_type == 'call'
            assert trade.bs_price > 0
            assert 0 <= trade.prob_itm <= 1
            assert -1 <= trade.delta <= 1
            print(f"✓ Call analysis: {trade.recommendation} (conf: {trade.confidence_score:.0f}%)")
    
    def test_strike_ladder_analysis(self):
        """Test analyzing multiple strikes"""
        strat = OptionsStrategy()
        
        # Generate synthetic data
        closes = [100 - math.sin(i/10)*5 + (i*0.1) for i in range(30)]
        
        results = strat.analyze_strike_ladder(
            symbol='SPY',
            closes=closes,
            current_price=102,
            strikes=[100, 102.5, 105, 107.5, 110],
            days_to_expiry=30,
            option_type='call'
        )
        
        assert len(results) > 0, "Should analyze at least some strikes"
        print(f"✓ Strike ladder: analyzed {len(results)} strikes")


class TestVolatilityEstimation:
    """Test volatility estimation"""
    
    def test_estimate_volatility(self):
        """Test historical volatility estimation"""
        # Generate prices with known volatility
        import random
        random.seed(42)
        
        prices = [100]
        for _ in range(100):
            daily_return = random.gauss(0.0005, 0.01)  # ~10% annual vol
            prices.append(prices[-1] * (1 + daily_return))
        
        vol = estimate_volatility_from_prices(prices, window=20)
        
        # Should be in reasonable range (actual ~10%)
        assert 0.05 < vol < 0.30, f"Volatility {vol:.1%} seems wrong"
        print(f"✓ Estimated volatility: {vol:.1%}")


if __name__ == '__main__':
    print("Running options pricing tests...\n")
    
    # Black-Scholes tests
    print("=" * 50)
    print("BLACK-SCHOLES TESTS")
    print("=" * 50)
    test_bs = TestBlackScholes()
    test_bs.test_call_put_parity()
    test_bs.test_atm_call_price()
    test_bs.test_delta()
    test_bs.test_gamma()
    test_bs.test_vega()
    test_bs.test_theta()
    
    # Monte Carlo tests
    print("\n" + "=" * 50)
    print("MONTE CARLO TESTS")
    print("=" * 50)
    test_mc = TestMonteCarloSimulation()
    test_mc.test_price_paths_generation()
    test_mc.test_european_option_pricing()
    test_mc.test_probability_itm()
    test_mc.test_var_cvar()
    test_mc.test_asian_option_vs_european()
    
    # Options strategy tests
    print("\n" + "=" * 50)
    print("OPTIONS STRATEGY TESTS")
    print("=" * 50)
    test_strat = TestOptionsStrategy()
    test_strat.test_strategy_initialization()
    test_strat.test_analyze_call_opportunity()
    test_strat.test_strike_ladder_analysis()
    
    # Volatility tests
    print("\n" + "=" * 50)
    print("VOLATILITY TESTS")
    print("=" * 50)
    test_vol = TestVolatilityEstimation()
    test_vol.test_estimate_volatility()
    
    print("\n✓ All tests passed!")
