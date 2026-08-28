"""
Vectorized technical indicators computed with NumPy and Pandas.
"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder's RSI)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss.replace(0, np.nan))
    rsi_val = 100.0 - (100.0 / (1.0 + rs))
    return rsi_val.fillna(50.0)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean().bfill()


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Moving Average Convergence Divergence."""
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands.
    Returns: (upper_band, middle_band, lower_band, bandwidth, zscore)
    """
    mid = sma(series, period)
    std = series.rolling(window=period).std().replace(0, np.nan).bfill()
    upper = mid + (num_std * std)
    lower = mid - (num_std * std)
    bandwidth = ((upper - lower) / mid.replace(0, np.nan)) * 100.0
    zscore = (series - mid) / std
    return upper, mid, lower, bandwidth.fillna(0.0), zscore.fillna(0.0)


def adx(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Average Directional Index (ADX) with +DI and -DI.
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    
    up_move = high - prev_high
    down_move = prev_low - low
    
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    tr = atr(df, period)
    
    plus_dm_series = pd.Series(plus_dm, index=df.index).ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    minus_dm_series = pd.Series(minus_dm, index=df.index).ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    
    plus_di = (plus_dm_series / tr.replace(0, np.nan)) * 100.0
    minus_di = (minus_dm_series / tr.replace(0, np.nan)) * 100.0
    
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100.0
    adx_val = dx.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean().fillna(20.0)
    
    return adx_val, plus_di.fillna(0.0), minus_di.fillna(0.0)


def rate_of_change(series: pd.Series, period: int = 12) -> pd.Series:
    """Price Rate of Change (ROC)."""
    return ((series - series.shift(period)) / series.shift(period).replace(0, np.nan)) * 100.0


def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> Tuple[pd.Series, pd.Series]:
    """
    Supertrend indicator.
    Returns: (supertrend_value, direction: 1 for Bullish, -1 for Bearish)
    """
    hl2 = (df["high"] + df["low"]) / 2.0
    atr_val = atr(df, period)
    
    upper_basic = hl2 + (multiplier * atr_val)
    lower_basic = hl2 - (multiplier * atr_val)
    
    upper_band = upper_basic.copy()
    lower_band = lower_basic.copy()
    
    close = df["close"].values
    n = len(df)
    trend = np.zeros(n)
    st = np.zeros(n)
    
    for i in range(1, n):
        if close[i - 1] > lower_band.iloc[i - 1]:
            lower_band.iloc[i] = max(lower_basic.iloc[i], lower_band.iloc[i - 1])
        else:
            lower_band.iloc[i] = lower_basic.iloc[i]
            
        if close[i - 1] < upper_band.iloc[i - 1]:
            upper_band.iloc[i] = min(upper_basic.iloc[i], upper_band.iloc[i - 1])
        else:
            upper_band.iloc[i] = upper_basic.iloc[i]
            
        if close[i] > upper_band.iloc[i - 1]:
            trend[i] = 1
        elif close[i] < lower_band.iloc[i - 1]:
            trend[i] = -1
        else:
            trend[i] = trend[i - 1]
            
        st[i] = lower_band.iloc[i] if trend[i] == 1 else upper_band.iloc[i]
        
    return pd.Series(st, index=df.index), pd.Series(trend, index=df.index)


def stochastic_oscillator(
    df: pd.DataFrame, k_period: int = 14, d_period: int = 3, smooth_k: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """
    Full Stochastic Oscillator (%K and %D lines).
    Essential for high-precision micro-momentum turnarounds in 1m/3m/5m scalping.
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]

    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    denom = (highest_high - lowest_low).replace(0, np.nan)
    raw_k = ((close - lowest_low) / denom) * 100.0

    # Smooth %K
    stoch_k = raw_k.rolling(window=smooth_k).mean().fillna(50.0)
    # %D is SMA of smoothed %K
    stoch_d = stoch_k.rolling(window=d_period).mean().fillna(50.0)

    return stoch_k, stoch_d


def vwap(df: pd.DataFrame) -> pd.Series:
    """
    Volume Weighted Average Price (VWAP).
    Key benchmark for institutional value pullbacks in short-timeframe trading.
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]
    volume = df["volume"].replace(0, 1.0)

    typical_price = (high + low + close) / 3.0
    cum_vol_price = (typical_price * volume).cumsum()
    cum_vol = volume.cumsum()

    vwap_series = cum_vol_price / cum_vol.replace(0, np.nan)
    return vwap_series.fillna(close)


def fast_atr(df: pd.DataFrame, period: int = 5) -> pd.Series:
    """Fast Average True Range for rapid short-timeframe volatility calibration."""
    return atr(df, period=period)

