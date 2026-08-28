"""
Deterministic Market Regime Classifier using ADX, Bollinger Bands, and EMA stacks.
"""
from enum import Enum
from typing import Dict, Any, Tuple
import pandas as pd


class MarketRegime(str, Enum):
    STRONG_BULLISH_TREND = "STRONG_BULLISH_TREND"
    WEAK_BULLISH_TREND = "WEAK_BULLISH_TREND"
    SIDEWAYS_RANGE = "SIDEWAYS_RANGE"
    WEAK_BEARISH_TREND = "WEAK_BEARISH_TREND"
    STRONG_BEARISH_TREND = "STRONG_BEARISH_TREND"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"


def classify_market_regime(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Deterministically classifies market regime from the latest candle in an enriched DataFrame.
    """
    if df.empty or len(df) < 50:
        return {
            "regime": MarketRegime.SIDEWAYS_RANGE.value,
            "adx": 20.0,
            "bb_width": 2.0,
            "trend_score": 0.0,
            "description": "Insufficient historical bars; defaulting to Sideways Range.",
        }

    latest = df.iloc[-1]
    adx_val = float(latest.get("adx_14", 20.0))
    plus_di = float(latest.get("plus_di", 20.0))
    minus_di = float(latest.get("minus_di", 20.0))
    bb_width = float(latest.get("bb_width", 2.0))
    close = float(latest.get("close", 1.0))
    ema_20 = float(latest.get("ema_20", close))
    ema_50 = float(latest.get("ema_50", close))
    ema_200 = float(latest.get("ema_200", close))

    # Trend alignment check
    bullish_stack = (close > ema_20) and (ema_20 > ema_50) and (ema_50 > ema_200)
    bearish_stack = (close < ema_20) and (ema_20 < ema_50) and (ema_50 < ema_200)

    # Volatility bounds
    rolling_bb_width_mean = df["bb_width"].tail(50).mean() if "bb_width" in df else bb_width
    is_high_volatility = bb_width > (rolling_bb_width_mean * 1.6)
    is_low_volatility = bb_width < (rolling_bb_width_mean * 0.5)

    if is_high_volatility and adx_val < 25:
        regime = MarketRegime.HIGH_VOLATILITY
        desc = "High volatility expansion without clear directional trend."
    elif adx_val >= 28 and bullish_stack and plus_di > minus_di:
        regime = MarketRegime.STRONG_BULLISH_TREND
        desc = f"Strong Bullish Trend confirmed (ADX={adx_val:.1f}, Quad-EMA Stack aligned)."
    elif adx_val >= 28 and bearish_stack and minus_di > plus_di:
        regime = MarketRegime.STRONG_BEARISH_TREND
        desc = f"Strong Bearish Trend confirmed (ADX={adx_val:.1f}, Quad-EMA Stack aligned)."
    elif adx_val >= 20 and close > ema_50:
        regime = MarketRegime.WEAK_BULLISH_TREND
        desc = f"Moderate Bullish bias (ADX={adx_val:.1f}, Price > EMA 50)."
    elif adx_val >= 20 and close < ema_50:
        regime = MarketRegime.WEAK_BEARISH_TREND
        desc = f"Moderate Bearish bias (ADX={adx_val:.1f}, Price < EMA 50)."
    elif is_low_volatility:
        regime = MarketRegime.LOW_VOLATILITY
        desc = "Low volatility compression / consolidation zone."
    else:
        regime = MarketRegime.SIDEWAYS_RANGE
        desc = f"Sideways Range consolidation (ADX={adx_val:.1f} <= 20)."

    return {
        "regime": regime.value,
        "adx": round(adx_val, 2),
        "bb_width": round(bb_width, 2),
        "is_trending": adx_val >= 22,
        "description": desc,
    }
