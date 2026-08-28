"""
Deterministic No-Trade Engine (First-Class Veto System).
Enforces 12+ explicit veto rules to filter out low-probability or high-risk market conditions.
"""
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from app.core.config import settings
from app.services.quality_guard import quality_guard
from app.trading.regime import MarketRegime, classify_market_regime


class NoTradeEngine:
    def __init__(self):
        pass

    def evaluate_vetoes(
        self,
        symbol: str,
        side: str,
        strategy_id: str,
        df_m15: pd.DataFrame,
        df_h1: Optional[pd.DataFrame] = None,
        quote: Optional[Dict[str, Any]] = None,
        daily_loss_pct: float = 0.0,
        drawdown_pct: float = 0.0,
        open_positions_count: int = 0,
        currency_exposure_count: int = 0,
        cooldown_remaining_seconds: float = 0.0,
        risk_reward_ratio: float = 2.0,
    ) -> Tuple[bool, List[str]]:
        """
        Returns (is_vetoed: bool, veto_reasons: List[str]).
        If is_vetoed is True, trade MUST NOT execute.
        """
        vetoes = []

        # 1. Stale Data & Spread Check from Live Quote
        if quote:
            if not quote.get("quality_valid", True):
                vetoes.append(f"Data Quality Guard: {quote.get('quality_error', 'Invalid market tick')}")
            spread_pips = quote.get("spread_pips", 1.0)
            if spread_pips > settings.MAX_SPREAD_PIPS:
                vetoes.append(f"Spread {spread_pips:.2f} pips exceeds {settings.MAX_SPREAD_PIPS} limit")

        if df_m15.empty or len(df_m15) < 30:
            vetoes.append("Insufficient M15 historical bars for indicator evaluation")
            return True, vetoes

        latest_m15 = df_m15.iloc[-1]
        rsi_14 = float(latest_m15.get("rsi_14", 50.0))

        # 2. RSI Climax Guard
        if side.upper() == "BUY" and rsi_14 > 72.0:
            vetoes.append(f"RSI Climax Guard: Long rejected at overbought RSI ({rsi_14:.1f} > 72)")
        elif side.upper() == "SELL" and rsi_14 < 28.0:
            vetoes.append(f"RSI Climax Guard: Short rejected at oversold RSI ({rsi_14:.1f} < 28)")

        # 3. Multi-Timeframe Alignment Gate (Trend Direction)
        if df_h1 is not None and not df_h1.empty and len(df_h1) >= 30:
            latest_trend = df_h1.iloc[-1]
            close_trend = float(latest_trend["close"])
            ema_50_trend = float(latest_trend.get("ema_50", close_trend))
            ema_20_trend = float(latest_trend.get("ema_20", close_trend))
            pct_diff = (close_trend - ema_50_trend) / max(1e-5, ema_50_trend)

            # Reversal & liquidity strategies are exempt from strict trend conformity
            is_reversal_strat = "REVERSAL" in strategy_id or "FVG" in strategy_id or "MEAN_REVERSION" in strategy_id

            if not is_reversal_strat:
                if side.upper() == "BUY" and pct_diff < -0.015 and ema_20_trend < ema_50_trend:
                    vetoes.append("Higher Timeframe Trend Conflict: Long opposes strong Bearish Trend (EMA20 < EMA50)")
                elif side.upper() == "SELL" and pct_diff > 0.015 and ema_20_trend > ema_50_trend:
                    vetoes.append("Higher Timeframe Trend Conflict: Short opposes strong Bullish Trend (EMA20 > EMA50)")

        # 4. Minimum Risk-to-Reward Threshold
        if risk_reward_ratio < settings.MIN_RISK_REWARD:
            vetoes.append(f"Risk:Reward ({risk_reward_ratio:.2f}) below required minimum {settings.MIN_RISK_REWARD}:1")

        # 5. Account Risk Boundaries
        if daily_loss_pct >= settings.MAX_DAILY_LOSS:
            vetoes.append(f"Daily Loss Limit Breached: Current daily loss {daily_loss_pct*100:.2f}% >= {settings.MAX_DAILY_LOSS*100:.2f}%")

        if drawdown_pct >= settings.MAX_DRAWDOWN:
            vetoes.append(f"Max Drawdown Breached: Peak-to-trough drawdown {drawdown_pct*100:.2f}% >= {settings.MAX_DRAWDOWN*100:.2f}%")

        if open_positions_count >= settings.MAX_OPEN_POSITIONS:
            vetoes.append(f"Position Limit Reached: Active positions ({open_positions_count}) >= {settings.MAX_OPEN_POSITIONS}")

        if currency_exposure_count >= settings.MAX_CURRENCY_CONCENTRATION:
            vetoes.append(f"Currency Concentration Reached: Pair exposure count ({currency_exposure_count}) >= {settings.MAX_CURRENCY_CONCENTRATION}")

        # 6. Anti-Overtrading Cooldown
        if cooldown_remaining_seconds > 0:
            vetoes.append(f"Anti-Overtrading Cooldown Active: {int(cooldown_remaining_seconds // 60)}m {int(cooldown_remaining_seconds % 60)}s remaining")

        return len(vetoes) > 0, vetoes


no_trade_engine = NoTradeEngine()
