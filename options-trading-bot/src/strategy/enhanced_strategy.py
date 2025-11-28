"""
Enhanced Stock Trading Strategy with Bollinger Bands, RSI, MACD, and Options Integration

Signal generation:
1. Technical: RSI + MACD + Bollinger Bands convergence
2. When stock BUY triggered: Analyze options for call opportunities
3. Returns both stock and options trading signals
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from src.indicators.rsi import RSIIndicator
from src.indicators.macd import MACDIndicator
from src.indicators.bollinger_bands import BollingerBandsIndicator
from src.quant.black_scholes import BlackScholesModel, estimate_volatility_from_prices
from src.quant.monte_carlo import MonteCarloSimulator
from src.core.logger import logger


@dataclass
class StockSignal:
    """Stock trading signal with technical indicators"""
    symbol: str
    action: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0-100
    price: float
    timestamp: datetime
    
    # Technical metrics
    rsi: float
    macd: float
    macd_signal: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_position: str  # 'upper', 'middle', 'lower'
    bb_percent_b: float
    
    # Combined signal strength
    signal_type: str  # 'rsi_oversold', 'macd_bullish', 'bb_bounce', 'combo'
    reason: str


@dataclass
class OptionsOpportunity:
    """Options trading opportunity triggered by stock signal"""
    symbol: str
    option_type: str  # 'call' or 'put'
    strike_price: float
    days_to_expiry: int
    entry_price: float
    
    # Analysis
    delta: float
    gamma: float
    vega: float
    theta: float
    prob_itm: float
    
    # Risk metrics
    var_95: float
    cvar_95: float
    
    # Recommendation
    recommendation: str  # 'BUY', 'HOLD', 'SKIP'
    confidence: float  # 0-100
    contracts_suggested: int


class EnhancedStockStrategy:
    """Enhanced stock strategy with technical analysis and options integration"""
    
    def __init__(
        self,
        rsi_period: int = 14,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bb_period: int = 20,
        bb_std_dev: float = 2.0,
        min_drawdown_for_buy: float = 2.0
    ):
        """
        Initialize enhanced strategy
        
        Args:
            rsi_period: RSI period
            rsi_oversold: RSI oversold threshold
            rsi_overbought: RSI overbought threshold
            macd_fast/slow/signal: MACD periods
            bb_period: Bollinger Bands period
            bb_std_dev: Bollinger Bands std dev multiplier
            min_drawdown_for_buy: Min drawdown % for buy signal
        """
        self.rsi = RSIIndicator(rsi_period)
        self.macd = MACDIndicator(macd_fast, macd_slow, macd_signal)
        self.bb = BollingerBandsIndicator(bb_period, bb_std_dev)
        
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.min_drawdown_for_buy = min_drawdown_for_buy
        
        # Track previous values
        self.prev_rsi = None
        self.prev_macd = None
        self.prev_signal = None
    
    def analyze_stock(
        self,
        symbol: str,
        closes: List[float],
        current_price: float
    ) -> Optional[StockSignal]:
        """
        Analyze stock and generate trading signal
        
        Args:
            symbol: Stock symbol
            closes: List of closing prices (30+)
            current_price: Current market price
            
        Returns:
            StockSignal or None
        """
        if len(closes) < 30:
            logger.warning(f"{symbol}: Insufficient data ({len(closes)} < 30)")
            return None
        
        # Calculate indicators
        rsi = self.rsi.calculate(closes)
        macd, signal, histogram = self.macd.calculate(closes)
        bb = self.bb.calculate(closes)
        
        if rsi is None or macd is None or signal is None or histogram is None or bb is None:
            return None
        
        # Determine signal
        action, confidence, signal_type, reason = self._evaluate_signal(
            rsi, macd, signal, histogram, bb, closes
        )
        
        if action == 'HOLD':
            return None
        
        signal = StockSignal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            price=current_price,
            timestamp=datetime.now(),
            rsi=rsi,
            macd=macd,
            macd_signal=signal,
            bb_upper=bb['upper'],
            bb_middle=bb['middle'],
            bb_lower=bb['lower'],
            bb_position=self.bb.get_band_position(closes),
            bb_percent_b=bb['percent_b'],
            signal_type=signal_type,
            reason=reason
        )
        
        logger.info(
            f"{symbol}: {action} signal (conf={confidence:.0f}%, "
            f"RSI={rsi:.1f}, BB={self.bb.get_band_position(closes)}, type={signal_type})"
        )
        
        return signal
    
    def _evaluate_signal(
        self,
        rsi: float,
        macd: float,
        signal: float,
        histogram: float,
        bb: Dict,
        closes: List[float]
    ) -> Tuple[str, float, str, str]:
        """
        Evaluate combined technical signal
        
        Returns:
            (action, confidence, signal_type, reason)
        """
        bb_position = self.bb.get_band_position(closes)
        current_price = closes[-1]
        
        # 1. RSI-based signals
        rsi_oversold = rsi < self.rsi_oversold
        rsi_overbought = rsi > self.rsi_overbought
        
        # 2. MACD-based signals
        macd_bullish = macd > signal and histogram > 0
        macd_bearish = macd < signal and histogram < 0
        
        # 3. Bollinger Bands signals
        bb_at_lower = bb_position == 'lower'
        bb_at_upper = bb_position == 'upper'
        
        # 4. Drawdown filter
        recent_high = max(closes[-20:]) if len(closes) >= 20 else current_price
        drawdown_pct = ((recent_high - current_price) / recent_high) * 100 if recent_high > 0 else 0
        has_drawdown = drawdown_pct >= self.min_drawdown_for_buy
        
        # BULLISH signals
        # Strong: All three bullish + drawdown
        if rsi_oversold and macd_bullish and bb_at_lower and has_drawdown:
            return 'BUY', 95.0, 'combo_strong', \
                f"RSI oversold + MACD bullish + BB lower bounce + {drawdown_pct:.1f}% drawdown"
        
        # Strong: Two or more bullish + drawdown
        bullish_count = sum([rsi_oversold, macd_bullish, bb_at_lower])
        if bullish_count >= 2 and has_drawdown:
            return 'BUY', 80.0, 'combo', \
                f"Multiple bullish signals + {drawdown_pct:.1f}% drawdown"
        
        # Moderate: Any two bullish signals
        if bullish_count >= 2:
            return 'BUY', 65.0, f'bb_rsi' if bb_at_lower and rsi_oversold else 'macd_rsi', \
                f"{bullish_count} bullish signals converging"
        
        # Single strong signal
        if rsi_oversold and has_drawdown:
            return 'BUY', 60.0, 'rsi_oversold', \
                f"RSI oversold ({rsi:.1f}) + {drawdown_pct:.1f}% drawdown"
        
        if macd_bullish and bb_at_lower:
            return 'BUY', 60.0, 'macd_bb', \
                f"MACD bullish crossover at lower Bollinger Band"
        
        # BEARISH signals
        if rsi_overbought and macd_bearish and bb_at_upper:
            return 'SELL', 90.0, 'combo_strong', \
                f"RSI overbought + MACD bearish + BB upper limit"
        
        bearish_count = sum([rsi_overbought, macd_bearish, bb_at_upper])
        if bearish_count >= 2:
            return 'SELL', 75.0, 'combo', \
                f"{bearish_count} bearish signals converging"
        
        if rsi_overbought:
            return 'SELL', 60.0, 'rsi_overbought', \
                f"RSI overbought ({rsi:.1f})"
        
        return 'HOLD', 0.0, 'none', 'No clear signal'
    
    def analyze_options_for_stock_signal(
        self,
        stock_signal: StockSignal,
        closes: List[float],
        current_price: float,
        days_to_expiry: int = 30,
        num_simulations: int = 5000,
        account_size: float = 50000
    ) -> Optional[OptionsOpportunity]:
        """
        When stock signal generated, analyze options for trading
        
        Args:
            stock_signal: The stock signal that triggered this analysis
            closes: Historical prices
            current_price: Current stock price
            days_to_expiry: Days to options expiration
            num_simulations: Monte Carlo simulations
            account_size: Account size for position sizing
            
        Returns:
            OptionsOpportunity or None
        """
        if stock_signal.action != 'BUY':
            return None  # Only trade calls on BUY signals
        
        # Estimate volatility
        volatility = estimate_volatility_from_prices(closes, window=20)
        time_to_expiry = days_to_expiry / 365.0
        
        # Select strike: 30 days ATM or slightly OTM for better risk/reward
        # Prefer 0.3-0.5 delta (30-50% probability ITM)
        strike_price = self._select_call_strike(
            current_price, closes, volatility, time_to_expiry, days_to_expiry
        )
        
        if strike_price is None:
            return None
        
        # Black-Scholes analysis
        greeks = BlackScholesModel.calculate_greeks(
            current_price, strike_price, time_to_expiry, volatility, 'call'
        )
        
        # Monte Carlo analysis
        mc_option = MonteCarloSimulator.price_european_option(
            current_price, strike_price, volatility, 0.05, days_to_expiry, 'call', num_simulations
        )
        
        mc_prob = MonteCarloSimulator.calculate_probability_itm(
            current_price, strike_price, volatility, 0.05, days_to_expiry, 'call', num_simulations
        )
        
        # Position sizing
        max_risk_per_trade = account_size * 0.02  # 2% risk
        position_size = max(1, int(max_risk_per_trade / (greeks['price'] * 100)))
        
        # VaR analysis
        var_result = MonteCarloSimulator.calculate_var_cvar(
            current_price, strike_price, position_size, 'call',
            volatility, 0.05, days_to_expiry, 0.95, num_simulations
        )
        
        # Confidence scoring
        confidence = self._score_options_confidence(
            stock_signal.confidence, greeks, mc_prob, var_result
        )
        
        # Recommendation
        recommendation = 'BUY' if confidence >= 70 and 0.40 <= mc_prob['prob_itm_at_expiry'] <= 0.70 else 'HOLD'
        
        options_opp = OptionsOpportunity(
            symbol=stock_signal.symbol,
            option_type='call',
            strike_price=strike_price,
            days_to_expiry=days_to_expiry,
            entry_price=greeks['price'],
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            vega=greeks['vega'],
            theta=greeks['theta'],
            prob_itm=mc_prob['prob_itm_at_expiry'],
            var_95=var_result['var_95'],
            cvar_95=var_result['cvar_95'],
            recommendation=recommendation,
            confidence=confidence,
            contracts_suggested=position_size
        )
        
        logger.info(
            f"{stock_signal.symbol} Call ${strike_price:.2f}: "
            f"{recommendation} (conf={confidence:.0f}%, delta={greeks['delta']:.3f})"
        )
        
        return options_opp
    
    def _select_call_strike(
        self,
        current_price: float,
        closes: List[float],
        volatility: float,
        time_to_expiry: float,
        days_to_expiry: int
    ) -> Optional[float]:
        """
        Select optimal call strike for options trade
        
        Prefer 0.3-0.5 delta (30-50% ITM probability)
        """
        # Generate candidate strikes
        candidates = [
            current_price,  # ATM
            current_price * 1.01,  # 1% OTM
            current_price * 1.02,  # 2% OTM
            current_price * 1.025,  # 2.5% OTM
        ]
        
        best_strike = None
        best_delta = None
        target_delta = 0.40  # Target 40% ITM
        
        for strike in candidates:
            delta = BlackScholesModel.delta(current_price, strike, time_to_expiry, volatility, 'call')
            
            # Find strike closest to target delta
            if best_delta is None or abs(delta - target_delta) < abs(best_delta - target_delta):
                best_strike = strike
                best_delta = delta
        
        return best_strike
    
    def _score_options_confidence(
        self,
        stock_confidence: float,
        greeks: Dict,
        mc_prob: Dict,
        var_result: Dict
    ) -> float:
        """
        Score options trade confidence (0-100)
        
        Combines:
        - Stock signal confidence (40%)
        - Delta appropriateness (30%)
        - Probability ITM (20%)
        - Risk/Reward (10%)
        """
        # Stock signal component
        stock_component = (stock_confidence / 100) * 40
        
        # Delta component (want 0.3-0.5)
        delta = greeks['delta']
        delta_component = 0
        if 0.30 <= delta <= 0.50:
            delta_component = 30
        elif 0.25 <= delta <= 0.55:
            delta_component = 25
        elif 0.20 <= delta <= 0.60:
            delta_component = 15
        
        # Probability component (want 40-60% ITM)
        prob_itm = mc_prob['prob_itm_at_expiry']
        prob_component = 0
        if 0.40 <= prob_itm <= 0.60:
            prob_component = 20
        elif 0.35 <= prob_itm <= 0.65:
            prob_component = 15
        elif 0.30 <= prob_itm <= 0.70:
            prob_component = 10
        
        # Risk/Reward component
        var_risk = var_result['var_95']
        best_gain = var_result['best_gain']
        reward_component = min(10, (best_gain / var_risk) * 5) if var_risk > 0 else 5
        
        total = stock_component + delta_component + prob_component + reward_component
        return min(100, max(0, total))


def format_stock_signal(signal: StockSignal) -> str:
    """Format stock signal as readable report"""
    return f"""
