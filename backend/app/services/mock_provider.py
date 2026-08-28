"""
High-fidelity deterministic Brownian motion market data generator.
Simulates realistic trend momentum, volatility clustering, and bid/ask spreads.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List
from app.core.config import settings


class MockDataProvider:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self._rng = np.random.default_rng(seed)
        
        # Base realistic prices
        self._base_prices: Dict[str, float] = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2650,
            "USDJPY": 154.20,
            "AUDUSD": 0.6550,
            "USDCAD": 1.3650,
            "USDCHF": 0.9050,
            "NZDUSD": 0.5950,
            "BTCUSDT": 67500.0,
            "ETHUSDT": 3550.0,
            "SOLUSDT": 182.0,
            "BNBUSDT": 590.0,
            "ADAUSDT": 0.4850,
            "XRPUSDT": 0.5650,
        }
        
        # Volatilities (annualized / bar-level)
        self._volatilities: Dict[str, float] = {
            "EURUSD": 0.0004,
            "GBPUSD": 0.0006,
            "USDJPY": 0.08,
            "AUDUSD": 0.0005,
            "USDCAD": 0.0005,
            "USDCHF": 0.0004,
            "NZDUSD": 0.0005,
            "BTCUSDT": 45.0,
            "ETHUSDT": 4.5,
            "SOLUSDT": 0.4,
            "BNBUSDT": 0.8,
            "ADAUSDT": 0.0015,
            "XRPUSDT": 0.0020,
        }
        
        # Current live tick prices
        self._current_prices: Dict[str, float] = self._base_prices.copy()
        self._cached_bars: Dict[str, pd.DataFrame] = {}

    def get_latest_price(self, symbol: str) -> Dict[str, float]:
        symbol = symbol.upper()
        curr = self._current_prices.get(symbol, 1.0850)
        vol = self._volatilities.get(symbol, 0.0004)
        pip_size = settings.get_pip_size(symbol)
        
        # Slight Brownian step
        step = self._rng.normal(0, vol * 0.2)
        new_price = max(pip_size * 10, curr + step)
        self._current_prices[symbol] = new_price
        
        # Spread: 1.0 to 1.8 pips
        spread_pips = self._rng.uniform(1.0, 1.8)
        half_spread = (spread_pips * pip_size) / 2.0
        
        bid = round(new_price - half_spread, 5 if pip_size < 0.001 else 2)
        ask = round(new_price + half_spread, 5 if pip_size < 0.001 else 2)
        
        return {
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "price": new_price,
            "spread_pips": round(spread_pips, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def generate_ohlcv(self, symbol: str, timeframe: str = "15m", count: int = 300) -> pd.DataFrame:
        symbol = symbol.upper()
        base_p = self._base_prices.get(symbol, 1.0850)
        vol = self._volatilities.get(symbol, 0.0004)
        pip_size = settings.get_pip_size(symbol)
        
        # Use deterministic seed combined with symbol for reproducible yet realistic motion
        symbol_seed = abs(hash(symbol + timeframe)) % (2**31 - 1)
        rng = np.random.default_rng(symbol_seed)
        
        # Geometric Brownian Motion with mild trend & mean reversion
        dt = 1.0
        drift = rng.choice([-0.00005, 0.00005, 0.0])
        
        std_pct = min(0.003, max(0.0002, vol / base_p))
        returns = rng.normal(drift, std_pct, count)
        price_path = base_p * np.exp(np.cumsum(returns))
        
        now = datetime.now(timezone.utc)
        delta_map = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}
        step_minutes = delta_map.get(timeframe.lower(), 15)
        
        timestamps = [now - timedelta(minutes=(count - i) * step_minutes) for i in range(count)]
        
        rows = []
        for i in range(count):
            close_p = price_path[i]
            prev_close = price_path[i - 1] if i > 0 else base_p
            open_p = prev_close + rng.normal(0, vol * 0.1)
            
            intra_max = max(open_p, close_p)
            intra_min = min(open_p, close_p)
            
            high_p = intra_max + abs(rng.normal(0, vol * 0.6))
            low_p = max(pip_size, intra_min - abs(rng.normal(0, vol * 0.6)))
            
            volume = float(rng.integers(100, 5000))
            
            dec = 5 if pip_size < 0.001 else 2
            rows.append({
                "timestamp": timestamps[i],
                "open": round(float(open_p), dec),
                "high": round(float(high_p), dec),
                "low": round(float(low_p), dec),
                "close": round(float(close_p), dec),
                "volume": volume,
            })
            
        df = pd.DataFrame(rows)
        self._cached_bars[f"{symbol}_{timeframe}"] = df
        return df


mock_provider = MockDataProvider()
