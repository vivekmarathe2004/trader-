"""
Walk-Forward Optimization & Out-of-Sample Validation Engine.
Splits historical series into rolling In-Sample (IS) and Out-of-Sample (OOS) windows.
"""
from typing import Dict, List, Any
import pandas as pd
from app.trading.strategies import QuantitativeStrategy, ALL_QUANT_STRATEGIES
from app.backtesting.engine import backtest_engine
from app.services.mock_provider import mock_provider
from app.features.pipeline import compute_indicator_pipeline


class WalkForwardEngine:
    def run_walk_forward(
        self,
        strategy: QuantitativeStrategy,
        symbol: str = "EURUSD",
        windows_count: int = 4,
        bars_per_window: int = 200,
        is_ratio: float = 0.70,
    ) -> Dict[str, Any]:
        symbol = symbol.upper()
        total_bars = windows_count * bars_per_window
        raw_df = mock_provider.generate_ohlcv(symbol, "15m", total_bars)
        full_df = compute_indicator_pipeline(raw_df)

        window_results = []
        is_trades_total = 0
        oos_trades_total = 0
        oos_returns_list = []

        is_size = int(bars_per_window * is_ratio)
        oos_size = bars_per_window - is_size

        for w in range(windows_count):
            start_idx = w * bars_per_window
            is_df = full_df.iloc[start_idx : start_idx + is_size]
            oos_df = full_df.iloc[start_idx + is_size : start_idx + bars_per_window]

            is_res = backtest_engine.run_backtest(strategy, symbol, df=is_df)
            oos_res = backtest_engine.run_backtest(strategy, symbol, df=oos_df)

            is_ret = is_res["metrics"]["total_return_pct"]
            oos_ret = oos_res["metrics"]["total_return_pct"]
            oos_returns_list.append(oos_ret)

            is_trades_total += is_res["metrics"]["total_trades"]
            oos_trades_total += oos_res["metrics"]["total_trades"]

            # Consistency check: OOS performance vs IS
            efficiency = round((oos_ret / max(0.1, is_ret)) * 100.0, 1) if is_ret > 0 else 0.0

            window_results.append({
                "window_index": w + 1,
                "in_sample_return_pct": is_ret,
                "in_sample_sharpe": is_res["metrics"]["sharpe_ratio"],
                "in_sample_trades": is_res["metrics"]["total_trades"],
                "out_of_sample_return_pct": oos_ret,
                "out_of_sample_sharpe": oos_res["metrics"]["sharpe_ratio"],
                "out_of_sample_trades": oos_res["metrics"]["total_trades"],
                "walk_forward_efficiency_pct": efficiency,
            })

        avg_oos_return = round(float(sum(oos_returns_list) / max(1, len(oos_returns_list))), 2)
        oos_profitable_windows = sum(1 for r in oos_returns_list if r > 0)
        consistency_score = round((oos_profitable_windows / max(1, len(oos_returns_list))) * 100.0, 1)

        return {
            "strategy_id": strategy.strategy_id,
            "strategy_name": strategy.name,
            "symbol": symbol,
            "windows_count": windows_count,
            "window_results": window_results,
            "average_oos_return_pct": avg_oos_return,
            "oos_consistency_pct": consistency_score,
            "total_is_trades": is_trades_total,
            "total_oos_trades": oos_trades_total,
            "walk_forward_grade": "CONSISTENT_OOS" if consistency_score >= 75.0 else "MODERATE_DEGRADATION",
        }


walk_forward_engine = WalkForwardEngine()