╔═══════════════════════════════════════════════════════════╗
║  STOCK SIGNAL: {signal.symbol} - {signal.action}
║  Confidence: {signal.confidence:.0f}%
║  Signal Type: {signal.signal_type}
║  Price: ${signal.price:.2f}
╠═══════════════════════════════════════════════════════════╣
║  TECHNICAL ANALYSIS
║  RSI: {signal.rsi:.1f} ({"Oversold" if signal.rsi < 30 else "Overbought" if signal.rsi > 70 else "Neutral"})
║  MACD: {signal.macd:.4f}
║  BB Position: {signal.bb_position.upper()} (%.B: {signal.bb_percent_b:.1%})
║  
║  Reason: {signal.reason}
╚═══════════════════════════════════════════════════════════╝
"""


def format_options_opportunity(opp: OptionsOpportunity) -> str:
    """Format options opportunity as readable report"""
    return f"""
╔═══════════════════════════════════════════════════════════╗
║  OPTIONS OPPORTUNITY: {opp.symbol} ${opp.strike_price:.2f} CALL
║  Recommendation: {opp.recommendation}
║  Confidence: {opp.confidence:.0f}%
║  Entry Price: ${opp.entry_price:.2f}
╠═══════════════════════════════════════════════════════════╣
║  GREEKS & RISK
║  Delta: {opp.delta:.3f} | Gamma: {opp.gamma:.4f}
║  Vega: {opp.vega:.3f} | Theta: {opp.theta:.4f}
║  Prob ITM: {opp.prob_itm:.1%}
║  VaR(95%): ${opp.var_95:.2f} | CVaR: ${opp.cvar_95:.2f}
║  
║  Position Size: {opp.contracts_suggested} contracts
╚═══════════════════════════════════════════════════════════╝
"""
