"""
Multi-timeframe Confluence & Checklist Matrix Engine.
Aggregates quantitative strategies, candlestick patterns, micro-momentum indicators, and regime alignment.
"""
import time
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from app.core.config import settings
from app.trading.strategies import ALL_QUANT_STRATEGIES, StrategySignalResult
from app.trading.pattern_engine import detect_candlestick_patterns
from app.trading.regime import classify_market_regime
from app.trading.no_trade import no_trade_engine
from app.services.unified_provider import unified_provider


class ConfluenceEngine:
    def __init__(self):
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def evaluate_symbol_confluence(
        self,
        symbol: str,
        timeframe: Optional[str] = None,
        df_m15: Optional[pd.DataFrame] = None,
        df_h1: Optional[pd.DataFrame] = None,
        df_exec: Optional[pd.DataFrame] = None,
        df_trend: Optional[pd.DataFrame] = None,
        daily_loss_pct: float = 0.0,
        drawdown_pct: float = 0.0,
        open_positions_count: int = 0,
        currency_exposure_count: int = 0,
        cooldown_remaining_seconds: float = 0.0,
    ) -> Dict[str, Any]:
        symbol = symbol.upper()
        active_tf = timeframe or getattr(settings, "DEFAULT_TIMEFRAME", "1m")

        # Fast cache check if no custom DataFrames are supplied
        cache_key = f"{symbol}_{active_tf}_{daily_loss_pct}_{open_positions_count}_{cooldown_remaining_seconds > 0}"
        now = time.time()
        if df_exec is None and df_trend is None and df_m15 is None and df_h1 is None:
            if cache_key in self._cache:
                cached_time, cached_res = self._cache[cache_key]
                if now - cached_time < 1.5:  # 1.5 second TTL cache
                    return cached_res

        # Map execution timeframe to optimal higher-timeframe trend context
        tf_trend_map = {
            "1m": "5m",
            "3m": "15m",
            "5m": "15m",
            "15m": "1h",
            "1h": "4h",
        }
        trend_tf = tf_trend_map.get(active_tf.lower(), "15m")

        # Fetch execution and trend dataframes
        exec_df = df_exec if df_exec is not None else df_m15
        if exec_df is None or exec_df.empty:
            exec_df = unified_provider.get_enriched_pipeline(symbol, active_tf, 250)

        trend_df = df_trend if df_trend is not None else df_h1
        if trend_df is None or trend_df.empty:
            trend_df = unified_provider.get_enriched_pipeline(symbol, trend_tf, 100)

        quote = unified_provider.get_latest_quote(symbol)
        regime_info = classify_market_regime(exec_df)
        patterns = detect_candlestick_patterns(exec_df)

        strategy_results: List[StrategySignalResult] = []
        approved_signals: List[StrategySignalResult] = []

        for strat in ALL_QUANT_STRATEGIES:
            res = strat.evaluate(exec_df, symbol)
            strategy_results.append(res)
            if res.decision == "APPROVED" and res.side:
                approved_signals.append(res)

        # Compute multi-factor institutional scalp confluence score (0-100)
        best_signal: Optional[StrategySignalResult] = None
        best_score = 0.0

        if not exec_df.empty and len(exec_df) >= 30:
            latest_bar = exec_df.iloc[-1]
            adx_val = float(latest_bar.get("adx_14", 20.0))
            rsi_val = float(latest_bar.get("rsi_14", 50.0))
            body_pct = float(latest_bar.get("body_pct", 0.5))
            stoch_k = float(latest_bar.get("stoch_k", 50.0))
            stoch_d = float(latest_bar.get("stoch_d", 50.0))
            vwap_val = float(latest_bar.get("vwap", float(latest_bar["close"])))
            close_val = float(latest_bar["close"])

            for sig in approved_signals:
                score = 50.0  # Base score for clearing strategy rules

                # 1. Trend & ADX Strength Factor (up to +20 pts)
                if adx_val >= 20.0:
                    score += min(20.0, (adx_val - 18.0) * 1.5)

                # 2. Optimal RSI Scalp Momentum Zone (up to +15 pts)
                if sig.side == "BUY" and 48.0 <= rsi_val <= 68.0:
                    score += 15.0  # Optimal bullish expansion zone
                elif sig.side == "SELL" and 32.0 <= rsi_val <= 52.0:
                    score += 15.0  # Optimal bearish expansion zone

                # 3. Micro-Stochastic Oscillator Alignment (up to +10 pts)
                if sig.side == "BUY" and stoch_k > stoch_d:
                    score += 10.0
                elif sig.side == "SELL" and stoch_k < stoch_d:
                    score += 10.0

                # 4. Institutional VWAP Alignment (up to +10 pts)
                if (sig.side == "BUY" and close_val >= vwap_val) or (sig.side == "SELL" and close_val <= vwap_val):
                    score += 10.0

                # 5. Candlestick Body Quality (up to +10 pts)
                if body_pct >= 0.40:
                    score += 10.0

                # 6. Multi-Strategy Agreement Bonus (+7.5 pts per extra agreeing strategy)
                same_dir_count = sum(1 for s in approved_signals if s.side == sig.side)
                score += (same_dir_count - 1) * 7.5

                # 7. Risk:Reward Ratio Efficiency (up to +10 pts)
                rr = sig.risk_reward_ratio or 1.8
                if rr >= 1.8:
                    score += min(10.0, (rr - 1.5) * 10.0)

                if score > best_score:
                    best_score = score
                    best_signal = sig

        primary_signal = best_signal or (approved_signals[0] if approved_signals else None)
        final_confluence_score = round(best_score, 1) if primary_signal else 0.0

        final_decision = "NO_SIGNAL"
        veto_reasons = []
        is_vetoed = False

        if primary_signal and primary_signal.side:
            is_vetoed, vetoes = no_trade_engine.evaluate_vetoes(
                symbol=symbol,
                side=primary_signal.side,
                strategy_id=primary_signal.strategy_id,
                df_m15=exec_df,
                df_h1=trend_df,
                quote=quote,
                daily_loss_pct=daily_loss_pct,
                drawdown_pct=drawdown_pct,
                open_positions_count=open_positions_count,
                currency_exposure_count=currency_exposure_count,
                cooldown_remaining_seconds=cooldown_remaining_seconds,
                risk_reward_ratio=primary_signal.risk_reward_ratio or 1.8,
            )
            veto_reasons.extend(vetoes)
            if is_vetoed:
                final_decision = "NO_TRADE"
            else:
                final_decision = "APPROVED"

        result = {
            "symbol": symbol,
            "timeframe": active_tf,
            "trend_timeframe": trend_tf,
            "decision": final_decision,
            "primary_signal": primary_signal.model_dump() if primary_signal else None,
            "market_regime": regime_info,
            "quote": quote,
            "strategy_evaluations": [s.model_dump() for s in strategy_results],
            "candlestick_patterns": patterns,
            "veto_reasons": veto_reasons,
            "confluence_score": final_confluence_score,
        }

        # Cache result
        self._cache[cache_key] = (now, result)
        return result


confluence_engine = ConfluenceEngine()

