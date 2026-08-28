"""
Alpha Vantage market data provider with fallback.
"""
import httpx
from typing import Dict, Optional, Any
from app.core.config import settings
from app.core.logging import logger


class AlphaVantageProvider:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ALPHA_VANTAGE_API_KEY
        self.base_url = "https://www.alphavantage.co/query"

    async def get_fx_rate(self, from_currency: str, to_currency: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(
                    self.base_url,
                    params={
                        "function": "CURRENCY_EXCHANGE_RATE",
                        "from_currency": from_currency,
                        "to_currency": to_currency,
                        "apikey": self.api_key,
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    rate_data = data.get("Realtime Currency Exchange Rate", {})
                    if rate_data:
                        return {
                            "from_symbol": rate_data.get("1. From_Currency Code"),
                            "to_symbol": rate_data.get("3. To_Currency Code"),
                            "exchange_rate": float(rate_data.get("5. Exchange Rate", 0.0)),
                            "bid_price": float(rate_data.get("8. Bid Price", 0.0)),
                            "ask_price": float(rate_data.get("9. Ask Price", 0.0)),
                        }
        except Exception as e:
            logger.warning(f"Alpha Vantage FX fetch failed for {from_currency}/{to_currency}: {e}")
        return None


alpha_vantage_provider = AlphaVantageProvider()
