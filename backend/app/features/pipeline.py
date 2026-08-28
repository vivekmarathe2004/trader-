"""
Unified feature computation pipeline enriching raw OHLCV DataFrames.
"""
import pandas as pd
from app.features.indicators import (
    ema, sma, rsi, atr, macd, bollinger_bands, adx, rate_of_change, supertrend,
    stochastic_oscillator, vwap, fast_atr
)
from app.features.price_action import (
    swing_highs_lows, candle_geometry, detect_pinbars, detect_engulfing
)


def compute_indicator_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    and appends all vectorized technical indicators and price action features.
    """
    if df.empty:
        return df

    res = df.copy()
    close = res["close"]

    # Fast Micro Scalping Moving Averages
    res["ema_3"] = ema(close, 3)
    res["ema_8"] = ema(close, 8)
    res["ema_9"] = ema(close, 9)
    res["ema_20"] = ema(close, 20)
    res["ema_21"] = ema(close, 21)
    res["ema_50"] = ema(close, 50)
    res["ema_200"] = ema(close, 200)
    res["sma_20"] = sma(close, 20)
    res["sma_50"] = sma(close, 50)

    # Momentum & Micro-Volatility
    res["rsi_14"] = rsi(close, 14)
    res["atr_5"] = fast_atr(res, 5)
    res["atr_14"] = atr(res, 14)
    res["roc_12"] = rate_of_change(close, 12)

    # Micro-Momentum Stochastic Oscillator (%K, %D)
    stoch_k, stoch_d = stochastic_oscillator(res, k_period=14, d_period=3, smooth_k=3)
    res["stoch_k"] = stoch_k
    res["stoch_d"] = stoch_d

    # Volume-Weighted Benchmark (VWAP)
    res["vwap"] = vwap(res)

    # MACD
    macd_line, macd_sig, macd_hist = macd(close, 12, 26, 9)
    res["macd_line"] = macd_line
    res["macd_signal"] = macd_sig
    res["macd_hist"] = macd_hist

    # Bollinger Bands
    bb_upper, bb_mid, bb_lower, bb_width, bb_zscore = bollinger_bands(close, 20, 2.0)
    res["bb_upper"] = bb_upper
    res["bb_middle"] = bb_mid
    res["bb_lower"] = bb_lower
    res["bb_width"] = bb_width
    res["bb_zscore"] = bb_zscore

    # ADX Directional System
    adx_val, plus_di, minus_di = adx(res, 14)
    res["adx_14"] = adx_val
    res["plus_di"] = plus_di
    res["minus_di"] = minus_di

    # Supertrend
    st_val, st_dir = supertrend(res, 10, 3.0)
    res["supertrend"] = st_val
    res["supertrend_dir"] = st_dir

    # Price Action & Geometry
    is_sh, is_sl = swing_highs_lows(res, 5)
    res["is_swing_high"] = is_sh
    res["is_swing_low"] = is_sl

    geom = candle_geometry(res)
    res["body_pct"] = geom["body_pct"]
    res["upper_wick_pct"] = geom["upper_wick_pct"]
    res["lower_wick_pct"] = geom["lower_wick_pct"]

    bull_pin, bear_pin = detect_pinbars(res)
    res["is_bullish_pinbar"] = bull_pin
    res["is_bearish_pinbar"] = bear_pin

    bull_eng, bear_eng = detect_engulfing(res)
    res["is_bullish_engulfing"] = bull_eng
    res["is_bearish_engulfing"] = bear_eng

    # Rolling Swing High / Low over 20 bars
    res["swing_high_20"] = res["high"].rolling(window=20).max()
    res["swing_low_20"] = res["low"].rolling(window=20).min()

    return res
