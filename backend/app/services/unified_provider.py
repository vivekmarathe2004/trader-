"""
Unified market data gateway serving real-time prices and historical bars with validation.
"""
from typing import Dict, List, Optional, Any
import pandas as pd
from app.core.config import settings
from app.services.quality_guard import quality_guard
from app.services.real_market_provider import real_market_provider
from app.services.mock_provider import mock_provider
from app.features.pipeline import compute_indicator_pipeline
from app.core.logging import logger


class UnifiedMarketDataProvider:
    def __init__(self):
        self._provider_mode: str = "REAL"  # REAL, HYBRID, MOCK_ONLY
        self._cached_dfs: Dict[str, pd.DataFrame] = {}

    def get_usd_inr_rate(self) -> float:
        return real_market_provider.get_usd_inr_rate()

    def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        symbol = symbol.upper()
        
        try:
            quote = real_market_provider.get_latest_quote(symbol)
        except Exception as e:
            logger.debug(f"Real market quote fallback for {symbol}: {e}")
            quote = mock_provider.get_latest_price(symbol)
        
        # Validate data quality
        is_valid, err = quality_guard.validate_tick(symbol, quote["bid"], quote["ask"])
        quote["quality_valid"] = is_valid
        quote["quality_error"] = err
        
        return quote

    def get_all_quotes(self) -> List[Dict[str, Any]]:
        quotes = []
        for symbol in settings.ALL_SYMBOLS:
            quote = self.get_latest_quote(symbol)
            quotes.append(quote)
        return quotes

    def get_ohlcv(self, symbol: str, timeframe: str = "15m", count: int = 300) -> pd.DataFrame:
        symbol = symbol.upper()
        cache_key = f"{symbol}_{timeframe}_{count}"
        
        try:
            df = real_market_provider.get_ohlcv(symbol, timeframe, count)
        except Exception as e:
            logger.debug(f"Real OHLCV fallback for {symbol}: {e}")
            df = mock_provider.generate_ohlcv(symbol, timeframe, count)
        
        is_valid, err = quality_guard.validate_ohlcv_dataframe(df, symbol)
        if not is_valid:
            logger.warning(f"Quality guard flagged OHLCV for {symbol}: {err}")
            
        self._cached_dfs[cache_key] = df
        return df

    def get_enriched_pipeline(self, symbol: str, timeframe: str = "15m", count: int = 300) -> pd.DataFrame:
        raw_df = self.get_ohlcv(symbol, timeframe, count)
        enriched_df = compute_indicator_pipeline(raw_df)
        return enriched_df


unified_provider = UnifiedMarketDataProvider()
