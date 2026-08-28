"""
Candlestick pattern detection engine with geometric validation.
"""
from typing import Dict, List, Any
import pandas as pd


def detect_candlestick_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detects classic candlestick patterns on the latest bars of an enriched DataFrame.
    """
    if len(df) < 5:
        return []

    patterns = []
    latest = df.iloc[-1]
    prev1 = df.iloc[-2]
    prev2 = df.iloc[-3]

    open_0, high_0, low_0, close_0 = float(latest["open"]), float(latest["high"]), float(latest["low"]), float(latest["close"])
    open_1, high_1, low_1, close_1 = float(prev1["open"]), float(prev1["high"]), float(prev1["low"]), float(prev1["close"])
    open_2, high_2, low_2, close_2 = float(prev2["open"]), float(prev2["high"]), float(prev2["low"]), float(prev2["close"])

    range_0 = max(high_0 - low_0, 1e-6)
    body_0 = abs(close_0 - open_0)
    upper_wick_0 = high_0 - max(open_0, close_0)
    lower_wick_0 = min(open_0, close_0) - low_0

    # 1. Hammer (Bullish Reversal)
    if (lower_wick_0 >= 0.60 * range_0) and (body_0 <= 0.30 * range_0) and (upper_wick_0 <= 0.15 * range_0):
        patterns.append({
            "pattern": "Hammer",
            "bias": "BULLISH",
            "reliability": "HIGH",
            "description": "Long lower wick rejection (>=60% candle range) indicating strong institutional buying absorption.",
        })

    # 2. Shooting Star (Bearish Reversal)
    if (upper_wick_0 >= 0.60 * range_0) and (body_0 <= 0.30 * range_0) and (lower_wick_0 <= 0.15 * range_0):
        patterns.append({
            "pattern": "Shooting Star",
            "bias": "BEARISH",
            "reliability": "HIGH",
            "description": "Long upper wick rejection (>=60% candle range) indicating severe overhead liquidity resistance.",
        })

    # 3. Bullish Engulfing
    if bool(latest.get("is_bullish_engulfing", False)):
        patterns.append({
            "pattern": "Bullish Engulfing",
            "bias": "BULLISH",
            "reliability": "VERY_HIGH",
            "description": "Large bullish candle body completely engulfs prior bearish body.",
        })

    # 4. Bearish Engulfing
    if bool(latest.get("is_bearish_engulfing", False)):
        patterns.append({
            "pattern": "Bearish Engulfing",
            "bias": "BEARISH",
            "reliability": "VERY_HIGH",
            "description": "Large bearish candle body completely engulfs prior bullish body.",
        })

    # 5. Morning Star (3-candle bullish reversal)
    if (close_2 < open_2) and (abs(close_1 - open_1) < 0.3 * (high_1 - low_1)) and (close_0 > open_0) and (close_0 > (open_2 + close_2) / 2):
        patterns.append({
            "pattern": "Morning Star",
            "bias": "BULLISH",
            "reliability": "VERY_HIGH",
            "description": "Three-candle bullish morning star reversal with midpoint penetration.",
        })

    # 6. Evening Star (3-candle bearish reversal)
    if (close_2 > open_2) and (abs(close_1 - open_1) < 0.3 * (high_1 - low_1)) and (close_0 < open_0) and (close_0 < (open_2 + close_2) / 2):
        patterns.append({
            "pattern": "Evening Star",
            "bias": "BEARISH",
            "reliability": "VERY_HIGH",
            "description": "Three-candle bearish evening star reversal with midpoint penetration.",
        })

    return patterns
