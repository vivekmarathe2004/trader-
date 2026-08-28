"""
Market data quality guard verifying freshness, spread validity, outliers, and gaps.
"""
import time
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timezone
import pandas as pd
from app.core.config import settings
from app.core.logging import logger


class DataQualityGuard:
    def __init__(self, max_stale_seconds: float = 30.0, max_spread_multiplier: float = 2.5):
        self.max_stale_seconds = max_stale_seconds
        self.max_spread_multiplier = max_spread_multiplier
        self._spread_history: Dict[str, List[float]] = {}
        self._last_tick_time: Dict[str, float] = {}

    def validate_tick(self, symbol: str, bid: float, ask: float, timestamp: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        now = timestamp or time.time()
        
        # 1. Non-positive price check
        if bid <= 0 or ask <= 0:
            return False, f"Invalid non-positive price: bid={bid}, ask={ask}"
            
        # 2. Inverted spread check
        if bid > ask:
            return False, f"Crossed market: bid {bid} > ask {ask}"
            
        pip_size = settings.get_pip_size(symbol)
        spread_pips = (ask - bid) / pip_size
        
        # 3. Absolute spread threshold check
        if spread_pips > settings.MAX_SPREAD_PIPS:
            return False, f"Spread {spread_pips:.2f} pips exceeds absolute threshold ({settings.MAX_SPREAD_PIPS} pips)"
            
        # 4. Spread expansion relative to rolling average
        history = self._spread_history.setdefault(symbol, [])
        history.append(spread_pips)
        if len(history) > 50:
            history.pop(0)
            
        if len(history) >= 10:
            avg_spread = sum(history) / len(history)
            if spread_pips > (avg_spread * self.max_spread_multiplier) and spread_pips > 1.5:
                return False, f"Abnormal spread expansion: {spread_pips:.2f} pips vs avg {avg_spread:.2f} pips"
                
        # 5. Stale price check
        last_time = self._last_tick_time.get(symbol)
        if last_time and (now - last_time) > self.max_stale_seconds:
            # We record warning but update time
            self._last_tick_time[symbol] = now
            return False, f"Stale market data: latency {now - last_time:.1f}s exceeds {self.max_stale_seconds}s limit"
            
        self._last_tick_time[symbol] = now
        return True, None

    def validate_ohlcv_dataframe(self, df: pd.DataFrame, symbol: str) -> Tuple[bool, Optional[str]]:
        if df.empty:
            return False, "OHLCV DataFrame is empty"
            
        required_cols = ["open", "high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                return False, f"Missing required column: {col}"
                
        # Check high >= low, high >= open, high >= close, low <= open, low <= close
        invalid_candles = (
            (df["high"] < df["low"]) |
            (df["high"] < df["open"]) |
            (df["high"] < df["close"]) |
            (df["low"] > df["open"]) |
            (df["low"] > df["close"])
        )
        if invalid_candles.any():
            return False, f"Found {invalid_candles.sum()} geometrically impossible candles"
            
        # Check price gaps > 15%
        close = df["close"]
        pct_change = close.pct_change().abs()
        if (pct_change > 0.15).any():
            return False, "Abnormal outlier gap (>15%) detected in historical bars"
            
        return True, None


quality_guard = DataQualityGuard()
