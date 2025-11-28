"""
Options Trading Strategy combining technical analysis, Black-Scholes, and Monte Carlo

Generates options trades based on:
1. Technical signals (RSI, MACD)
2. Black-Scholes pricing and Greeks
3. Monte Carlo simulations for risk/reward analysis
4. Probability-weighted entry/exit decisions
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from src.quant.black_scholes import BlackScholesModel, estimate_volatility_from_prices
from src.quant.monte_carlo import MonteCarloSimulator
from src.indicators.rsi import RSIIndicator
from src.indicators.macd import MACDIndicator
from src.core.logger import logger


@dataclass
class OptionsTrade:
    """Represents an options trading opportunity"""
    symbol: str
    option_type: str  # 'call' or 'put'
    strike_price: float
    expiration_date: datetime
    entry_price: float
    entry_signal_type: str  # 'rsi', 'macd', 'combo'
    
    # Technical analysis
    rsi_value: float
    macd_value: float
    signal_strength: float  # 0-100
    
    # Black-Scholes metrics
    bs_price: float
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float
    
    # Monte Carlo metrics
    prob_itm: float  # Probability in-the-money
    var_95: float   # Value at Risk
    cvar_95: float  # Conditional VaR
    expected_payoff: float
    
    # Position sizing
    contracts_suggested: int
    risk_per_trade: float
    reward_potential: float
    
    # Decision
    confidence_score: float  # 0-100, combination of all factors
    recommendation: str  # 'STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL'


class OptionsStrategy:
    """Options trading strategy with Greeks and Monte Carlo analysis"""
    
    def __init__(
        self,
        account_size: float = 10000,
        max_risk_percent: float = 0.02,
        risk_free_rate: float = 0.05,
        days_to_expiry_range: Tuple[int, int] = (30, 45)
    ):
        """
        Initialize options strategy
        
        Args:
            account_size: Total account capital
            max_risk_percent: Max risk per trade (2%)
            risk_free_rate: Annual risk-free rate
            days_to_expiry_range: Preferred DTE range
        """
        self.account_size = account_size
        self.max_risk_percent = max_risk_percent
        self.max_risk_per_trade = account_size * max_risk_percent
        self.risk_free_rate = risk_free_rate
        self.days_to_expiry_range = days_to_expiry_range
        
        # Technical indicators
        self.rsi = RSIIndicator(period=14)
        self.macd = MACDIndicator(fast=12, slow=26, signal=9)
        
        logger.info(f"Options Strategy initialized: Account=${account_size}, Risk={max_risk_percent*100}%")
    
    def analyze(
        self,
        symbol: str,
        closes: List[float],
        current_price: float,
        strike_price: float,
        days_to_expiry: int,
        option_type: str = 'call',
        num_simulations: int = 5000
    ) -> Optional[OptionsTrade]:
        """
        Analyze options trading opportunity
        
        Args:
            symbol: Stock symbol
            closes: List of recent closing prices (30+ minimum)
            current_price: Current stock price
            strike_price: Option strike price
            days_to_expiry: Days until expiration
            option_type: 'call' or 'put'
            num_simulations: Monte Carlo simulations
            
        Returns:
            OptionsTrade object or None if insufficient data
        """
        if len(closes) < 30:
            logger.warning(f"{symbol}: Insufficient data for analysis ({len(closes)} < 30)")
            return None
        
        # 1. Technical Analysis
        rsi_value = self.rsi.calculate(closes)
        macd_value, signal, histogram = self.macd.calculate(closes)
        signal_type, signal_strength = self._evaluate_technical_signal(
            rsi_value, macd_value, signal, histogram, option_type
        )
        
        if signal_strength == 0:
            logger.info(f"{symbol}: No technical signal")
            return None
        
        # 2. Estimate volatility from historical prices
        volatility = estimate_volatility_from_prices(closes, window=20)
        time_to_expiry = days_to_expiry / 365.0
        
        # 3. Black-Scholes pricing and Greeks
        greeks = BlackScholesModel.calculate_greeks(
            current_price, strike_price, time_to_expiry, volatility, option_type, self.risk_free_rate
        )
        
        # 4. Monte Carlo analysis
        mc_option = MonteCarloSimulator.price_european_option(
            current_price, strike_price, volatility, self.risk_free_rate, days_to_expiry,
            option_type, num_simulations
        )
        
        mc_prob = MonteCarloSimulator.calculate_probability_itm(
            current_price, strike_price, volatility, self.risk_free_rate, days_to_expiry,
            option_type, num_simulations
        )
        
        # 5. Risk analysis (VaR/CVaR)
        max_position_size = int(self.account_size / (greeks['price'] * 100 + 1))
        position_size = max(1, min(max_position_size, 5))  # 1-5 contracts
        
        risk_analysis = MonteCarloSimulator.calculate_var_cvar(
            current_price, strike_price, position_size, option_type,
            volatility, self.risk_free_rate, days_to_expiry, 0.95, num_simulations
        )
        
        # 6. Calculate confidence score (0-100)
        confidence_score = self._calculate_confidence(
            signal_strength, greeks, mc_prob, risk_analysis, option_type
        )
        
        # 7. Determine recommendation
        recommendation = self._get_recommendation(confidence_score, greeks, mc_prob)
        
        # 8. Calculate expected payoff
        expected_payoff = mc_option['option_price'] * position_size * 100
        reward_potential = greeks['delta'] * (current_price * 0.05) * position_size * 100  # 5% move
        
        trade = OptionsTrade(
            symbol=symbol,
            option_type=option_type,
            strike_price=strike_price,
            expiration_date=datetime.now() + timedelta(days=days_to_expiry),
            entry_price=greeks['price'],
            entry_signal_type=signal_type,
            rsi_value=rsi_value,
            macd_value=macd_value,
            signal_strength=signal_strength,
            bs_price=greeks['price'],
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            vega=greeks['vega'],
            theta=greeks['theta'],
            rho=greeks['rho'],
            prob_itm=mc_prob['prob_itm_at_expiry'],
            var_95=risk_analysis['var_95'],
            cvar_95=risk_analysis['cvar_95'],
            expected_payoff=expected_payoff,
            contracts_suggested=position_size,
            risk_per_trade=risk_analysis['var_95'],
            reward_potential=reward_potential,
            confidence_score=confidence_score,
            recommendation=recommendation
        )
        
        logger.info(
            f"{symbol} {option_type.upper()} ${strike_price} "
            f"({days_to_expiry}DTE): {recommendation} "
            f"(conf={confidence_score:.0f}%, prob_itm={mc_prob['prob_itm_at_expiry']:.1%})"
        )
        
        return trade
    
    def _evaluate_technical_signal(
        self,
        rsi: float,
        macd: float,
        signal: float,
        histogram: float,
        option_type: str
    ) -> Tuple[str, float]:
        """
        Evaluate technical signal strength
        
        Returns:
            Tuple of (signal_type, signal_strength 0-100)
        """
        signal_type = 'none'
        strength = 0.0
        
        is_call = option_type.lower() == 'call'
        
        # RSI signals
        rsi_oversold = rsi < 30
        rsi_overbought = rsi > 70
        
        # MACD signals
        macd_bullish = macd > signal and histogram > 0
        macd_bearish = macd < signal and histogram < 0
        
        if is_call:
            # Call: want bullish signals
            if rsi_oversold and macd_bullish:
                signal_type = 'combo'
                strength = 80.0  # Strong buy signal
            elif rsi_oversold:
                signal_type = 'rsi'
                strength = 60.0
            elif macd_bullish:
                signal_type = 'macd'
                strength = 50.0
        else:
            # Put: want bearish signals
            if rsi_overbought and macd_bearish:
                signal_type = 'combo'
                strength = 80.0  # Strong sell signal
            elif rsi_overbought:
                signal_type = 'rsi'
                strength = 60.0
            elif macd_bearish:
                signal_type = 'macd'
                strength = 50.0
        
        return signal_type, strength
    
    def _calculate_confidence(
        self,
        signal_strength: float,
        greeks: Dict,
        mc_prob: Dict,
        risk_analysis: Dict,
        option_type: str
    ) -> float:
        """
        Calculate overall confidence score (0-100)
        
        Combines:
        - Technical signal strength (30%)
        - Probability ITM (40%)
        - Delta appropriateness (20%)
        - Risk/Reward ratio (10%)
        """
        # Signal strength component (0-30)
        signal_component = (signal_strength / 100) * 30
        
        # Probability ITM component (0-40)
        prob_itm = mc_prob['prob_itm_at_expiry']
        # Want 40-70% for good risk/reward
        prob_component = 0
        if 0.40 <= prob_itm <= 0.70:
            prob_component = 40
        elif 0.30 <= prob_itm <= 0.80:
            prob_component = 30
        elif 0.20 <= prob_itm <= 0.90:
            prob_component = 15
        
        # Delta component (0-20)
        delta = greeks['delta']
        if option_type.lower() == 'call':
            # For calls, want 0.3-0.6 delta (not too risky, not too slow)
            if 0.30 <= delta <= 0.60:
                delta_component = 20
            elif 0.20 <= delta <= 0.70:
                delta_component = 15
            else:
                delta_component = 5
        else:
            # For puts, want -0.6 to -0.3 delta
            if -0.60 <= delta <= -0.30:
                delta_component = 20
            elif -0.70 <= delta <= -0.20:
                delta_component = 15
            else:
                delta_component = 5
        
        # Risk/Reward component (0-10)
        var = risk_analysis['var_95']
        cvar = risk_analysis['cvar_95']
        if var > 0 and cvar > 0:
            ratio = min(1.0, 1.0 / (cvar / var))  # Reward/Risk
            reward_component = min(10, ratio * 5)
        else:
            reward_component = 5
        
        total = signal_component + prob_component + delta_component + reward_component
        return min(100, max(0, total))
    
    def _get_recommendation(self, confidence_score: float, greeks: Dict, mc_prob: Dict) -> str:
        """
        Get trading recommendation based on confidence and metrics
        """
        prob_itm = mc_prob['prob_itm_at_expiry']
        
        if confidence_score >= 80 and 0.45 <= prob_itm <= 0.65:
            return 'STRONG_BUY'
        elif confidence_score >= 70 and 0.40 <= prob_itm <= 0.70:
            return 'BUY'
        elif confidence_score >= 60 and 0.30 <= prob_itm <= 0.80:
            return 'HOLD'
        elif confidence_score >= 50 and 0.20 <= prob_itm <= 0.90:
            return 'SELL'
        else:
            return 'STRONG_SELL'
    
    def analyze_strike_ladder(
        self,
        symbol: str,
        closes: List[float],
        current_price: float,
        strikes: List[float],
        days_to_expiry: int,
        option_type: str = 'call'
    ) -> Dict[float, OptionsTrade]:
        """
        Analyze multiple strikes (option chain) for same expiration
        
        Args:
            symbol: Stock symbol
            closes: Historical prices
            current_price: Current price
            strikes: List of strike prices to analyze
            days_to_expiry: Days to expiration
            option_type: 'call' or 'put'
            
        Returns:
            Dictionary mapping strike to OptionsTrade analysis
        """
        results = {}
        
        for strike in strikes:
            trade = self.analyze(
                symbol, closes, current_price, strike, days_to_expiry, option_type
            )
            if trade:
                results[strike] = trade
        
        return results


def format_trade_report(trade: OptionsTrade) -> str:
    """Format options trade analysis as readable report"""
    
    report = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║  OPTIONS TRADE ANALYSIS REPORT                                           ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Symbol: {trade.symbol:<15} Type: {trade.option_type.upper():<10} Recommendation: {trade.recommendation:<15} ║
║  Strike: ${trade.strike_price:<12.2f} Expires: {trade.expiration_date.strftime('%Y-%m-%d'):<15}                    ║
║  Entry Price: ${trade.entry_price:<8.2f} Signal Strength: {trade.signal_strength:.0f}%                         ║
╠══════════════════════════════════════════════════════════════════════════╣
║  TECHNICAL ANALYSIS                                                      ║
║  • RSI: {trade.rsi_value:>6.1f} (Signal: {trade.entry_signal_type}                 ║
║  • MACD: {trade.macd_value:>5.2f}                                              ║
║  • Signal Strength: {trade.signal_strength:.0f}%                                    ║
╠══════════════════════════════════════════════════════════════════════════╣
║  BLACK-SCHOLES GREEKS                                                    ║
║  • Delta: {trade.delta:>7.3f}  (price sensitivity)                       ║
║  • Gamma: {trade.gamma:>7.4f}  (delta acceleration)                      ║
║  • Vega: {trade.vega:>7.3f}   (volatility sensitivity)                  ║
║  • Theta: {trade.theta:>7.4f}  (daily time decay)                        ║
║  • Rho: {trade.rho:>7.3f}    (rate sensitivity)                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║  MONTE CARLO ANALYSIS                                                    ║
║  • Prob ITM: {trade.prob_itm:.1%}                                            ║
║  • Expected Payoff: ${trade.expected_payoff:.2f}                                ║
║  • Reward Potential: ${trade.reward_potential:.2f}                             ║
╠══════════════════════════════════════════════════════════════════════════╣
║  RISK ANALYSIS (95% Confidence)                                          ║
║  • Value at Risk: ${trade.var_95:.2f}                                   ║
║  • Conditional VaR: ${trade.cvar_95:.2f}                                  ║
║  • Risk per Trade: ${trade.risk_per_trade:.2f}                                 ║
╠══════════════════════════════════════════════════════════════════════════╣
║  POSITION SIZING                                                         ║
║  • Suggested Contracts: {trade.contracts_suggested}                                     ║
║  • Confidence Score: {trade.confidence_score:.0f}%                                      ║
║  • Overall Recommendation: {trade.recommendation:<20}          ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    return report
