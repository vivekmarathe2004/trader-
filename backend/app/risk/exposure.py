"""
Currency concentration, net asset exposure, and correlation tracking.
"""
from typing import Dict, List, Any
from app.core.config import settings


class ExposureTracker:
    def __init__(self):
        pass

    def calculate_exposure(self, open_positions: list) -> Dict[str, Any]:
        """
        Calculates total notional USD exposure and currency distribution.
        """
        total_notional_usd = 0.0
        currency_breakdown: Dict[str, float] = {}
        pair_counts: Dict[str, int] = {}

        for pos in open_positions:
            symbol = pos.symbol.upper()
            lots = getattr(pos, "lots", 0.0)
            entry_price = getattr(pos, "entry_price", 1.0)
            units = lots * settings.get_lot_units(symbol)
            notional = units * entry_price
            total_notional_usd += notional

            # Currency breakdown
            if len(symbol) == 6:  # Forex pair (e.g., EURUSD)
                base = symbol[:3]
                quote = symbol[3:6]
                side_sign = 1.0 if pos.side.upper() == "BUY" else -1.0
                
                currency_breakdown[base] = currency_breakdown.get(base, 0.0) + (notional * side_sign)
                currency_breakdown[quote] = currency_breakdown.get(quote, 0.0) - (notional * side_sign)
                
                pair_counts[base] = pair_counts.get(base, 0) + 1
                pair_counts[quote] = pair_counts.get(quote, 0) + 1
            else:
                currency_breakdown[symbol] = currency_breakdown.get(symbol, 0.0) + notional

        return {
            "total_notional_usd": round(total_notional_usd, 2),
            "max_notional_limit": settings.MAX_NOTIONAL_EXPOSURE,
            "currency_net_exposure_usd": {k: round(v, 2) for k, v in currency_breakdown.items()},
            "currency_pair_counts": pair_counts,
            "is_concentration_limit_breached": any(c > settings.MAX_CURRENCY_CONCENTRATION for c in pair_counts.values()),
        }


exposure_tracker = ExposureTracker()
