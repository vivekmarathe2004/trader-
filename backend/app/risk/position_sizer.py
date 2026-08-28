"""
Deterministic Position Sizing Engine (Fixed Fractional & Volatility-Adjusted).
"""
import numpy as np
from typing import Dict, Optional
from app.core.config import settings


class PositionSizer:
    def calculate_lots(
        self,
        symbol: str,
        equity: float,
        entry_price: float,
        stop_loss: float,
        risk_pct: Optional[float] = None,
        atr: Optional[float] = None,
    ) -> float:
        """
        Calculates optimal lot size based on account equity, risk percentage, and SL distance.
        Formula: Lots = (Equity * Risk%) / (SL Distance in Pips * Pip Value per Standard Lot)
        """
        risk_percentage = risk_pct if risk_pct is not None else settings.DEFAULT_RISK_PER_TRADE
        risk_amount_usd = equity * risk_percentage

        sl_distance = abs(entry_price - stop_loss)
        pip_size = settings.get_pip_size(symbol)
        
        if sl_distance <= 0 or pip_size <= 0:
            return 0.01  # Minimum lot default

        sl_pips = sl_distance / pip_size
        
        # Approximate pip value per 1.0 standard lot (100,000 units) in USD
        # For EURUSD, GBPUSD, AUDUSD, NZDUSD: $10/pip per standard lot
        # For USDJPY, USDCAD, USDCHF: ~$10 / exchange rate
        # For Crypto (1 unit): pip value = $0.01 or $1
        lot_units = settings.get_lot_units(symbol)
        
        if "USD" in symbol:
            if symbol.endswith("USD"):
                pip_val_per_unit = pip_size
            else:
                pip_val_per_unit = pip_size / max(entry_price, 1e-4)
        else:
            pip_val_per_unit = pip_size

        risk_per_unit = sl_distance
        total_units = risk_amount_usd / max(risk_per_unit, 1e-6)
        
        calculated_lots = total_units / lot_units

        # Volatility adjustment: If current ATR is unusually high (> 1.5x normal), reduce size
        if atr and atr > 0:
            expected_atr = entry_price * 0.005
            if atr > (expected_atr * 1.5):
                vol_scale = expected_atr / atr
                calculated_lots *= min(1.0, max(0.5, vol_scale))

        # Clamp between 0.01 and 10.0 lots for safety
        clamped_lots = round(float(np.clip(calculated_lots, 0.01, 10.0)), 2)
        return clamped_lots


position_sizer = PositionSizer()
