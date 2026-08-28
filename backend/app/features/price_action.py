"""
Vectorized price action, candlestick geometry, and swing high/low detection.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict


def swing_highs_lows(df: pd.DataFrame, window: int = 5) -> Tuple[pd.Series, pd.Series]:
    """
    Detects local swing highs and swing lows over a rolling window.
    Returns: (is_swing_high, is_swing_low)
    """
    high = df["high"]
    low = df["low"]
    
    rolling_max = high.rolling(window=2 * window + 1, center=True).max()
    rolling_min = low.rolling(window=2 * window + 1, center=True).min()
    
    is_high = (high == rolling_max)
    is_low = (low == rolling_min)
    
    return is_high.fillna(False), is_low.fillna(False)


def candle_geometry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates body size, upper wick, lower wick, and their ratios relative to total candle range.
    """
    open_p = df["open"]
    close = df["close"]
    high = df["high"]
    low = df["low"]
    
    total_range = (high - low).replace(0, 1e-6)
    body_size = (close - open_p).abs()
    upper_wick = high - pd.concat([open_p, close], axis=1).max(axis=1)
    lower_wick = pd.concat([open_p, close], axis=1).min(axis=1) - low
    
    res = pd.DataFrame(index=df.index)
    res["body_pct"] = body_size / total_range
    res["upper_wick_pct"] = upper_wick / total_range
    res["lower_wick_pct"] = lower_wick / total_range
    res["is_bullish"] = close >= open_p
    res["is_bearish"] = close < open_p
    return res


def detect_pinbars(df: pd.DataFrame, min_wick_pct: float = 0.60, max_body_pct: float = 0.30) -> Tuple[pd.Series, pd.Series]:
    """
    Detects bullish and bearish pinbars (long wick rejection).
    Returns: (is_bullish_pinbar, is_bearish_pinbar)
    """
    geom = candle_geometry(df)
    
    bullish_pinbar = (geom["lower_wick_pct"] >= min_wick_pct) & (geom["body_pct"] <= max_body_pct)
    bearish_pinbar = (geom["upper_wick_pct"] >= min_wick_pct) & (geom["body_pct"] <= max_body_pct)
    
    return bullish_pinbar, bearish_pinbar


def detect_engulfing(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    Detects Bullish and Bearish Engulfing candle pairs.
    Returns: (is_bullish_engulfing, is_bearish_engulfing)
    """
    open_curr = df["open"]
    close_curr = df["close"]
    open_prev = df["open"].shift(1)
    close_prev = df["close"].shift(1)
    
    # Bullish Engulfing: Prior candle bearish, current candle bullish and engulfs prior body
    bull_engulf = (
        (close_prev < open_prev) &
        (close_curr > open_curr) &
        (open_curr <= close_prev) &
        (close_curr >= open_prev)
    )
    
    # Bearish Engulfing: Prior candle bullish, current candle bearish and engulfs prior body
    bear_engulf = (
        (close_prev > open_prev) &
        (close_curr < open_curr) &
        (open_curr >= close_prev) &
        (close_curr <= open_prev)
    )
    
    return bull_engulf.fillna(False), bear_engulf.fillna(False)
