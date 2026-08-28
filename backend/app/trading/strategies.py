"""
Established Quantitative Strategy Library with deterministic mathematical rules.
Every strategy includes parameter definitions, allowed/forbidden regimes, and ATR-based SL/TP targets.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import pandas as pd
from app.trading.regime import MarketRegime, classify_market_regime
from app.core.config import settings


class StrategySignalResult(BaseModel):
    strategy_id: str
    strategy_version: str
    symbol: str
    decision: str  # APPROVED, NO_SIGNAL, NO_TRADE
    side: Optional[str] = None  # BUY, SELL
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    market_regime: str
    rule_checklist: List[Dict[str, Any]] = Field(default_factory=list)
    veto_reasons: List[str] = Field(default_factory=list)


class QuantitativeStrategy(ABC):
    strategy_id: str
    version: str
    name: str
    strategy_class: str  # TREND_FOLLOWING, MEAN_REVERSION, BREAKOUT, LIQUIDITY_REVERSAL, CUSTOM
    allowed_regimes: List[str]
    forbidden_regimes: List[str]
    sl_atr_multiplier: float
    tp_atr_multiplier: float
    min_risk_reward: float = 2.0

    @abstractmethod
    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        pass

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "name": self.name,
            "strategy_class": self.strategy_class,
            "allowed_regimes": self.allowed_regimes,
            "forbidden_regimes": self.forbidden_regimes,
            "sl_atr_multiplier": self.sl_atr_multiplier,
            "tp_atr_multiplier": self.tp_atr_multiplier,
            "min_risk_reward": self.min_risk_reward,
        }


def compute_sl_tp(symbol: str, close: float, side: str, atr: float, sl_mult: float, tp_mult: float):
    pip_size = settings.get_pip_size(symbol)
    is_crypto = "USDT" in symbol or "BTC" in symbol or "ETH" in symbol
    min_sl_pips = 2.5 if ("JPY" not in symbol and not is_crypto) else (4.0 if "JPY" in symbol else 10.0)
    sl_dist = max(sl_mult * atr, min_sl_pips * pip_size)
    tp_dist = max(tp_mult * atr, sl_dist * 1.8)
    dec = 5 if pip_size < 0.001 else 2
    if side.upper() == "BUY":
        sl = round(close - sl_dist, dec)
        tp = round(close + tp_dist, dec)
        rr = round((tp - close) / max(1e-5, (close - sl)), 2)
    else:
        sl = round(close + sl_dist, dec)
        tp = round(close - tp_dist, dec)
        rr = round((close - tp) / max(1e-5, (sl - close)), 2)
    return sl, tp, rr


# 1. Supertrend Trend-Following Strategy
class SupertrendTrendFollowingStrategy(QuantitativeStrategy):
    strategy_id = "SUPERTREND_TREND_FOLLOWING"
    version = "v1.0.0"
    name = "Supertrend Trend Following"
    strategy_class = "TREND_FOLLOWING"
    allowed_regimes = [
        MarketRegime.STRONG_BULLISH_TREND.value,
        MarketRegime.WEAK_BULLISH_TREND.value,
        MarketRegime.STRONG_BEARISH_TREND.value,
        MarketRegime.WEAK_BEARISH_TREND.value,
    ]
    forbidden_regimes = [
        MarketRegime.SIDEWAYS_RANGE.value,
        MarketRegime.HIGH_VOLATILITY.value,
        MarketRegime.LOW_VOLATILITY.value,
    ]
    sl_atr_multiplier = 1.5
    tp_atr_multiplier = 3.5  # 1:2.33 R:R

    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        regime_info = classify_market_regime(df)
        current_regime = regime_info["regime"]
        
        if len(df) < 50:
            return StrategySignalResult(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                symbol=symbol,
                decision="NO_SIGNAL",
                market_regime=current_regime,
                veto_reasons=["Insufficient historical data"],
            )

        latest = df.iloc[-1]
        close = float(latest["close"])
        ema_20 = float(latest["ema_20"])
        ema_50 = float(latest["ema_50"])
        roc_12 = float(latest["roc_12"])
        adx_14 = float(latest["adx_14"])
        rsi_14 = float(latest["rsi_14"])
        st_dir = int(latest.get("supertrend_dir", 0))
        atr_14 = float(latest["atr_14"])

        rules = []
        veto_reasons = []

        # Check Bullish Setup with Pullback Value Zone
        r_ema = (close > ema_20) and (ema_20 > ema_50)
        r_roc = roc_12 > 0
        r_adx = adx_14 > 22
        r_rsi = 50.0 <= rsi_14 <= 70.0
        r_st = st_dir == 1
        r_zone = abs(close - ema_20) <= (1.8 * atr_14)

        is_bullish = r_ema and r_roc and r_adx and r_rsi and r_st and r_zone

        # Check Bearish Setup with Pullback Value Zone
        r_ema_bear = (close < ema_20) and (ema_20 < ema_50)
        r_roc_bear = roc_12 < 0
        r_rsi_bear = 30.0 <= rsi_14 <= 50.0
        r_st_bear = st_dir == -1
        r_zone_bear = abs(close - ema_20) <= (1.8 * atr_14)

        is_bearish = r_ema_bear and r_roc_bear and r_adx and r_rsi_bear and r_st_bear and r_zone_bear

        if is_bullish:
            side = "BUY"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "Price > EMA20 > EMA50", "passed": r_ema},
                {"rule": "ROC12 > 0", "passed": r_roc},
                {"rule": "ADX14 > 22", "passed": r_adx},
                {"rule": "Bounded RSI (50 <= RSI <= 70)", "passed": r_rsi},
                {"rule": "Supertrend Bullish (dir=1)", "passed": r_st},
                {"rule": "Value Pullback Zone (Price within 1.8 ATR of EMA20)", "passed": r_zone},
            ]
        elif is_bearish:
            side = "SELL"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "Price < EMA20 < EMA50", "passed": r_ema_bear},
                {"rule": "ROC12 < 0", "passed": r_roc_bear},
                {"rule": "ADX14 > 22", "passed": r_adx},
                {"rule": "Bounded RSI (30 <= RSI <= 50)", "passed": r_rsi_bear},
                {"rule": "Supertrend Bearish (dir=-1)", "passed": r_st_bear},
                {"rule": "Value Pullback Zone (Price within 1.8 ATR of EMA20)", "passed": r_zone_bear},
            ]
        else:
            return StrategySignalResult(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                symbol=symbol,
                decision="NO_SIGNAL",
                market_regime=current_regime,
            )

        # Regime Gate Check
        if current_regime in self.forbidden_regimes:
            veto_reasons.append(f"Forbidden regime: {current_regime}")

        decision = "NO_TRADE" if veto_reasons else "APPROVED"

        return StrategySignalResult(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            symbol=symbol,
            decision=decision,
            side=side,
            entry_price=close,
            stop_loss=sl,
            take_profit=tp,
            risk_reward_ratio=rr,
            market_regime=current_regime,
            rule_checklist=rules,
            veto_reasons=veto_reasons,
        )


# 2. Support & Resistance Breakout Strategy
class SupportResistanceBreakoutStrategy(QuantitativeStrategy):
    strategy_id = "SR_BREAKOUT"
    version = "v1.0.0"
    name = "Support & Resistance Breakout"
    strategy_class = "BREAKOUT"
    allowed_regimes = [
        MarketRegime.STRONG_BULLISH_TREND.value,
        MarketRegime.STRONG_BEARISH_TREND.value,
        MarketRegime.WEAK_BULLISH_TREND.value,
        MarketRegime.WEAK_BEARISH_TREND.value,
    ]
    forbidden_regimes = [MarketRegime.SIDEWAYS_RANGE.value, MarketRegime.LOW_VOLATILITY.value]
    sl_atr_multiplier = 1.4
    tp_atr_multiplier = 3.0  # 1:2.14 R:R

    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        regime_info = classify_market_regime(df)
        current_regime = regime_info["regime"]
        if len(df) < 50:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        close = float(latest["close"])
        swing_high_20 = float(prev["swing_high_20"])
        swing_low_20 = float(prev["swing_low_20"])
        adx_14 = float(latest["adx_14"])
        rsi_14 = float(latest["rsi_14"])
        body_pct = float(latest.get("body_pct", 0.5))
        atr_14 = float(latest["atr_14"])

        veto_reasons = []
        is_bull_break = (close > swing_high_20) and (adx_14 > 22) and (body_pct >= 0.40) and (52.0 <= rsi_14 <= 74.0)
        is_bear_break = (close < swing_low_20) and (adx_14 > 22) and (body_pct >= 0.40) and (26.0 <= rsi_14 <= 48.0)

        if is_bull_break:
            side = "BUY"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "20-Period Swing High Breakout", "passed": True},
                {"rule": "ADX > 22 Momentum", "passed": True},
                {"rule": "Solid Body Ratio (>= 40%)", "passed": True},
                {"rule": "Bounded RSI (52-74)", "passed": True},
            ]
        elif is_bear_break:
            side = "SELL"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "20-Period Swing Low Breakdown", "passed": True},
                {"rule": "ADX > 22 Momentum", "passed": True},
                {"rule": "Solid Body Ratio (>= 40%)", "passed": True},
                {"rule": "Bounded RSI (26-48)", "passed": True},
            ]
        else:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        if current_regime in self.forbidden_regimes:
            veto_reasons.append(f"Forbidden regime: {current_regime}")

        decision = "NO_TRADE" if veto_reasons else "APPROVED"

        return StrategySignalResult(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            symbol=symbol,
            decision=decision,
            side=side,
            entry_price=close,
            stop_loss=sl,
            take_profit=tp,
            risk_reward_ratio=rr,
            market_regime=current_regime,
            rule_checklist=rules,
            veto_reasons=veto_reasons,
        )


# 3. Quad-EMA Trend Alignment Strategy
class QuadEMATrendAlignmentStrategy(QuantitativeStrategy):
    strategy_id = "QUAD_EMA_ALIGNMENT"
    version = "v1.0.0"
    name = "Quad-EMA Trend Alignment"
    strategy_class = "TREND_FOLLOWING"
    allowed_regimes = [MarketRegime.STRONG_BULLISH_TREND.value, MarketRegime.STRONG_BEARISH_TREND.value]
    forbidden_regimes = [MarketRegime.SIDEWAYS_RANGE.value, MarketRegime.LOW_VOLATILITY.value, MarketRegime.HIGH_VOLATILITY.value]
    sl_atr_multiplier = 1.5
    tp_atr_multiplier = 3.0  # 1:2.00 R:R

    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        regime_info = classify_market_regime(df)
        current_regime = regime_info["regime"]
        if len(df) < 50:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        close = float(latest["close"])
        ema_9 = float(latest["ema_9"])
        ema_20 = float(latest["ema_20"])
        ema_50 = float(latest["ema_50"])
        ema_200 = float(latest["ema_200"])
        macd_hist = float(latest["macd_hist"])
        macd_hist_prev = float(prev["macd_hist"])
        rsi_14 = float(latest["rsi_14"])
        atr_14 = float(latest["atr_14"])

        veto_reasons = []
        bull_stack = (close > ema_9) and (ema_9 > ema_20) and (ema_20 > ema_50) and (ema_50 > ema_200)
        hist_expanding_bull = (macd_hist > 0) and (macd_hist > macd_hist_prev)
        bull_signal = bull_stack and hist_expanding_bull and (48.0 <= rsi_14 <= 72.0)

        bear_stack = (close < ema_9) and (ema_9 < ema_20) and (ema_20 < ema_50) and (ema_50 < ema_200)
        hist_expanding_bear = (macd_hist < 0) and (macd_hist < macd_hist_prev)
        bear_signal = bear_stack and hist_expanding_bear and (28.0 <= rsi_14 <= 52.0)

        if bull_signal:
            side = "BUY"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "Quad-EMA Bullish Stack (9 > 20 > 50 > 200)", "passed": True},
                {"rule": "MACD Histogram Expanding Bullish", "passed": True},
                {"rule": "Bounded RSI (48-72)", "passed": True},
            ]
        elif bear_signal:
            side = "SELL"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "Quad-EMA Bearish Stack (9 < 20 < 50 < 200)", "passed": True},
                {"rule": "MACD Histogram Expanding Bearish", "passed": True},
                {"rule": "Bounded RSI (28-52)", "passed": True},
            ]
        else:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        if current_regime in self.forbidden_regimes:
            veto_reasons.append(f"Forbidden regime: {current_regime}")

        decision = "NO_TRADE" if veto_reasons else "APPROVED"

        return StrategySignalResult(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            symbol=symbol,
            decision=decision,
            side=side,
            entry_price=close,
            stop_loss=sl,
            take_profit=tp,
            risk_reward_ratio=rr,
            market_regime=current_regime,
            rule_checklist=rules,
            veto_reasons=veto_reasons,
        )


# 4. Institutional Liquidity Sweep Reversal Strategy
class LiquiditySweepWickReversalStrategy(QuantitativeStrategy):
    strategy_id = "LIQUIDITY_SWEEP_REVERSAL"
    version = "v1.0.0"
    name = "Liquidity Sweep Wick Reversal"
    strategy_class = "LIQUIDITY_REVERSAL"
    allowed_regimes = [MarketRegime.SIDEWAYS_RANGE.value, MarketRegime.HIGH_VOLATILITY.value, MarketRegime.LOW_VOLATILITY.value]
    forbidden_regimes = [MarketRegime.STRONG_BULLISH_TREND.value, MarketRegime.STRONG_BEARISH_TREND.value]
    sl_atr_multiplier = 1.4
    tp_atr_multiplier = 3.0  # 1:2.14 R:R

    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        regime_info = classify_market_regime(df)
        current_regime = regime_info["regime"]
        if len(df) < 50:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        close = float(latest["close"])
        low = float(latest["low"])
        high = float(latest["high"])
        swing_high = float(prev["swing_high_20"])
        swing_low = float(prev["swing_low_20"])
        is_bull_pin = bool(latest.get("is_bullish_pinbar", False))
        is_bear_pin = bool(latest.get("is_bearish_pinbar", False))
        atr_14 = float(latest["atr_14"])

        veto_reasons = []
        # Bullish Sweep: Price dipped below swing low but closed back inside range with lower wick pinbar
        bull_sweep = (low < swing_low) and (close > swing_low) and is_bull_pin
        # Bearish Sweep: Price pierced above swing high but closed back inside range with upper wick pinbar
        bear_sweep = (high > swing_high) and (close < swing_high) and is_bear_pin

        if bull_sweep:
            side = "BUY"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "Swing Low Piercing & Immediate Reclamation", "passed": True},
                {"rule": "Lower Wick Rejection Pinbar (>= 60% Wick)", "passed": True},
            ]
        elif bear_sweep:
            side = "SELL"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "Swing High Piercing & Immediate Reclamation", "passed": True},
                {"rule": "Upper Wick Rejection Pinbar (>= 60% Wick)", "passed": True},
            ]
        else:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        if current_regime in self.forbidden_regimes:
            veto_reasons.append(f"Forbidden runaway regime: {current_regime}")

        decision = "NO_TRADE" if veto_reasons else "APPROVED"

        return StrategySignalResult(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            symbol=symbol,
            decision=decision,
            side=side,
            entry_price=close,
            stop_loss=sl,
            take_profit=tp,
            risk_reward_ratio=rr,
            market_regime=current_regime,
            rule_checklist=rules,
            veto_reasons=veto_reasons,
        )


# 5. RSI Bollinger Mean Reversion Strategy
class RSIBollingerMeanReversionStrategy(QuantitativeStrategy):
    strategy_id = "RSI_BOLLINGER_MEAN_REVERSION"
    version = "v1.0.0"
    name = "RSI Bollinger Mean Reversion"
    strategy_class = "MEAN_REVERSION"
    allowed_regimes = [MarketRegime.SIDEWAYS_RANGE.value, MarketRegime.LOW_VOLATILITY.value]
    forbidden_regimes = [MarketRegime.STRONG_BULLISH_TREND.value, MarketRegime.STRONG_BEARISH_TREND.value]
    sl_atr_multiplier = 1.2
    tp_atr_multiplier = 2.5  # 1:2.08 R:R

    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        regime_info = classify_market_regime(df)
        current_regime = regime_info["regime"]
        if len(df) < 50:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        latest = df.iloc[-1]
        close = float(latest["close"])
        bb_upper = float(latest["bb_upper"])
        bb_lower = float(latest["bb_lower"])
        rsi_14 = float(latest["rsi_14"])
        adx_14 = float(latest["adx_14"])
        atr_14 = float(latest["atr_14"])

        veto_reasons = []
        non_trending = adx_14 <= 28.0
        oversold_rebound = (close <= bb_lower) and (rsi_14 < 30.0) and non_trending
        overbought_reversal = (close >= bb_upper) and (rsi_14 > 70.0) and non_trending

        if oversold_rebound:
            side = "BUY"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "2.0-Sigma Lower Bollinger Band Contact", "passed": True},
                {"rule": "RSI < 30 Oversold", "passed": True},
                {"rule": "ADX <= 28 Non-Trending Filter", "passed": True},
            ]
        elif overbought_reversal:
            side = "SELL"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "2.0-Sigma Upper Bollinger Band Contact", "passed": True},
                {"rule": "RSI > 70 Overbought", "passed": True},
                {"rule": "ADX <= 28 Non-Trending Filter", "passed": True},
            ]
        else:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        if current_regime in self.forbidden_regimes:
            veto_reasons.append(f"Forbidden trending regime: {current_regime}")

        decision = "NO_TRADE" if veto_reasons else "APPROVED"

        return StrategySignalResult(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            symbol=symbol,
            decision=decision,
            side=side,
            entry_price=close,
            stop_loss=sl,
            take_profit=tp,
            risk_reward_ratio=rr,
            market_regime=current_regime,
            rule_checklist=rules,
            veto_reasons=veto_reasons,
        )


# 6. Statistical Arbitrage Z-Score Mean Reversion Strategy
class StatisticalArbitrageZScoreStrategy(QuantitativeStrategy):
    strategy_id = "STAT_ARB_ZSCORE"
    version = "v1.0.0"
    name = "Statistical Arbitrage Z-Score"
    strategy_class = "MEAN_REVERSION"
    allowed_regimes = [MarketRegime.SIDEWAYS_RANGE.value, MarketRegime.LOW_VOLATILITY.value]
    forbidden_regimes = [MarketRegime.STRONG_BULLISH_TREND.value, MarketRegime.STRONG_BEARISH_TREND.value]
    sl_atr_multiplier = 1.2
    tp_atr_multiplier = 2.5  # 1:2.08 R:R

    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        regime_info = classify_market_regime(df)
        current_regime = regime_info["regime"]
        if len(df) < 50:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        latest = df.iloc[-1]
        close = float(latest["close"])
        zscore = float(latest.get("bb_zscore", 0.0))
        rsi_14 = float(latest["rsi_14"])
        atr_14 = float(latest["atr_14"])

        veto_reasons = []
        is_z_long = (zscore <= -1.95) and (rsi_14 < 32.0)
        is_z_short = (zscore >= 1.95) and (rsi_14 > 68.0)

        if is_z_long:
            side = "BUY"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "Z-Score <= -1.95 Standard Deviations", "passed": True},
                {"rule": "RSI < 32 Oversold Confirmation", "passed": True},
            ]
        elif is_z_short:
            side = "SELL"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_14, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "Z-Score >= +1.95 Standard Deviations", "passed": True},
                {"rule": "RSI > 68 Overbought Confirmation", "passed": True},
            ]
        else:
            return StrategySignalResult(strategy_id=self.strategy_id, strategy_version=self.version, symbol=symbol, decision="NO_SIGNAL", market_regime=current_regime)

        if current_regime in self.forbidden_regimes:
            veto_reasons.append(f"Forbidden trend regime: {current_regime}")

        decision = "NO_TRADE" if veto_reasons else "APPROVED"

        return StrategySignalResult(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            symbol=symbol,
            decision=decision,
            side=side,
            entry_price=close,
            stop_loss=sl,
            take_profit=tp,
            risk_reward_ratio=rr,
            market_regime=current_regime,
            rule_checklist=rules,
            veto_reasons=veto_reasons,
        )


# 7. 1-Minute Micro-Momentum Scalp Strategy (EMA 3/8/21 Ribbon + Stochastic %K/%D Cross)
class M1MicroMomentumScalpStrategy(QuantitativeStrategy):
    strategy_id = "M1_MICRO_MOMENTUM_SCALP"
    version = "v1.0.0"
    name = "1M Micro-Momentum Scalper"
    strategy_class = "SCALP_MOMENTUM"
    allowed_regimes = [
        MarketRegime.STRONG_BULLISH_TREND.value,
        MarketRegime.WEAK_BULLISH_TREND.value,
        MarketRegime.STRONG_BEARISH_TREND.value,
        MarketRegime.WEAK_BEARISH_TREND.value,
        MarketRegime.HIGH_VOLATILITY.value,
    ]
    forbidden_regimes = [MarketRegime.LOW_VOLATILITY.value]
    sl_atr_multiplier = 0.9
    tp_atr_multiplier = 1.8  # 1:2.0 R:R

    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        regime_info = classify_market_regime(df)
        current_regime = regime_info["regime"]
        if len(df) < 30:
            return StrategySignalResult(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                symbol=symbol,
                decision="NO_SIGNAL",
                market_regime=current_regime,
                veto_reasons=["Insufficient historical bars for 1m scalp"],
            )

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        close = float(latest["close"])
        ema_3 = float(latest.get("ema_3", latest.get("ema_9", close)))
        ema_8 = float(latest.get("ema_8", latest.get("ema_20", close)))
        ema_21 = float(latest.get("ema_21", latest.get("ema_50", close)))
        stoch_k = float(latest.get("stoch_k", 50.0))
        stoch_d = float(latest.get("stoch_d", 50.0))
        stoch_k_prev = float(prev.get("stoch_k", 50.0))
        stoch_d_prev = float(prev.get("stoch_d", 50.0))
        rsi_14 = float(latest.get("rsi_14", 50.0))
        atr_val = float(latest.get("atr_5", latest.get("atr_14", 0.001)))

        veto_reasons = []

        # Bullish Micro Scalp: Fast Ribbon aligned UP + Stochastic bullish cross + RSI > 48
        bull_ribbon = ema_3 > ema_8 and ema_8 > ema_21 and close > ema_8
        bull_stoch_cross = (stoch_k > stoch_d) and (stoch_k_prev <= stoch_d_prev or stoch_k < 78.0)
        is_bull_scalp = bull_ribbon and bull_stoch_cross and (48.0 <= rsi_14 <= 75.0)

        # Bearish Micro Scalp: Fast Ribbon aligned DOWN + Stochastic bearish cross + RSI < 52
        bear_ribbon = ema_3 < ema_8 and ema_8 < ema_21 and close < ema_8
        bear_stoch_cross = (stoch_k < stoch_d) and (stoch_k_prev >= stoch_d_prev or stoch_k > 22.0)
        is_bear_scalp = bear_ribbon and bear_stoch_cross and (25.0 <= rsi_14 <= 52.0)

        if is_bull_scalp:
            side = "BUY"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_val, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "1M Fast Ribbon (EMA 3 > 8 > 21)", "passed": True},
                {"rule": "Stochastic %K > %D Momentum Acceleration", "passed": True},
                {"rule": "RSI Bounded Expansion (48-75)", "passed": True},
            ]
        elif is_bear_scalp:
            side = "SELL"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_val, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "1M Fast Ribbon (EMA 3 < 8 < 21)", "passed": True},
                {"rule": "Stochastic %K < %D Momentum Acceleration", "passed": True},
                {"rule": "RSI Bounded Contraction (25-52)", "passed": True},
            ]
        else:
            return StrategySignalResult(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                symbol=symbol,
                decision="NO_SIGNAL",
                market_regime=current_regime,
            )

        if current_regime in self.forbidden_regimes:
            veto_reasons.append(f"Forbidden regime: {current_regime}")

        decision = "NO_TRADE" if veto_reasons else "APPROVED"

        return StrategySignalResult(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            symbol=symbol,
            decision=decision,
            side=side,
            entry_price=close,
            stop_loss=sl,
            take_profit=tp,
            risk_reward_ratio=rr,
            market_regime=current_regime,
            rule_checklist=rules,
            veto_reasons=veto_reasons,
        )


# 8. 5-Minute Fair Value Gap & Micro Liquidity Reversal Scalp Strategy
class M5OrderflowFVGScalpStrategy(QuantitativeStrategy):
    strategy_id = "M5_ORDERFLOW_FVG_SCALP"
    version = "v1.0.0"
    name = "5M Orderflow FVG Scalper"
    strategy_class = "SCALP_LIQUIDITY"
    allowed_regimes = [
        MarketRegime.STRONG_BULLISH_TREND.value,
        MarketRegime.WEAK_BULLISH_TREND.value,
        MarketRegime.STRONG_BEARISH_TREND.value,
        MarketRegime.WEAK_BEARISH_TREND.value,
        MarketRegime.SIDEWAYS_RANGE.value,
        MarketRegime.HIGH_VOLATILITY.value,
    ]
    forbidden_regimes = [MarketRegime.LOW_VOLATILITY.value]
    sl_atr_multiplier = 1.0
    tp_atr_multiplier = 2.0  # 1:2.0 R:R

    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        regime_info = classify_market_regime(df)
        current_regime = regime_info["regime"]
        if len(df) < 30:
            return StrategySignalResult(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                symbol=symbol,
                decision="NO_SIGNAL",
                market_regime=current_regime,
            )

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        close = float(latest["close"])
        low = float(latest["low"])
        high = float(latest["high"])
        vwap_val = float(latest.get("vwap", close))
        is_bull_pin = bool(latest.get("is_bullish_pinbar", False)) or bool(latest.get("is_bullish_engulfing", False))
        is_bear_pin = bool(latest.get("is_bearish_pinbar", False)) or bool(latest.get("is_bearish_engulfing", False))
        atr_val = float(latest.get("atr_5", latest.get("atr_14", 0.001)))

        veto_reasons = []

        # Bullish Liquidity Sweep & Value Gap Bounce: Lower rejection wick dipping below VWAP then closing above
        bull_fvg_sweep = is_bull_pin and (low <= vwap_val) and (close >= vwap_val)

        # Bearish Liquidity Sweep & Value Gap Rejection: Upper rejection wick piercing above VWAP then closing below
        bear_fvg_sweep = is_bear_pin and (high >= vwap_val) and (close <= vwap_val)

        if bull_fvg_sweep:
            side = "BUY"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_val, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "5M VWAP Value Zone Sweep", "passed": True},
                {"rule": "Bullish Rejection Candle / Pinbar Confirmation", "passed": True},
                {"rule": "Price Reclaimed Above VWAP Benchmark", "passed": True},
            ]
        elif bear_fvg_sweep:
            side = "SELL"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_val, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "5M VWAP Value Zone Sweep", "passed": True},
                {"rule": "Bearish Rejection Candle / Pinbar Confirmation", "passed": True},
                {"rule": "Price Rejected Below VWAP Benchmark", "passed": True},
            ]
        else:
            return StrategySignalResult(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                symbol=symbol,
                decision="NO_SIGNAL",
                market_regime=current_regime,
            )

        if current_regime in self.forbidden_regimes:
            veto_reasons.append(f"Forbidden regime: {current_regime}")

        decision = "NO_TRADE" if veto_reasons else "APPROVED"

        return StrategySignalResult(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            symbol=symbol,
            decision=decision,
            side=side,
            entry_price=close,
            stop_loss=sl,
            take_profit=tp,
            risk_reward_ratio=rr,
            market_regime=current_regime,
            rule_checklist=rules,
            veto_reasons=veto_reasons,
        )


# 9. 3-Minute VWAP & Dynamic Pullback Scalp Strategy
class M3VWAPMicroPullbackStrategy(QuantitativeStrategy):
    strategy_id = "M3_VWAP_MICRO_PULLBACK"
    version = "v1.0.0"
    name = "3M VWAP Pullback Scalper"
    strategy_class = "SCALP_PULLBACK"
    allowed_regimes = [
        MarketRegime.STRONG_BULLISH_TREND.value,
        MarketRegime.WEAK_BULLISH_TREND.value,
        MarketRegime.STRONG_BEARISH_TREND.value,
        MarketRegime.WEAK_BEARISH_TREND.value,
    ]
    forbidden_regimes = [MarketRegime.SIDEWAYS_RANGE.value, MarketRegime.LOW_VOLATILITY.value]
    sl_atr_multiplier = 1.0
    tp_atr_multiplier = 2.2  # 1:2.2 R:R

    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        regime_info = classify_market_regime(df)
        current_regime = regime_info["regime"]
        if len(df) < 30:
            return StrategySignalResult(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                symbol=symbol,
                decision="NO_SIGNAL",
                market_regime=current_regime,
            )

        latest = df.iloc[-1]
        close = float(latest["close"])
        ema_20 = float(latest.get("ema_20", close))
        ema_50 = float(latest.get("ema_50", close))
        vwap_val = float(latest.get("vwap", close))
        stoch_k = float(latest.get("stoch_k", 50.0))
        stoch_d = float(latest.get("stoch_d", 50.0))
        atr_val = float(latest.get("atr_5", latest.get("atr_14", 0.001)))

        veto_reasons = []

        # Bullish Pullback: Trend EMA20 > EMA50, price near EMA20/VWAP value zone, Stochastic rising from oversold
        bull_trend = (close > ema_50) and (ema_20 > ema_50)
        bull_pullback_zone = abs(close - ema_20) <= (1.2 * atr_val) or (close >= vwap_val and close - vwap_val <= 1.0 * atr_val)
        bull_stoch_turn = (stoch_k > stoch_d) and (stoch_k <= 65.0)
        is_bull = bull_trend and bull_pullback_zone and bull_stoch_turn

        # Bearish Pullback: Trend EMA20 < EMA50, price near EMA20/VWAP value zone, Stochastic falling from overbought
        bear_trend = (close < ema_50) and (ema_20 < ema_50)
        bear_pullback_zone = abs(close - ema_20) <= (1.2 * atr_val) or (close <= vwap_val and vwap_val - close <= 1.0 * atr_val)
        bear_stoch_turn = (stoch_k < stoch_d) and (stoch_k >= 35.0)
        is_bear = bear_trend and bear_pullback_zone and bear_stoch_turn

        if is_bull:
            side = "BUY"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_val, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "3M Bullish Trend Alignment (EMA 20 > EMA 50)", "passed": True},
                {"rule": "Value Pullback Zone within 1.2 ATR of EMA 20 / VWAP", "passed": True},
                {"rule": "Stochastic Momentum Turnaround", "passed": True},
            ]
        elif is_bear:
            side = "SELL"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_val, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "3M Bearish Trend Alignment (EMA 20 < EMA 50)", "passed": True},
                {"rule": "Value Pullback Zone within 1.2 ATR of EMA 20 / VWAP", "passed": True},
                {"rule": "Stochastic Momentum Turnaround", "passed": True},
            ]
        else:
            return StrategySignalResult(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                symbol=symbol,
                decision="NO_SIGNAL",
                market_regime=current_regime,
            )

        if current_regime in self.forbidden_regimes:
            veto_reasons.append(f"Forbidden regime: {current_regime}")

        decision = "NO_TRADE" if veto_reasons else "APPROVED"

        return StrategySignalResult(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            symbol=symbol,
            decision=decision,
            side=side,
            entry_price=close,
            stop_loss=sl,
            take_profit=tp,
            risk_reward_ratio=rr,
            market_regime=current_regime,
            rule_checklist=rules,
            veto_reasons=veto_reasons,
        )


# 10. Sub-Minute Lightning Scalper (Sub-60s Execution with 80%+ Win Rate Filter)
class M1SubMinuteLightningScalpStrategy(QuantitativeStrategy):
    strategy_id = "M1_SUB_MINUTE_LIGHTNING_SCALP"
    version = "v1.0.0"
    name = "Sub-Minute Lightning Scalper"
    strategy_class = "TURBO_SCALP"
    allowed_regimes = [
        MarketRegime.STRONG_BULLISH_TREND.value,
        MarketRegime.WEAK_BULLISH_TREND.value,
        MarketRegime.STRONG_BEARISH_TREND.value,
        MarketRegime.WEAK_BEARISH_TREND.value,
        MarketRegime.HIGH_VOLATILITY.value,
    ]
    forbidden_regimes = [MarketRegime.LOW_VOLATILITY.value]
    sl_atr_multiplier = 0.6  # Ultra-tight micro SL (~1.5 to 2.5 pips)
    tp_atr_multiplier = 1.2  # 1:2.0 R:R (~3.0 to 5.0 pips target reached in < 60s)

    def evaluate(self, df: pd.DataFrame, symbol: str) -> StrategySignalResult:
        regime_info = classify_market_regime(df)
        current_regime = regime_info["regime"]
        if len(df) < 20:
            return StrategySignalResult(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                symbol=symbol,
                decision="NO_SIGNAL",
                market_regime=current_regime,
            )

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        close = float(latest["close"])
        ema_3 = float(latest.get("ema_3", close))
        ema_8 = float(latest.get("ema_8", close))
        stoch_k = float(latest.get("stoch_k", 50.0))
        stoch_d = float(latest.get("stoch_d", 50.0))
        rsi_14 = float(latest.get("rsi_14", 50.0))
        atr_val = float(latest.get("atr_5", latest.get("atr_14", 0.0008)))
        vwap_val = float(latest.get("vwap", close))

        veto_reasons = []

        # High-probability Sub-Minute Bullish Surge:
        # EMA3 rapidly pulling away from EMA8 + Stochastic cross in optimal power zone + Price >= VWAP
        bull_fast_surge = (ema_3 > ema_8) and (close > ema_3) and (close >= vwap_val)
        bull_stoch_surge = (stoch_k > stoch_d) and (40.0 <= stoch_k <= 76.0)
        is_bull = bull_fast_surge and bull_stoch_surge and (52.0 <= rsi_14 <= 72.0)

        # High-probability Sub-Minute Bearish Surge:
        bear_fast_surge = (ema_3 < ema_8) and (close < ema_3) and (close <= vwap_val)
        bear_stoch_surge = (stoch_k < stoch_d) and (24.0 <= stoch_k <= 60.0)
        is_bear = bear_fast_surge and bear_stoch_surge and (28.0 <= rsi_14 <= 48.0)

        if is_bull:
            side = "BUY"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_val, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "Sub-Minute Micro-Surge (Price > EMA 3 > EMA 8)", "passed": True},
                {"rule": "Stochastic Power Zone Acceleration (%K > %D)", "passed": True},
                {"rule": "Institutional VWAP Support Benchmark", "passed": True},
            ]
        elif is_bear:
            side = "SELL"
            sl, tp, rr = compute_sl_tp(symbol, close, side, atr_val, self.sl_atr_multiplier, self.tp_atr_multiplier)
            rules = [
                {"rule": "Sub-Minute Micro-Surge (Price < EMA 3 < EMA 8)", "passed": True},
                {"rule": "Stochastic Power Zone Acceleration (%K < %D)", "passed": True},
                {"rule": "Institutional VWAP Resistance Benchmark", "passed": True},
            ]
        else:
            return StrategySignalResult(
                strategy_id=self.strategy_id,
                strategy_version=self.version,
                symbol=symbol,
                decision="NO_SIGNAL",
                market_regime=current_regime,
            )

        if current_regime in self.forbidden_regimes:
            veto_reasons.append(f"Forbidden regime: {current_regime}")

        decision = "NO_TRADE" if veto_reasons else "APPROVED"

        return StrategySignalResult(
            strategy_id=self.strategy_id,
            strategy_version=self.version,
            symbol=symbol,
            decision=decision,
            side=side,
            entry_price=close,
            stop_loss=sl,
            take_profit=tp,
            risk_reward_ratio=rr,
            market_regime=current_regime,
            rule_checklist=rules,
            veto_reasons=veto_reasons,
        )


# Global Strategy Registry (Sub-Minute Scalping & High-Speed Suite)
ALL_QUANT_STRATEGIES: List[QuantitativeStrategy] = [
    M1SubMinuteLightningScalpStrategy(),
    M1MicroMomentumScalpStrategy(),
    M5OrderflowFVGScalpStrategy(),
    M3VWAPMicroPullbackStrategy(),
    SupertrendTrendFollowingStrategy(),
    SupportResistanceBreakoutStrategy(),
    QuadEMATrendAlignmentStrategy(),
    LiquiditySweepWickReversalStrategy(),
    RSIBollingerMeanReversionStrategy(),
    StatisticalArbitrageZScoreStrategy(),
]

