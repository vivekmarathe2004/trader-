"""
Finnhub REST/WebSocket market data provider with fallback.
"""
import httpx
from typing import Dict, Optional, Any
from app.core.config import settings
from app.core.logging import logger


class FinnhubProvider:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.FINNHUB_API_KEY
        self.base_url = "https://finnhub.io/api/v1"

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(
                    f"{self.base_url}/quote",
                    params={"symbol": symbol, "token": self.api_key}
                )
                if res.status_code == 200:
                    data = res.json()
                    # c = current price, h = high, l = low, o = open, pc = previous close
                    return {
                        "symbol": symbol,
                        "price": data.get("c"),
                        "high": data.get("h"),
                        "low": data.get("l"),
                        "open": data.get("o"),
                        "prev_close": data.get("pc"),
                    }
        except Exception as e:
            logger.warning(f"Finnhub quote fetch failed for {symbol}: {e}")
        return None


finnhub_provider = FinnhubProvider()
