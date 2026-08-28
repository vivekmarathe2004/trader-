"""
Hardened Multi-Layer Deterministic Risk Engine.
The single, un-bypassable gatekeeper for all order submissions.
"""
from typing import Dict, Tuple, Optional, List, Any
from app.core.config import settings
from app.core.logging import logger
from app.core.security import idempotency_guard, generate_idempotency_key
from app.risk.position_sizer import position_sizer
from app.risk.exposure import exposure_tracker
from app.risk.portfolio_risk import portfolio_risk_engine


class RiskEngine:
    def __init__(self):
        self.emergency_kill_switch_active: bool = False
        self.live_trading_enabled: bool = settings.LIVE_TRADING_ENABLED
        self._initial_day_equity: float = 100000.0
        self._current_equity: float = 100000.0
        self._peak_equity: float = 100000.0
        self._daily_realized_loss: float = 0.0

    def trigger_emergency_kill_switch(self, reason: str = "Manual User Trigger"):
        self.emergency_kill_switch_active = True
        logger.critical(f"EMERGENCY KILL SWITCH ACTIVATED: {reason}")

    def reset_emergency_kill_switch(self):
        self.emergency_kill_switch_active = False
        logger.warning("Emergency Kill Switch has been reset.")

    def reset_daily_stats(self, initial_equity: float = 100000.0):
        self._initial_day_equity = initial_equity
        self._current_equity = initial_equity
        self._peak_equity = initial_equity
        self._daily_realized_loss = 0.0

    def set_live_trading_gate(self, enabled: bool):
        self.live_trading_enabled = enabled
        logger.warning(f"Master Live Trading Gate set to: {enabled}")

    def update_equity(self, current_equity: float, realized_pnl_delta: float = 0.0):
        self._current_equity = current_equity
        if current_equity > self._peak_equity:
            self._peak_equity = current_equity
        if realized_pnl_delta < 0:
            self._daily_realized_loss += abs(realized_pnl_delta)

    def get_daily_loss_pct(self) -> float:
        if self._initial_day_equity <= 0:
            return 0.0
        return self._daily_realized_loss / self._initial_day_equity

    def get_drawdown_pct(self) -> float:
        if self._peak_equity <= 0:
            return 0.0
        return max(0.0, (self._peak_equity - self._current_equity) / self._peak_equity)

    def validate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_loss: Optional[float],
        take_profit: Optional[float],
        broker_type: str,
        open_positions: list,
        strategy_id: str = "MANUAL",
        current_spread_pips: float = 1.2,
    ) -> Tuple[bool, Optional[str], float]:
        """
        Un-bypassable multi-layer risk validation loop.
        Returns: (is_approved: bool, rejection_reason: Optional[str], approved_lots: float)
        """
        symbol = symbol.upper()
        side = side.upper()

        # Layer 1: Emergency Kill Switch
        if self.emergency_kill_switch_active:
            return False, "REJECTED: Emergency Kill Switch is currently active", 0.0

        # Layer 2: Live Trading Master Gate
        is_real_broker = broker_type.upper() not in ["MOCK_BROKER", "PAPER"]
        if is_real_broker and not self.live_trading_enabled:
            return False, "REJECTED: Master Live Trading Gate is locked (LIVE_TRADING_ENABLED=False)", 0.0

        # Layer 3: Daily Loss Limit
        if self.get_daily_loss_pct() >= settings.MAX_DAILY_LOSS:
            return False, f"REJECTED: Daily Loss Limit breached ({self.get_daily_loss_pct()*100:.2f}% >= {settings.MAX_DAILY_LOSS*100:.2f}%)", 0.0

        # Layer 4: Peak-to-Trough Drawdown
        if self.get_drawdown_pct() >= settings.MAX_DRAWDOWN:
            return False, f"REJECTED: Max Drawdown breached ({self.get_drawdown_pct()*100:.2f}% >= {settings.MAX_DRAWDOWN*100:.2f}%)", 0.0

        # Layer 5: Max Open Positions
        if len(open_positions) >= settings.MAX_OPEN_POSITIONS:
            return False, f"REJECTED: Max Open Positions reached ({len(open_positions)} >= {settings.MAX_OPEN_POSITIONS})", 0.0

        # Layer 6: Spread Filter
        if current_spread_pips > settings.MAX_SPREAD_PIPS:
            return False, f"REJECTED: Spread {current_spread_pips:.2f} pips exceeds max threshold {settings.MAX_SPREAD_PIPS} pips", 0.0

        # Layer 7: Stop Loss and Take Profit Mandatory Integrity
        if not stop_loss or not take_profit:
            return False, "REJECTED: Hard Stop Loss and Take Profit are strictly mandatory", 0.0

        # Validate SL/TP Geometry
        if side == "BUY" and (stop_loss >= price or take_profit <= price):
            return False, f"REJECTED: Invalid BUY geometry (SL {stop_loss} >= Entry {price} or TP {take_profit} <= Entry)", 0.0
        elif side == "SELL" and (stop_loss <= price or take_profit >= price):
            return False, f"REJECTED: Invalid SELL geometry (SL {stop_loss} <= Entry {price} or TP {take_profit} >= Entry)", 0.0

        # Layer 8: Minimum Risk:Reward Ratio
        sl_dist = abs(price - stop_loss)
        tp_dist = abs(take_profit - price)
        rr_ratio = tp_dist / max(sl_dist, 1e-6)
        if rr_ratio < settings.MIN_RISK_REWARD:
            return False, f"REJECTED: Calculated Risk:Reward ({rr_ratio:.2f}) is below mandatory minimum {settings.MIN_RISK_REWARD}:1", 0.0

        # Layer 9: Currency Concentration Exposure
        base = symbol[:3]
        quote = symbol[3:6] if len(symbol) >= 6 else ""
        currency_count = sum(1 for p in open_positions if base in p.symbol or (quote and quote in p.symbol))
        if currency_count >= settings.MAX_CURRENCY_CONCENTRATION:
            return False, f"REJECTED: Currency concentration limit reached ({currency_count} pairs already active)", 0.0

        # Layer 10: Fixed Fractional Position Sizing Check & Override
        calculated_lots = position_sizer.calculate_lots(
            symbol=symbol,
            equity=self._current_equity,
            entry_price=price,
            stop_loss=stop_loss,
            risk_pct=settings.DEFAULT_RISK_PER_TRADE,
        )

        final_lots = min(quantity, calculated_lots) if quantity > 0 else calculated_lots

        # Layer 11: Order Idempotency Guard (rounded to 30s window)
        import time
        rounded_ts = int(time.time() // 30)
        idem_key = generate_idempotency_key(symbol, side, strategy_id, rounded_ts)
        if not idempotency_guard.check_and_set(idem_key):
            return False, "REJECTED: Duplicate order signature within 30-second window", 0.0

        return True, None, final_lots

    def get_risk_status(self, open_positions: list) -> Dict[str, Any]:
        exposure = exposure_tracker.calculate_exposure(open_positions)
        var_metrics = portfolio_risk_engine.compute_portfolio_risk_metrics(self._current_equity, [])
        return {
            "emergency_kill_switch_active": self.emergency_kill_switch_active,
            "live_trading_enabled": self.live_trading_enabled,
            "current_equity": round(self._current_equity, 2),
            "peak_equity": round(self._peak_equity, 2),
            "daily_loss_pct": round(self.get_daily_loss_pct() * 100, 2),
            "max_daily_loss_pct": round(settings.MAX_DAILY_LOSS * 100, 2),
            "drawdown_pct": round(self.get_drawdown_pct() * 100, 2),
            "max_drawdown_pct": round(settings.MAX_DRAWDOWN * 100, 2),
            "open_positions_count": len(open_positions),
            "max_open_positions": settings.MAX_OPEN_POSITIONS,
            "min_risk_reward": settings.MIN_RISK_REWARD,
            "max_spread_pips": settings.MAX_SPREAD_PIPS,
            "exposure": exposure,
            "portfolio_risk": var_metrics,
        }


risk_engine = RiskEngine()
